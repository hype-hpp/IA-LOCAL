"""
Fase 02 - 2.1 + 2.2: Cria as collections do Qdrant separadas por escopo (Decision 018).
Fase 05 - 5.1: Adiciona índice de payload para 'memory_type' em global_scope.

Duas collections, não uma única com filtro de payload:
  - chat_scope   -> pontos de ./chats/{chat_id}/, apagados junto com o chat
  - global_scope -> pontos de ./knowledge/, persistentes, promovidos via /save

ATENÇÃO - decisão pendente de validação:
  VECTOR_SIZE está setado para 2560, assumindo Qwen3-Embedding-4B.
  Isso precisa ser confirmado rodando o modelo real e checando a
  dimensão do vetor retornado antes de indexar qualquer dado de verdade.

Mudança de comportamento na Fase 05 (5.1):
  Antes, os índices de payload só eram criados junto com a collection nova
  (bloco pulado inteiro se a collection já existisse). Isso significava que
  rodar este script de novo numa instalação já existente NUNCA adicionava
  um índice novo. Agora a criação de índice é uma etapa separada, sempre
  executada — para poder adicionar índices novos (como 'memory_type' agora)
  numa instalação já em uso, bastando rodar o script de novo.

  Achado real em teste no hardware (5.1): checar existência do índice via
  payload_schema ANTES de criar, em vez de tentar criar e tratar exceção
  de "já existe" — client.create_payload_index() do Qdrant não levanta
  exceção quando o índice já existe (é idempotente no servidor), então um
  try/except nunca detectava esse caso e o log sempre dizia "criado", 
  mesmo quando não tinha nada novo pra criar.
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
VECTOR_SIZE = int(os.environ.get("VECTOR_SIZE", "2560"))  # TODO: confirmar com Qwen3-Embedding-4B real

COLLECTIONS = ["chat_scope", "global_scope"]

# Índices aplicados às duas collections (Decision 018 + 003)
COMMON_INDEXES = ["chat_id", "source", "content_hash"]

# Índices específicos de uma única collection (Fase 05 - 5.1)
SCOPED_INDEXES = {
    "global_scope": ["memory_type"],
}


def ensure_payload_index(client: QdrantClient, collection: str, field_name: str) -> None:
    """
    Cria o índice de payload se ainda não existir.

    Achado real em teste no hardware (5.1): ao contrário do que se assumia,
    client.create_payload_index() NÃO levanta exceção se o índice já existe
    — o Qdrant trata a chamada como idempotente no servidor e sempre
    retorna sucesso. Isso não quebra nada (o índice não duplica), mas um
    try/except baseado em exceção nunca cai no "já existe", e o log mentia
    dizendo "criado" toda vez. Corrigido checando antes o payload_schema
    da collection, para o log refletir o que de fato aconteceu.
    """
    info = client.get_collection(collection)
    existing_fields = set(info.payload_schema.keys()) if info.payload_schema else set()

    if field_name in existing_fields:
        print(f"[skip] Índice '{field_name}' em '{collection}' já existe.")
        return

    client.create_payload_index(
        collection_name=collection,
        field_name=field_name,
        field_schema=PayloadSchemaType.KEYWORD,
    )
    print(f"[ok] Índice '{field_name}' criado em '{collection}'.")


def main():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    print(f"Conectando em {QDRANT_HOST}:{QDRANT_PORT} ...")
    info = client.get_collections()
    print(f"Conexão OK. Collections existentes: {[c.name for c in info.collections]}")

    for name in COLLECTIONS:
        existing = [c.name for c in client.get_collections().collections]
        if name in existing:
            print(f"[skip] Collection '{name}' já existe.")
        else:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            print(f"[ok] Collection '{name}' criada (dim={VECTOR_SIZE}, distance=COSINE).")

        # Índices de payload — sempre garantidos, independente da collection
        # ser nova ou já existir (ver nota de mudança de comportamento acima).
        for field_name in COMMON_INDEXES:
            ensure_payload_index(client, name, field_name)
        for field_name in SCOPED_INDEXES.get(name, []):
            ensure_payload_index(client, name, field_name)

    print("\nEstado final das collections:")
    for name in COLLECTIONS:
        c = client.get_collection(name)
        print(f"  - {name}: pontos={c.points_count}, status={c.status}")


if __name__ == "__main__":
    main()
