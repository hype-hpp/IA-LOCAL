"""
Fase 03 - 3.4: Teste de merge_queries e _dedup_by_url. Lógica pura, sem rede,
sem Ollama, sem SearXNG.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from multi_query import merge_queries, _dedup_by_url


def test_merge_queries():
    # Caso 1: query original sempre primeiro, variações atrás
    result = merge_queries("python tutorial", ["aprender python", "curso python"])
    assert result == ["python tutorial", "aprender python", "curso python"], f"resultado inesperado: {result}"
    print("[ok] Query original primeiro, variações na ordem gerada.")

    # Caso 2: duplicata da original (case-insensitive) é removida
    result = merge_queries("Python Tutorial", ["python tutorial", "curso python"])
    assert result == ["Python Tutorial", "curso python"], f"resultado inesperado: {result}"
    print("[ok] Duplicata case-insensitive da query original é removida.")

    # Caso 3: lista de variações vazia -> só a original
    result = merge_queries("query solo", [])
    assert result == ["query solo"]
    print("[ok] Sem variações, resultado é só a query original.")

    # Caso 4: variações vazias/espaço são ignoradas
    result = merge_queries("query", ["", "  ", "variação válida"])
    assert result == ["query", "variação válida"], f"resultado inesperado: {result}"
    print("[ok] Variações vazias/espaço são ignoradas.")


def test_dedup_by_url():
    # Caso 1: mesma URL em duas listas diferentes -> aparece só uma vez
    results_by_query = [
        [{"url": "https://a.com", "title": "A"}, {"url": "https://b.com", "title": "B"}],
        [{"url": "https://b.com", "title": "B (de novo)"}, {"url": "https://c.com", "title": "C"}],
    ]
    result = _dedup_by_url(results_by_query, max_results=10)
    urls = [r["url"] for r in result]
    assert urls == ["https://a.com", "https://b.com", "https://c.com"], f"resultado inesperado: {urls}"
    print("[ok] URL repetida entre queries aparece só uma vez, mantendo primeira ocorrência.")

    # Caso 2: respeita max_results após dedup
    results_by_query = [[{"url": f"https://site{i}.com"} for i in range(5)]]
    result = _dedup_by_url(results_by_query, max_results=3)
    assert len(result) == 3, f"esperado 3, veio {len(result)}"
    print("[ok] max_results respeitado após dedup.")

    # Caso 3: listas vazias não quebram
    result = _dedup_by_url([], max_results=10)
    assert result == [], "lista vazia deveria retornar lista vazia"
    print("[ok] Lista de queries vazia tratada corretamente.")


if __name__ == "__main__":
    print("1. Testando merge_queries...")
    test_merge_queries()
    print("2. Testando _dedup_by_url...")
    test_dedup_by_url()
    print("\nTodos os testes de multi_query (lógica pura) passaram.")
