"""
Fase 03 - 3.2: Fetch + extração de conteúdo via Crawl4AI.

Decisão (confirmada no planejamento da Fase 03): usar Crawl4AI em vez de
Playwright puro + lib de extração separada (trafilatura/readability).
Crawl4AI já usa Playwright por baixo dos panos e entrega markdown limpo
pronto, resolvendo fetch + extração num passo só.

Este módulo é só a camada de fetch/extração — não faz dedup, não chunka,
não insere no Qdrant. Isso é responsabilidade do próximo passo (3.3).
"""

import asyncio
from typing import Dict, List

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

DEFAULT_TIMEOUT_MS = 30_000


def _extract_markdown(result) -> str:
    """
    result.markdown pode vir como string simples ou como um objeto
    MarkdownGenerationResult (dependendo da config), então tratamos os
    dois casos em vez de assumir um só.
    """
    md = result.markdown
    if md is None:
        return ""
    if isinstance(md, str):
        return md
    return getattr(md, "raw_markdown", "") or ""


def _normalize_result(result) -> Dict:
    """Converte um CrawlResult do Crawl4AI no formato simples que o resto do pipeline usa."""
    if not result.success:
        return {
            "url": result.url,
            "success": False,
            "title": None,
            "markdown": None,
            "error": result.error_message,
        }

    title = None
    if result.metadata:
        title = result.metadata.get("title")

    return {
        "url": result.url,
        "success": True,
        "title": title,
        "markdown": _extract_markdown(result),
        "error": None,
    }


async def _fetch_pages_async(urls: List[str], timeout_ms: int) -> List[Dict]:
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, page_timeout=timeout_ms)
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(urls, config=config)
        return [_normalize_result(r) for r in results]


def fetch_page(url: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> Dict:
    """Busca e extrai o conteúdo (markdown) de uma única URL."""
    return fetch_pages([url], timeout_ms=timeout_ms)[0]


def fetch_pages(urls: List[str], timeout_ms: int = DEFAULT_TIMEOUT_MS) -> List[Dict]:
    """
    Busca e extrai o conteúdo de várias URLs em paralelo (o Crawl4AI já
    gerencia concorrência internamente via arun_many).

    Cada item do retorno: {"url", "success", "title", "markdown", "error"}
    """
    if not urls:
        return []
    return asyncio.run(_fetch_pages_async(urls, timeout_ms))


if __name__ == "__main__":
    # smoke test manual
    r = fetch_page("https://example.com")
    print(f"success={r['success']} title={r['title']!r}")
    if r["success"]:
        print(f"markdown ({len(r['markdown'])} chars): {r['markdown'][:200]}...")
    else:
        print(f"erro: {r['error']}")
