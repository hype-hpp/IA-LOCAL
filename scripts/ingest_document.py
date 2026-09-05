"""
Fase 02 - 2.4c: Ingestão de documento real no escopo global.
Fase 05 - 5.1: passa a usar src/memory/schema.py para o ID do ponto e o
payload, em vez de montar os dois na mão — mesma lógica de antes, agora
compartilhada com /save (5.2) e nota manual (5.3), que vão gravar em
'global_scope' com o mesmo formato de payload (regra 2 do projeto).

Uso:
    python scripts/ingest_document.py knowledge/documents/algum_arquivo.md

Fluxo:
    1. Lê o arquivo (parser.py)
    2. Divide em chunks (chunking.py)
    3. Para cada chunk, calcula content_hash (sha256) e pula se já existe
       no global_scope (dedup, regra 14 do projeto: evitar indexação repetida)
    4. Gera embeddings em lote (embedding_client.py)
    5. Insere no Qdrant, collection 'global_scope', memory_type='knowledge'

Mudança de payload nesta entrega (5.1):
    - Campo "ingested_at" (Fase 02) foi substituído por "saved_at", para
      documentos, evidências promovidas e notas manuais poderem ser
      listados/filtrados da mesma forma no passo 5.4. "chunk_index"
      continua existindo (específico de documento chunkeado).
    - Novo campo "memory_type": "knowledge" em todo ponto gerado por este
      script, e "tags": [] por padrão (editável depois via o passo 5.4).
"""

import os
import sys
import hashlib
import argparse

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))
from parser import read_text_file
from chunking import chunk_text
from embedding_client import embed_texts

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from schema import memory_point_id, build_memory_payload

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
    points = [
        PointStruct(
            id=memory_point_id(chash),
            vector=vector,
            payload=build_memory_payload(
                text=chunk,
                content_hash=chash,
                memory_type="knowledge",
                source=source_name,
                extra={"chunk_index": i},
            ),
        )
        for i, ((chunk, chash), vector) in enumerate(zip(new_chunks, vectors))
    ]
    client.upsert(collection_name=COLLECTION, points=points)
    print(f"   {len(points)} pontos inseridos em '{COLLECTION}'.")

    total = client.get_collection(COLLECTION).points_count
    print(f"\nTotal de pontos em '{COLLECTION}' agora: {total}")


if __name__ == "__main__":
    main()
