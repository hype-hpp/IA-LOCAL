"""
Fase 03 - 3.3: Pipeline de evidências de pesquisa web.

Junta busca (searxng_client, 3.1) + fetch (page_fetcher, 3.2), reaproveita
chunking.py (Fase 02) para dividir o conteúdo, deduplica por hash (mesmo
padrão do ingest_document.py / Decision 023) e insere no Qdrant.

Escopo: chat_scope por padrão (Decision 018) — evidências de pesquisa web
são tratadas como temporárias, promovíveis a global_scope via /save.
O dedup aqui é escopado por chat_id (não global): o mesmo conteúdo pode
aparecer em dois chats diferentes sem conflito, mas dentro do mesmo chat
não duplica.
"""

import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, List

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from chunking import chunk_text
from embedding_client import embed_texts

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION = "chat_scope"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _already_indexed(client: QdrantClient, chat_id: str, chash: str) -> bool:
    """Verifica se um chunk com esse hash já existe para esse chat_id específico."""
    result, _ = client.scroll(
        collection_name=COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(key="chat_id", match=MatchValue(value=chat_id)),
                FieldCondition(key="content_hash", match=MatchValue(value=chash)),
            ]
        ),
        limit=1,
    )
    return len(result) > 0


def build_evidence_chunks(fetch_results: List[Dict], query: str) -> List[Dict]:
    """
    A partir dos resultados do page_fetcher, gera uma lista de chunks
    prontos para embedding. Páginas que falharam no fetch ou vieram com
    markdown vazio são ignoradas silenciosamente (não é erro, é esperado
    que nem toda URL candidata renda conteúdo útil).

    Cada item: {"text", "source_url", "title", "query"}
    """
    chunks = []
    for page in fetch_results:
        if not page.get("success"):
            continue
        markdown = page.get("markdown") or ""
        if not markdown.strip():
            continue
        for chunk in chunk_text(markdown):
            chunks.append({
                "text": chunk,
                "source_url": page["url"],
                "title": page.get("title"),
                "query": query,
            })
    return chunks


def index_evidence(chat_id: str, chunks: List[Dict]) -> Dict:
    """
    Deduplica (por hash, escopado ao chat_id) e insere os chunks novos no
    chat_scope. Retorna um resumo: {"total", "novos", "pulados"}.
    """
    if not chunks:
        return {"total": 0, "novos": 0, "pulados": 0}

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    new_items = []
    for c in chunks:
        chash = content_hash(c["text"])
        if _already_indexed(client, chat_id, chash):
            continue
        new_items.append((c, chash))

    skipped = len(chunks) - len(new_items)
    if not new_items:
        return {"total": len(chunks), "novos": 0, "pulados": skipped}

    texts = [c["text"] for c, _ in new_items]
    vectors = embed_texts(texts)

    now = datetime.now(timezone.utc).isoformat()
    points = [
        PointStruct(
            # Namespace inclui chat_id: o mesmo texto em chats diferentes
            # gera IDs diferentes (sem colisão entre escopos).
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{chat_id}:{chash}")),
            vector=vector,
            payload={
                "chat_id": chat_id,
                "source": c["source_url"],
                "title": c["title"],
                "query": c["query"],
                "content_hash": chash,
                "text": c["text"],
                "ingested_at": now,
            },
        )
        for (c, chash), vector in zip(new_items, vectors)
    ]
    client.upsert(collection_name=COLLECTION, points=points)

    return {"total": len(chunks), "novos": len(points), "pulados": skipped}
