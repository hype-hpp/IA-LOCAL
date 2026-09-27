"""
Fase 06 - 6.1: Wrapper de crawling adaptativo.

O crawl4ai (já pinado em requirements.txt) traz dois módulos nativos que
não são conectados entre si:
  - AdaptiveCrawler (crawl4ai.adaptive_crawler): decide profundidade e
    quando parar via confiança/saturação estatística (sem GPU/embedding).
    max_pages/max_depth funcionam como teto de segurança.
  - FilterChain (crawl4ai.deep_crawling.filters): exclusões e domínios
    permitidos (DomainFilter, URLPatternFilter).

Ponto de integração: o AdaptiveCrawler aceita uma `strategy` customizada
(interface CrawlStrategy). Em vez de forkar o laço interno do `digest()`
(que quebraria em upgrades da lib), FilteredStatisticalStrategy sobrescreve
só `rank_links()`: remove de state.pending_links os links que não passam
no FilterChain, e delega o resto (scoring, confiança, parada) pro
StatisticalStrategy original do crawl4ai. Nenhuma lógica de profundidade,
orçamento ou parada é reimplementada aqui — só composição.
"""

import asyncio
from typing import List, Optional

from crawl4ai import (
    AsyncWebCrawler,
    AdaptiveCrawler,
    AdaptiveConfig,
    CrawlState,
    StatisticalStrategy,
    FilterChain,
    DomainFilter,
    URLPatternFilter,
)


class FilteredStatisticalStrategy(StatisticalStrategy):
    """StatisticalStrategy nativa, com exclusões/domínios aplicados a
    state.pending_links antes de cada rodada de ranking."""

    def __init__(self, filter_chain: Optional[FilterChain] = None):
        super().__init__()
        self.filter_chain = filter_chain

    async def rank_links(self, state: CrawlState, config: AdaptiveConfig):
        if self.filter_chain is not None:
            state.pending_links = await self._filter_links(state.pending_links)
        return await super().rank_links(state, config)

    async def _filter_links(self, links: List) -> List:
        kept = []
        for link in links:
            if await self.filter_chain.apply(link.href):
                kept.append(link)
        return kept


def build_filter_chain(
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> Optional[FilterChain]:
    """
    Monta um FilterChain nativo do crawl4ai a partir de listas de config
    simples. Retorna None se nada foi pedido (sem overhead nesse caso).

    exclude_patterns: padrões glob (ex: "*/login/*") que devem ser
    EXCLUÍDOS — aplicado com reverse=True (URLPatternFilter por padrão
    inclui o que casa com o padrão; reverse inverte para exclusão).
    """
    filters = []
    if allowed_domains or blocked_domains:
        filters.append(
            DomainFilter(allowed_domains=allowed_domains, blocked_domains=blocked_domains)
        )
    if exclude_patterns:
        filters.append(URLPatternFilter(patterns=exclude_patterns, reverse=True))
    if not filters:
        return None
    return FilterChain(filters)


async def _crawl_adaptive_async(
    start_url: str,
    query: str,
    max_pages: int,
    max_depth: int,
    confidence_threshold: float,
    filter_chain: Optional[FilterChain],
) -> CrawlState:
    config = AdaptiveConfig(
        max_pages=max_pages,
        max_depth=max_depth,
        confidence_threshold=confidence_threshold,
    )
    strategy = FilteredStatisticalStrategy(filter_chain=filter_chain)

    async with AsyncWebCrawler() as crawler:
        adaptive = AdaptiveCrawler(crawler=crawler, config=config, strategy=strategy)
        state = await adaptive.digest(start_url=start_url, query=query)
    return state


def crawl_adaptive(
    start_url: str,
    query: str,
    max_pages: int = 20,
    max_depth: int = 5,
    confidence_threshold: float = 0.7,
    allowed_domains: Optional[List[str]] = None,
    blocked_domains: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
) -> CrawlState:
    """
    Roda o crawler adaptativo (estratégia estatística) a partir de
    start_url, guiado por query. Para sozinho quando a confiança/
    saturação atinge o threshold, ou quando bate o teto de segurança
    (max_pages/max_depth). Exclusões e domínios permitidos são aplicados
    via FilterChain nativo em cada rodada de ranking de links.

    Retorna o CrawlState final:
      - state.knowledge_base: lista de CrawlResult já crawleados
      - state.crawled_urls: set de URLs visitadas
      - state.metrics: confidence, coverage, consistency, saturation,
        pages_crawled, depth_reached
    """
    filter_chain = build_filter_chain(allowed_domains, blocked_domains, exclude_patterns)
    return asyncio.run(
        _crawl_adaptive_async(
            start_url, query, max_pages, max_depth, confidence_threshold, filter_chain
        )
    )


if __name__ == "__main__":
    # smoke test manual (precisa de rede + Chromium do Crawl4AI)
    state = crawl_adaptive(
        start_url="https://docs.crawl4ai.com/",
        query="deep crawling strategies",
        max_pages=5,
        max_depth=2,
    )
    print(f"Páginas crawleadas: {len(state.crawled_urls)}")
    print(f"Confiança final: {state.metrics.get('confidence'):.3f}")
    for url in state.crawl_order:
        print(f"  - {url}")
