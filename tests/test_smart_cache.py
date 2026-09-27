"""
Fase 06 - 6.4: Teste do CachedAdaptiveCrawler — confirma que
_crawl_with_preview() passa cache_mode=CacheMode.ENABLED pro
CrawlerRunConfig usado em cada fetch. Sem rede real: substitui o
AsyncWebCrawler por um fake que só grava o CrawlerRunConfig recebido.
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "crawler"))
from adaptive import CachedAdaptiveCrawler, FilteredStatisticalStrategy

from crawl4ai import AdaptiveConfig, CacheMode


class FakeCrawlResult:
    def __init__(self, url):
        self.url = url
        self.success = True
        self.markdown = "conteúdo fake"
        self.links = {"internal": [], "external": []}


class FakeAsyncCrawler:
    """Substitui o AsyncWebCrawler real: só grava o CrawlerRunConfig
    recebido em cada chamada de arun(), sem rede nenhuma."""

    def __init__(self):
        self.received_configs = []

    async def arun(self, url, config):
        self.received_configs.append(config)
        return FakeCrawlResult(url)


def main():
    # Caso 1: cache_mode=ENABLED é passado no fetch
    fake_crawler = FakeAsyncCrawler()
    config = AdaptiveConfig(max_pages=1, max_depth=1)
    strategy = FilteredStatisticalStrategy()
    adaptive = CachedAdaptiveCrawler(crawler=fake_crawler, config=config, strategy=strategy)

    result = asyncio.run(adaptive._crawl_with_preview("https://exemplo.com/", "query de teste"))

    assert len(fake_crawler.received_configs) == 1
    used_config = fake_crawler.received_configs[0]
    assert used_config.cache_mode == CacheMode.ENABLED, (
        f"esperado CacheMode.ENABLED, veio {used_config.cache_mode}"
    )
    assert result.url == "https://exemplo.com/"
    print("[ok] CachedAdaptiveCrawler usa cache_mode=CacheMode.ENABLED no fetch.")

    # Caso 2: score_links e link_preview_config continuam presentes
    # (a sobrescrita não perdeu nada do comportamento original)
    assert used_config.score_links is True
    assert used_config.link_preview_config is not None
    assert used_config.link_preview_config.query == "query de teste"
    print("[ok] score_links e link_preview_config continuam iguais ao original.")

    print("\nTodos os testes do Smart Cache (6.4) passaram.")


if __name__ == "__main__":
    main()
