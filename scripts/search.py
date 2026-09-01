"""
Fase 02 - 2.6: Busca com reranking via GPT-OSS.

Uso:
    python scripts/search.py "sua pergunta aqui"              # com rerank (padrão)
    python scripts/search.py "sua pergunta aqui" --no-rerank  # só hybrid search (RRF puro)
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "retrieval"))
from hybrid_search import hybrid_search
from llm_reranker import rerank


def main():
    parser = argparse.ArgumentParser(description="Busca híbrida (dense + BM25 + rerank) no global_scope")
    parser.add_argument("query", help="Texto da busca")
    parser.add_argument("--top-k", type=int, default=5, help="Quantos resultados finais mostrar")
    parser.add_argument("--candidates", type=int, default=15, help="Quantos candidatos buscar antes do rerank")
    parser.add_argument("--no-rerank", action="store_true", help="Desativa o rerank, mostra ordem crua do RRF")
    args = parser.parse_args()

    print(f"Buscando: '{args.query}'\n")

    candidate_k = args.candidates if not args.no_rerank else args.top_k
    results = hybrid_search(args.query, top_k=candidate_k)

    if not results:
        print("Nenhum resultado. O global_scope está vazio? Rode scripts/ingest_document.py primeiro.")
        return

    if not args.no_rerank:
        print(f"({len(results)} candidatos encontrados, reordenando com GPT-OSS...)\n")
        results = rerank(args.query, results, top_k=args.top_k)
    else:
        results = results[: args.top_k]

    for i, r in enumerate(results, 1):
        preview = (r["text"] or "")[:200].replace("\n", " ")
        print(f"{i}. [score={r['score']}] fonte={r['source']}")
        print(f"   {preview}...\n")


if __name__ == "__main__":
    main()
