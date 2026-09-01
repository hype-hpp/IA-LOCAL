"""
Fase 03 - 3.1: Cliente de busca via SearXNG local.

SearXNG é um meta-buscador: agrega resultados de vários motores (Google,
Bing, DuckDuckGo etc.) e devolve num formato único. Rodando local, evitamos
depender de API paga de busca (Decision 001 - local-first).

Pré-requisito: SearXNG no ar (docker-compose) e com `json` habilitado em
`formats` no `searxng/settings.yml` (bloqueado por padrão) e um
`secret_key` real (não o valor de exemplo do template).
"""

import os
import requests
from typing import List, Dict, Optional

SEARXNG_URL = os.environ.get("SEARXNG_URL", "http://localhost:8080/search")


def search(query: str, max_results: int = 10, categories: Optional[str] = None) -> List[Dict]:
    """
    Busca no SearXNG local e retorna uma lista de resultados normalizados.

    Cada resultado: {"title": str, "url": str, "snippet": str, "engine": str}

    Args:
        query: texto da busca
        max_results: corta a lista após N resultados (SearXNG pode devolver
            dezenas; cortamos aqui para controlar o que vira "candidato" nos
            próximos passos da Fase 03)
        categories: opcional, filtra por categoria do SearXNG (ex: "general",
            "news"). Deixe None para usar o padrão.
    """
    params = {"q": query, "format": "json"}
    if categories:
        params["categories"] = categories

    try:
        response = requests.get(SEARXNG_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(
            f"Falha ao consultar SearXNG em {SEARXNG_URL}: {e}"
        ) from e

    data = response.json()
    raw_results = data.get("results", [])

    results = []
    for item in raw_results[:max_results]:
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
            "engine": item.get("engine", ""),
        })
    return results


if __name__ == "__main__":
    # smoke test manual
    r = search("teste rápido do client de busca")
    print(f"{len(r)} resultados encontrados.")
    if r:
        print(f"Primeiro: {r[0]['title']} -> {r[0]['url']}")
