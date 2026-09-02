"""
Fase 03 - 3.3: Teste de integração da indexação de evidências no chat_scope.

Requer Ollama (embedding) + Qdrant no ar. Usa um chat_id de teste isolado
e limpa os dados no início e no fim, para não deixar lixo no chat_scope.
"""

import os
import sys

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from evidence import index_evidence

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
TEST_CHAT_ID = "test_chat_3_3"


def cleanup(client: QdrantClient):
    client.delete(
        collection_name="chat_scope",
        points_selector=Filter(
            must=[FieldCondition(key="chat_id", match=MatchValue(value=TEST_CHAT_ID))]
        ),
    )


def main():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    cleanup(client)  # garante ambiente limpo antes de começar, caso uma run anterior tenha falhado no meio

    chunks = [
        {
            "text": "A Fase 03 do projeto IA Local implementa busca web com SearXNG e Crawl4AI.",
            "source_url": "https://teste.com",
            "title": "Página de teste",
            "query": "IA Local Fase 03",
        },
    ]

    print("1. Indexando evidência nova...")
    summary = index_evidence(TEST_CHAT_ID, chunks)
    assert summary["novos"] == 1, f"esperado 1 novo, veio {summary}"
    print(f"   [ok] {summary}")

    print("2. Reindexando o mesmo chunk (dedup deve pular)...")
    summary = index_evidence(TEST_CHAT_ID, chunks)
    assert summary["novos"] == 0 and summary["pulados"] == 1, f"dedup falhou: {summary}"
    print(f"   [ok] {summary}")

    print("3. Limpando dados de teste...")
    cleanup(client)
    print("   [ok] Limpo.")

    print("\nTodos os testes de indexação de evidências passaram.")


if __name__ == "__main__":
    main()
