"""
Fase 06 - 6.3: Indexação do resultado do crawl adaptativo em crawl_scope.
Fase 06 - 6.5: Limite de armazenamento (retention.py) aplicado a cada indexação.

Liga as peças já prontas, sem duplicar nenhuma lógica:
  - crawl_adaptive() (6.1): roda o AdaptiveCrawler e devolve um CrawlState
    com knowledge_base (páginas já crawleadas) e metrics (confidence,
    depth_reached, etc).
  - chunking.py / embedding_client.py (Fase 02): chunk_text()/embed_texts(),
    mesmas funções já usadas por ingest_document.py.
  - schema.py (6.2): build_crawl_payload()/crawl_point_id()/
    is_already_crawled(), dedup GLOBAL por content_hash dentro de
    crawl_scope.
  - retention.py (6.5): enforce_storage_limit(), chamado ao final de toda
    indexação (mesmo quando não há chunk novo), pra manter o número de
    execuções (crawl_id) em crawl_scope dentro do teto — regra 13 do
    projeto (limitar armazenamento).

Nota honesta sobre o campo 'depth' do payload (6.2): o AdaptiveCrawler não
rastreia profundidade por página individual — só uma variável local do
laço interno do digest() e o metrics['depth_reached'] final (profundidade
máxima alcançada na execução inteira). Por isso 'depth' aqui é o
depth_reached da execução (mesmo valor para todo chunk deste crawl_id),
não a profundidade exata de cada página. Rastrear por página exigiria
forkar o laço interno do digest() (mesma discussão do 6.1) — não fizemos
isso sem necessidade comprovada (regra 1 do projeto). Se fizer falta de
verdade mais pra frente, é um ajuste pontual no 6.1.
"""

import os
import sys
import hashlib
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from chunking import chunk_text
from embedding_client import embed_texts

from schema import build_crawl_payload, crawl_point_id, is_already_crawled, COLLECTION
from retention import enforce_storage_limit, DEFAULT_MAX_CRAWL_IDS

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def index_crawl_state(
    state,
    crawl_id: str,
    seed_url: str,
    query: str,
    client: Optional[QdrantClient] = None,
    max_crawl_ids: int = DEFAULT_MAX_CRAWL_IDS,
) -> dict:
    """
    Indexa o resultado de um crawl_adaptive() (6.1) em crawl_scope: chunka
    cada página de state.knowledge_base, deduplica por content_hash
    (global, schema.py 6.2), embeda em lote e insere. No final, sempre
    aplica o limite de armazenamento (retention.py, 6.5) — mesmo quando
    não há chunk novo, porque uma execução anterior pode ter deixado o
    total acima do teto.

    'state' é qualquer objeto com .knowledge_base (lista de itens com
    .url e .markdown) e .metrics (dict com 'depth_reached') — duck typing
    proposital, não importa CrawlState do crawl4ai aqui, para não acoplar
    o indexador ao tipo exato de retorno do 6.1.

    Retorna um resumo: {"pages": N, "chunks_novos": N, "chunks_pulados": N,
    "retention": {...} (ver enforce_storage_limit)}.
    """
    client = client or QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    depth_reached = int(state.metrics.get("depth_reached", 0))

    new_chunks = []  # (chunk_text, content_hash, source_url, chunk_index)
    skipped = 0

    for result in state.knowledge_base:
        url = getattr(result, "url", None)
        text = getattr(result, "markdown", None) or ""
        if not text.strip():
            continue
        for i, chunk in enumerate(chunk_text(text)):
            chash = content_hash(chunk)
            if is_already_crawled(client, chash):
                skipped += 1
                continue
            new_chunks.append((chunk, chash, url, i))

    if new_chunks:
        texts = [c for c, _, _, _ in new_chunks]
        vectors = embed_texts(texts)

        points = [
            PointStruct(
                id=crawl_point_id(chash),
                vector=vector,
                payload=build_crawl_payload(
                    text=chunk,
                    content_hash=chash,
                    source=url,
                    crawl_id=crawl_id,
                    seed_url=seed_url,
                    query=query,
                    depth=depth_reached,
                    chunk_index=chunk_index,
                ),
            )
            for (chunk, chash, url, chunk_index), vector in zip(new_chunks, vectors)
        ]

        client.upsert(collection_name=COLLECTION, points=points)

    retention_summary = enforce_storage_limit(client, max_crawl_ids=max_crawl_ids)

    return {
        "pages": len(state.knowledge_base),
        "chunks_novos": len(new_chunks),
        "chunks_pulados": skipped,
        "retention": retention_summary,
    }
