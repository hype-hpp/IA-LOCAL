"""
Fase 02 - 2.3c: Teste ponta a ponta do pipeline de embedding + Qdrant.

Fluxo:
  1. Gera embedding de um texto de teste via embedding_client
  2. Insere o ponto na collection 'chat_scope' com um chat_id de teste
  3. Busca de volta usando o mesmo vetor (deve retornar o próprio ponto, score ~1.0)
  4. Remove o ponto de teste (não deixar lixo na collection)
"""

import os
import sys
import uuid
import hashlib

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Permite importar src/ingestion/embedding_client.py independente de onde o script é chamado
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))
from embedding_client import embed_text

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
TEST_CHAT_ID = "test_chat_2_3"
TEST_TEXT = "A Fase 02 do projeto IA Local implementa RAG com Qdrant e embeddings Qwen3."


def main():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    print("1. Gerando embedding de teste...")
    vector = embed_text(TEST_TEXT)
    print(f"   Vetor com {len(vector)} dimensões.")

    point_id = str(uuid.uuid4())
    content_hash = hashlib.sha256(TEST_TEXT.encode()).hexdigest()

    print("2. Inserindo ponto de teste em 'chat_scope'...")
    client.upsert(
        collection_name="chat_scope",
        points=[
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "chat_id": TEST_CHAT_ID,
                    "source": "test_pipeline_2_3",
                    "content_hash": content_hash,
                    "text": TEST_TEXT,
                },
            )
        ],
    )
    print(f"   Ponto inserido: {point_id}")

    print("3. Buscando de volta com o mesmo vetor...")
    results = client.query_points(
        collection_name="chat_scope",
        query=vector,
        limit=1,
    ).points

    if not results:
        print("[FALHA] Nenhum resultado retornado na busca.")
        return

    top = results[0]
    print(f"   Resultado: id={top.id}, score={top.score:.4f}")

    if str(top.id) == point_id and top.score > 0.99:
        print("[ok] Pipeline validado: embed -> insert -> search funcionando.")
    else:
        print("[ATENÇÃO] Resultado inesperado, revisar antes de prosseguir.")

    print("4. Limpando ponto de teste...")
    client.delete(collection_name="chat_scope", points_selector=[point_id])
    print("   Ponto de teste removido.")


if __name__ == "__main__":
    main()
