"""
Fase 02 - 2.4c: Ingestão de documento real no escopo global.

Uso:
    python scripts/ingest_document.py knowledge/documents/algum_arquivo.md

Fluxo:
    1. Lê o arquivo (parser.py)
    2. Divide em chunks (chunking.py)
    3. Para cada chunk, calcula content_hash (sha256) e pula se já existe
       no global_scope (dedup, regra 14 do projeto: evitar indexação repetida)
    4. Gera embeddings em lote (embedding_client.py)
    5. Insere no Qdrant, collection 'global_scope', com metadata completa
"""

import os
import sys
import uuid
import hashlib
import argparse
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))
from parser import read_text_file
from chunking import chunk_text
from embedding_client import embed_texts

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION = "global_scope"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def already_indexed(client: QdrantClient, chash: str) -> bool:
    """Verifica se um chunk com esse hash já existe no global_scope."""
    result, _ = client.scroll(
        collection_name=COLLECTION,
        scroll_filter=Filter(
            must=[FieldCondition(key="content_hash", match=MatchValue(value=chash))]
        ),
        limit=1,
    )
    return len(result) > 0


def main():
    parser = argparse.ArgumentParser(description="Ingesta um documento no escopo global")
    parser.add_argument("filepath", help="Caminho do arquivo .md ou .txt a ingerir")
    args = parser.parse_args()

    print(f"1. Lendo {args.filepath} ...")
    text = read_text_file(args.filepath)
    print(f"   {len(text)} caracteres lidos.")

    print("2. Dividindo em chunks...")
    chunks = chunk_text(text)
    print(f"   {len(chunks)} chunks gerados.")

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    source_name = os.path.basename(args.filepath)

    print("3. Checando duplicatas...")
    new_chunks = []
    for chunk in chunks:
        chash = content_hash(chunk)
        if already_indexed(client, chash):
            continue
        new_chunks.append((chunk, chash))

    skipped = len(chunks) - len(new_chunks)
    print(f"   {len(new_chunks)} novos, {skipped} já existiam (pulados).")

    if not new_chunks:
        print("Nada novo para indexar. Fim.")
        return

    print("4. Gerando embeddings em lote...")
    texts = [c for c, _ in new_chunks]
    vectors = embed_texts(texts)
    print(f"   {len(vectors)} vetores gerados.")

    print("5. Inserindo no Qdrant...")
    now = datetime.now(timezone.utc).isoformat()
    points = [
        PointStruct(
            # Qdrant exige id como inteiro ou UUID — geramos um UUID
            # determinístico a partir do hash, então o mesmo conteúdo
            # sempre produz o mesmo id (reforça o dedup).
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, chash)),
            vector=vector,
            payload={
                "source": source_name,
                "content_hash": chash,
                "text": chunk,
                "chunk_index": i,
                "ingested_at": now,
            },
        )
        for i, ((chunk, chash), vector) in enumerate(zip(new_chunks, vectors))
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    print(f"   {len(points)} pontos inseridos em '{COLLECTION}'.")

    total = client.get_collection(COLLECTION).points_count
    print(f"\nTotal de pontos em '{COLLECTION}' agora: {total}")


if __name__ == "__main__":
    main()
