"""
Fase 03 - 3.3: Orquestra o fluxo completo de pesquisa web.

query -> SearXNG (3.1, top N) -> fetch das URLs (3.2, Crawl4AI) ->
chunking + dedup + embed + insert no chat_scope (3.3, evidence.py)

Uso:
    python scripts/web_research.py "sua pergunta aqui" --chat-id meu_chat
    python scripts/web_research.py "sua pergunta aqui" --chat-id meu_chat --max-results 5
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from searxng_client import search
from page_fetcher import fetch_pages
from evidence import build_evidence_chunks, index_evidence

DEFAULT_MAX_RESULTS = 10


def main():
    parser = argparse.ArgumentParser(
        description="Pesquisa web completa: busca -> fetch -> evidências no chat_scope"
    )
    parser.add_argument("query", help="Pergunta/tema a pesquisar")
    parser.add_argument(
        "--chat-id", default="cli_test_chat",
        help="chat_id usado para escopar as evidências (Decision 018). Default: cli_test_chat",
    )
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    args = parser.parse_args()

    print(f"1. Buscando '{args.query}' no SearXNG (top {args.max_results})...")
    search_results = search(args.query, max_results=args.max_results)
    if not search_results:
        print("Nenhum resultado de busca. SearXNG está no ar? Abortando.")
        return
    urls = [r["url"] for r in search_results]
    print(f"   {len(urls)} URLs candidatas encontradas.")

    print("2. Buscando e extraindo conteúdo (Crawl4AI)...")
    fetch_results = fetch_pages(urls)
    ok = sum(1 for r in fetch_results if r["success"])
    print(f"   {ok}/{len(fetch_results)} páginas extraídas com sucesso.")
    for r in fetch_results:
        if not r["success"]:
            print(f"   [falha] {r['url']} -> {r['error']}")

    print("3. Montando chunks de evidência...")
    chunks = build_evidence_chunks(fetch_results, query=args.query)
    print(f"   {len(chunks)} chunks gerados.")

    if not chunks:
        print("Nenhum chunk gerado (nenhuma página rendeu conteúdo útil). Fim.")
        return

    print(f"4. Indexando no chat_scope (chat_id={args.chat_id!r})...")
    summary = index_evidence(args.chat_id, chunks)
    print(f"   total={summary['total']} novos={summary['novos']} pulados={summary['pulados']}")
    print("\nPesquisa concluída.")


if __name__ == "__main__":
    main()
