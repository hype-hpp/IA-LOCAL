"""
Fase 03 - 3.4: Orquestração de busca multi-query.

Junta query_expansion.py (gera variações via GPT-OSS) + searxng_client.py
(3.1) para buscar a query original + variações, e deduplica os resultados
por URL, mantendo a ordem de primeira aparição (query original tem
prioridade, depois as variações na ordem gerada).

A lógica de merge/dedup é separada em funções puras (merge_queries,
_dedup_by_url) para serem testáveis sem rede — mesmo padrão usado no
llm_reranker.py (parse separado da chamada de rede).
"""

import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(__file__))
from query_expansion import generate_query_variations
from searxng_client import search


def merge_queries(original: str, variations: List[str]) -> List[str]:
    """
    Junta a query original com as variações, removendo duplicatas
    (case-insensitive) e mantendo a original sempre em primeiro.
    """
    seen = {original.strip().lower()}
    merged = [original]
    for v in variations:
        key = v.strip().lower()
        if key and key not in seen:
            seen.add(key)
            merged.append(v)
    return merged


def _dedup_by_url(results_by_query: List[List[Dict]], max_results: int) -> List[Dict]:
    """
    Recebe uma lista de listas de resultados (uma lista por query buscada)
    e devolve uma única lista deduplicada por URL, mantendo a ordem de
    primeira aparição, cortada em max_results.
    """
    seen_urls = set()
    merged = []
    for results in results_by_query:
        for r in results:
            url = r.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(r)
    return merged[:max_results]


def multi_query_search(query: str, max_results: int = 10, num_variations: int = 3) -> Dict:
    """
    Fluxo completo: gera variações da query, busca cada uma no SearXNG,
    deduplica por URL.

    Retorna: {"queries_used": [...], "results": [...]}
    """
    variations = generate_query_variations(query, n=num_variations) if num_variations > 0 else []
    queries = merge_queries(query, variations)

    results_by_query = [search(q, max_results=max_results) for q in queries]
    merged = _dedup_by_url(results_by_query, max_results=max_results)

    return {"queries_used": queries, "results": merged}
