"""
Fase 06 - 6.1: Teste isolado do wrapper de crawling adaptativo.
Sem rede, sem Ollama, sem Qdrant — só a lógica de composição
(FilterChain + FilteredStatisticalStrategy). Roda rápido e não deveria
quebrar nunca sozinho.
"""

import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "crawler"))
from adaptive import build_filter_chain, FilteredStatisticalStrategy

from crawl4ai.models import Link
from crawl4ai.adaptive_crawler import CrawlState, AdaptiveConfig


def make_link(href: str) -> Link:
    return Link(href=href, text="", title="")


def main():
    # Caso 1: sem nenhum filtro pedido -> None (sem overhead)
    chain = build_filter_chain()
    assert chain is None, "sem filtros pedidos, build_filter_chain deveria retornar None"
    print("[ok] Sem filtros pedidos, build_filter_chain retorna None.")

    # Caso 2: allowed_domains filtra domínio fora da lista
    chain = build_filter_chain(allowed_domains=["docs.crawl4ai.com"])
    assert asyncio.run(chain.apply("https://docs.crawl4ai.com/quickstart")) is True
    assert asyncio.run(chain.apply("https://outrosite.com/pagina")) is False
    print("[ok] allowed_domains aceita domínio permitido e rejeita o resto.")

    # Caso 3: exclude_patterns rejeita URL que bate no padrão
    chain = build_filter_chain(exclude_patterns=["*/login/*"])
    assert asyncio.run(chain.apply("https://site.com/login/form")) is False
    assert asyncio.run(chain.apply("https://site.com/docs/intro")) is True
    print("[ok] exclude_patterns rejeita URL que bate no padrão e aceita o resto.")

    # Caso 4: FilteredStatisticalStrategy remove links bloqueados de
    # state.pending_links antes de ranquear, mantendo os permitidos
    chain = build_filter_chain(blocked_domains=["bloqueado.com"])
    strategy = FilteredStatisticalStrategy(filter_chain=chain)

    state = CrawlState()
    state.query = "documentação de crawling"
    state.pending_links = [
        make_link("https://permitido.com/pagina-1"),
        make_link("https://bloqueado.com/pagina-2"),
        make_link("https://permitido.com/pagina-3"),
    ]

    config = AdaptiveConfig()
    ranked = asyncio.run(strategy.rank_links(state, config))
    ranked_urls = {link.href for link, _score in ranked}

    assert "https://bloqueado.com/pagina-2" not in ranked_urls, (
        "link de domínio bloqueado não deveria ser ranqueado"
    )
    assert ranked_urls == {
        "https://permitido.com/pagina-1",
        "https://permitido.com/pagina-3",
    }, f"conjunto de links ranqueados inesperado: {ranked_urls}"
    assert len(state.pending_links) == 2, "state.pending_links deveria ter sido filtrado in-place"
    print("[ok] FilteredStatisticalStrategy remove links bloqueados antes do ranking.")

    # Caso 5: sem filter_chain (None), rank_links se comporta como o
    # StatisticalStrategy nativo (nenhum link removido)
    strategy_sem_filtro = FilteredStatisticalStrategy(filter_chain=None)
    state2 = CrawlState()
    state2.query = "documentação de crawling"
    state2.pending_links = [make_link("https://qualquer.com/pagina")]
    ranked2 = asyncio.run(strategy_sem_filtro.rank_links(state2, config))
    assert len(ranked2) == 1, "sem filter_chain, nenhum link deveria ser removido"
    print("[ok] Sem filter_chain, nenhum link é removido (comportamento nativo preservado).")

    print("\nTodos os testes do wrapper de crawling adaptativo passaram.")


if __name__ == "__main__":
    main()
