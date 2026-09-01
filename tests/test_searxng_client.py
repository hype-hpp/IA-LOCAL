"""
Fase 03 - 3.1: Teste de integração do cliente SearXNG.

Requer SearXNG rodando em http://localhost:8080 com 'json' habilitado em
'formats' no searxng/settings.yml. Assim como test_end_to_end.py (Fase 02)
depende de serviço externo no ar, este também não roda "a seco".
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from searxng_client import search


def main():
    print("1. Buscando 'python programming language'...")
    results = search("python programming language", max_results=5)
    assert isinstance(results, list), "resultado deveria ser uma lista"
    assert len(results) > 0, "esperado ao menos 1 resultado"
    first = results[0]
    assert "title" in first and "url" in first, "resultado sem campos esperados"
    assert first["url"].startswith("http"), "url do resultado parece inválida"
    print(f"   [ok] {len(results)} resultados, primeiro: {first['title']!r}")

    print("2. Checando limite de max_results...")
    results = search("open source software", max_results=3)
    assert len(results) <= 3, f"esperado no máximo 3, veio {len(results)}"
    print(f"   [ok] max_results respeitado ({len(results)} <= 3).")

    print("\nTodos os testes do cliente SearXNG passaram.")


if __name__ == "__main__":
    main()
