"""
Fase 06 - 6.1: Wrapper de crawling adaptativo.
Fase 06 - 6.4: Smart Cache nativo do Crawl4AI (atualização incremental).

O crawl4ai (já pinado em requirements.txt) traz módulos nativos que não
são conectados entre si:
  - AdaptiveCrawler (crawl4ai.adaptive_crawler): decide profundidade e
    quando parar via confiança/saturação estatística (sem GPU/embedding).
    max_pages/max_depth funcionam como teto de segurança.
  - FilterChain (crawl4ai.deep_crawling.filters): exclusões e domínios
    permitidos (DomainFilter, URLPatternFilter).
  - Smart Cache (crawl4ai.cache_context / async_database): revalidação
    por ETag/Last-Modified com fallback por hash do <head>, persistida em
    ~/.crawl4ai/crawl4ai.db (sqlite, entre execuções separadas).

Ponto de integração 1 (6.1): o AdaptiveCrawler aceita uma `strategy`
customizada (interface CrawlStrategy). Em vez de forkar o laço interno do
`digest()` (que quebraria em upgrades da lib), FilteredStatisticalStrategy
sobrescreve só `rank_links()`: remove de state.pending_links os links que
não passam no FilterChain, e delega o resto (scoring, confiança, parada)
pro StatisticalStrategy original do crawl4ai.

Ponto de integração 2 (6.4): o AdaptiveCrawler usa internamente um único
método, `_crawl_with_preview()`, para TODO fetch (a semente e cada link
seguido) — mas monta o CrawlerRunConfig sem especificar cache_mode, e o
default do crawl4ai==0.9.2 pra CrawlerRunConfig é CacheMode.BYPASS. Ou
seja, sem essa sobrescrita, o AdaptiveCrawler NUNCA usa o Smart Cache (nem
lê, nem escreve). CachedAdaptiveCrawler sobrescreve só esse método,
reproduzindo os mesmos parâmetros e só acrescentando
cache_mode=CacheMode.ENABLED. É um método "privado" (prefixo _, não faz
parte de nenhuma interface pública tipo CrawlStrategy) — risco aceito e
documentado: se uma versão futura do crawl4ai mudar essa assinatura
interna, a sobrescrita para de valer e volta a cair no bypass padrão da
lib (não quebra, só deixa de cachear).

Nenhuma lógica de profundidade, orçamento, parada ou cache é
reimplementada aqui — só composição.
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
    CacheMode,
)
from crawl4ai.async_configs import CrawlerRunConfig, LinkPreviewConfig


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


class CachedAdaptiveCrawler(AdaptiveCrawler):
    """
    AdaptiveCrawler nativo, com o Smart Cache do Crawl4AI ativado.

    Sobrescreve só _crawl_with_preview() (o único ponto de fetch usado
    internamente pelo digest(), tanto pra semente quanto pra cada link
    seguido) pra acrescentar cache_mode=CacheMode.ENABLED — sem essa
    sobrescrita, o AdaptiveCrawler usa o default da lib (BYPASS) e nunca
    cacheia nada. O resto do método é uma cópia fiel do original (mesmos
    parâmetros de link_preview_config e score_links), só com esse único
    campo a mais.
    """

    async def _crawl_with_preview(self, url: str, query: str):
        config = CrawlerRunConfig(
            link_preview_config=LinkPreviewConfig(
                include_internal=True,
                include_external=False,
                query=query,
                concurrency=5,
                timeout=self.config.link_preview_timeout,
                max_links=50,
                verbose=False,
            ),
            score_links=True,
            cache_mode=CacheMode.ENABLED,
        )
        try:
            result = await self.crawler.arun(url=url, config=config)
            if hasattr(result, "_results") and result._results:
                result = result._results[0]
            if hasattr(result, "links") and result.links:
                result.links["internal"] = [
                    link for link in result.links["internal"] if link.get("head_data")
                ]
            return result
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            return None


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
    use_smart_cache: bool,
) -> CrawlState:
    config = AdaptiveConfig(
        max_pages=max_pages,
        max_depth=max_depth,
        confidence_threshold=confidence_threshold,
    )
    strategy = FilteredStatisticalStrategy(filter_chain=filter_chain)
    crawler_cls = CachedAdaptiveCrawler if use_smart_cache else AdaptiveCrawler

    async with AsyncWebCrawler() as crawler:
        adaptive = crawler_cls(crawler=crawler, config=config, strategy=strategy)
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
    use_smart_cache: bool = True,
) -> CrawlState:
    """
    Roda o crawler adaptativo (estratégia estatística) a partir de
    start_url, guiado por query. Para sozinho quando a confiança/
    saturação atinge o threshold, ou quando bate o teto de segurança
    (max_pages/max_depth). Exclusões e domínios permitidos são aplicados
    via FilterChain nativo em cada rodada de ranking de links.

    use_smart_cache=True (default) ativa o Smart Cache nativo do Crawl4AI
    (ETag/Last-Modified + fallback por hash do <head>), persistido em
    ~/.crawl4ai/crawl4ai.db entre execuções separadas — páginas não
    mudadas desde a última visita são revalidadas sem re-baixar o corpo
    inteiro. Combinado com o dedup por content_hash do crawl_scope (6.2/
    6.3), cobre a "atualização incremental" do roadmap desta fase.

    Retorna o CrawlState final:
      - state.knowledge_base: lista de CrawlResult já crawleados
      - state.crawled_urls: set de URLs visitadas
      - state.metrics: confidence, coverage, consistency, saturation,
        pages_crawled, depth_reached
    """
    filter_chain = build_filter_chain(allowed_domains, blocked_domains, exclude_patterns)
    return asyncio.run(
        _crawl_adaptive_async(
            start_url, query, max_pages, max_depth, confidence_threshold,
            filter_chain, use_smart_cache,
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
