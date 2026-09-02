"""
Fase 03 - 3.2: CLI para testar o fetch + extração de páginas isoladamente.

Uso:
    python scripts/fetch_page.py https://example.com
    python scripts/fetch_page.py https://example.com https://outra-url.com
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from page_fetcher import fetch_pages


def main():
    parser = argparse.ArgumentParser(description="Testa fetch + extração via Crawl4AI")
    parser.add_argument("urls", nargs="+", help="Uma ou mais URLs para buscar")
    args = parser.parse_args()

    print(f"Buscando {len(args.urls)} URL(s)...\n")
    results = fetch_pages(args.urls)

    for r in results:
        print(f"URL: {r['url']}")
        if r["success"]:
            preview = (r["markdown"] or "")[:300].replace("\n", " ")
            print(f"  título: {r['title']}")
            print(f"  markdown: {len(r['markdown'])} caracteres")
            print(f"  prévia: {preview}...")
        else:
            print(f"  [FALHA] {r['error']}")
        print()


if __name__ == "__main__":
    main()
