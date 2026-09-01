"""
Fase 03 - 3.1: CLI para testar a busca via SearXNG isoladamente.

Uso:
    python scripts/search_web.py "sua query aqui"
    python scripts/search_web.py "sua query aqui" --max-results 5
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from searxng_client import search


def main():
    parser = argparse.ArgumentParser(description="Testa busca via SearXNG")
    parser.add_argument("query", help="Texto da busca")
    parser.add_argument("--max-results", type=int, default=10)
    args = parser.parse_args()

    print(f"Buscando: {args.query!r}\n")
    results = search(args.query, max_results=args.max_results)

    if not results:
        print("Nenhum resultado encontrado. Verifique se o SearXNG está no ar "
              "(docker compose ps) e se 'json' está habilitado em 'formats' "
              "no searxng/settings.yml.")
        return

    for i, r in enumerate(results, 1):
        preview = (r["snippet"] or "")[:150]
        print(f"[{i}] {r['title']}")
        print(f"    {r['url']}")
        print(f"    engine: {r['engine']}")
        print(f"    {preview}...")
        print()


if __name__ == "__main__":
    main()
