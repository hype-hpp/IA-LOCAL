"""
Fase 03 - 3.5: Teste de integração end-to-end do pipeline completo de
pesquisa web (fechamento da fase).

Requer SearXNG, Ollama (embedding + GPT-OSS) e Qdrant todos no ar. Cobre o
mesmo fluxo usado por scripts/web_research.py, mas chamando as funções
diretamente (sem subprocess) para validar cada etapa isoladamente.

Usa um chat_id de teste isolado e limpa antes/depois, para não deixar lixo
no chat_scope real.
"""

import os
import sys

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from multi_query import multi_query_search
from page_fetcher import fetch_pages
from evidence import build_evidence_chunks, index_evidence

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
TEST_CHAT_ID = "test_chat_3_5_e2e"


def cleanup(client: QdrantClient):
    client.delete(
        collection_name="chat_scope",
        points_selector=Filter(
            must=[FieldCondition(key="chat_id", match=MatchValue(value=TEST_CHAT_ID))]
        ),
    )


def main():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    cleanup(client)  # garante ambiente limpo, caso uma run anterior tenha falhado no meio

    query = "o que é retrieval augmented generation"

    print("1. Multi-query + busca no SearXNG...")
    search_data = multi_query_search(query, max_results=5, num_variations=2)
    assert len(search_data["queries_used"]) >= 1, "esperado ao menos a query original"
    assert len(search_data["results"]) > 0, "esperado ao menos 1 resultado de busca"
    print(f"   [ok] {len(search_data['queries_used'])} queries usadas, "
          f"{len(search_data['results'])} URLs únicas.")

    urls = [r["url"] for r in search_data["results"]]

    print("2. Fetch + extração via Crawl4AI...")
    fetch_results = fetch_pages(urls)
    ok = sum(1 for r in fetch_results if r["success"])
    assert ok > 0, "esperado ao menos 1 página extraída com sucesso (todas falharam?)"
    print(f"   [ok] {ok}/{len(fetch_results)} páginas extraídas.")

    print("3. Montando chunks de evidência...")
    chunks = build_evidence_chunks(fetch_results, query=query)
    assert len(chunks) > 0, "esperado ao menos 1 chunk"
    print(f"   [ok] {len(chunks)} chunks gerados.")

    print("4. Indexando no chat_scope...")
    summary = index_evidence(TEST_CHAT_ID, chunks)
    assert summary["novos"] > 0, "esperado ao menos 1 chunk novo indexado"
    print(f"   [ok] {summary}")

    print("5. Reindexando os mesmos chunks (dedup deve pular tudo)...")
    summary2 = index_evidence(TEST_CHAT_ID, chunks)
    assert summary2["novos"] == 0, f"dedup falhou na segunda rodada: {summary2}"
    print(f"   [ok] {summary2}")

    print("6. Limpando dados de teste...")
    cleanup(client)
    print("   [ok] Limpo.")

    print("\nPipeline completo da Fase 03 validado de ponta a ponta.")


if __name__ == "__main__":
    main()
