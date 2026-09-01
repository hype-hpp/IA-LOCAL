"""
Fase 02 - 2.1 + 2.2: Cria as collections do Qdrant separadas por escopo (Decision 018).

Duas collections, não uma única com filtro de payload:
  - chat_scope   -> pontos de ./chats/{chat_id}/, apagados junto com o chat
  - global_scope -> pontos de ./knowledge/, persistentes, promovidos via /save

ATENÇÃO - decisão pendente de validação:
  VECTOR_SIZE está setado para 2560, assumindo Qwen3-Embedding-4B.
  Isso precisa ser confirmado rodando o modelo real e checando a
  dimensão do vetor retornado antes de indexar qualquer dado de verdade.
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
VECTOR_SIZE = int(os.environ.get("VECTOR_SIZE", "2560"))  # TODO: confirmar com Qwen3-Embedding-4B real

COLLECTIONS = ["chat_scope", "global_scope"]


def main():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    print(f"Conectando em {QDRANT_HOST}:{QDRANT_PORT} ...")
    info = client.get_collections()
    print(f"Conexão OK. Collections existentes: {[c.name for c in info.collections]}")

    for name in COLLECTIONS:
        existing = [c.name for c in client.get_collections().collections]
        if name in existing:
            print(f"[skip] Collection '{name}' já existe.")
            continue

        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        print(f"[ok] Collection '{name}' criada (dim={VECTOR_SIZE}, distance=COSINE).")

        # Índices de metadata mínimos para filtragem (Decision 018 + 003)
        client.create_payload_index(
            collection_name=name,
            field_name="chat_id",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        client.create_payload_index(
            collection_name=name,
            field_name="source",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        client.create_payload_index(
            collection_name=name,
            field_name="content_hash",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print(f"[ok] Índices de payload criados em '{name}' (chat_id, source, content_hash).")

    print("\nEstado final das collections:")
    for name in COLLECTIONS:
        c = client.get_collection(name)
        print(f"  - {name}: pontos={c.points_count}, status={c.status}")


if __name__ == "__main__":
    main()
