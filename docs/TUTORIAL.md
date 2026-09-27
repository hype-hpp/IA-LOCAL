dx# Tutorial — Fase 06, passo 6.1 (Wrapper de Crawling Adaptativo)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `__init__.py` | `src/crawler/__init__.py` | Novo — pasta `src/crawler/` criada nesta fase |
| `adaptive.py` | `src/crawler/adaptive.py` | Novo — wrapper de crawling adaptativo |
| `test_adaptive_crawler.py` | `tests/test_adaptive_crawler.py` | Novo — teste isolado, sem rede |

Nenhum arquivo existente foi modificado neste passo.

## O que o `adaptive.py` faz

O `crawl4ai` (já pinado em `requirements.txt` desde a Fase 03) traz dois
módulos nativos que **não são conectados entre si**:

- `AdaptiveCrawler` — decide profundidade e quando parar via
  confiança/saturação estatística (estratégia `"statistical"`, sem
  GPU/embedding). `max_pages`/`max_depth` funcionam como teto de
  segurança, não como critério principal de parada.
- `FilterChain` (`DomainFilter`, `URLPatternFilter`) — exclusões e
  domínios permitidos.

`FilteredStatisticalStrategy` é uma subclasse fina do `StatisticalStrategy`
nativo que só sobrescreve `rank_links()`: remove de `state.pending_links`
o que não passa no `FilterChain` antes de delegar o resto (scoring,
confiança, parada) pro `StatisticalStrategy` original. Esse é o único
ponto de extensão público que o `AdaptiveCrawler` oferece (injeção de
`strategy`) — evita forkar o laço interno do `digest()`, que quebraria em
upgrades futuros da lib.

Funções expostas:

- `build_filter_chain(allowed_domains, blocked_domains, exclude_patterns)` — monta o `FilterChain` nativo; retorna `None` se nada foi pedido.
- `crawl_adaptive(start_url, query, max_pages, max_depth, confidence_threshold, ...)` — entrypoint síncrono (mesmo padrão de `asyncio.run` usado em `page_fetcher.py`).

## Validação prévia (antes de chegar até você)

Instalei o `crawl4ai==0.9.2` de verdade num ambiente isolado aqui e rodei
os 5 casos do `test_adaptive_crawler.py` — todos passaram:

1. Sem filtros pedidos, `build_filter_chain` retorna `None`.
2. `allowed_domains` aceita o domínio permitido e rejeita o resto.
3. `exclude_patterns` rejeita URL que bate no padrão (`*/login/*`) e aceita o resto.
4. `FilteredStatisticalStrategy` remove links de domínio bloqueado de `state.pending_links` **antes** do ranking, mantendo os permitidos.
5. Sem `filter_chain` (`None`), nenhum link é removido — comportamento nativo preservado.

Isso valida a lógica de filtro/composição. **Não** valida o crawl real via
rede (`crawl_adaptive()` com `AsyncWebCrawler`/Chromium) — isso só dá pra
confirmar no seu hardware.

## Como testar

```bash
# 1. Teste isolado (rápido, sem rede) — deve reproduzir os 5 [ok] daqui
python tests/test_adaptive_crawler.py

# 2. Smoke test manual real — PRECISA de rede + Chromium do Crawl4AI
python src/crawler/adaptive.py
```

Saída esperada do passo 2: nº de páginas crawleadas, confiança final
(`state.metrics["confidence"]`) e a lista de URLs visitadas, crawleando
`docs.crawl4ai.com` a partir de uma query de teste.

### Checklist de validação

- [ ] `test_adaptive_crawler.py` roda sem erro, os 5 passos aparecem com `[ok]`
- [ ] `python src/crawler/adaptive.py` roda de verdade contra a rede e imprime páginas + confiança
- [ ] Confirmar que o crawler realmente para antes de `max_pages` quando a confiança satura (ou reportar se sempre bate o teto — isso vira um ajuste de `confidence_threshold`)

## Próximo passo

6.2 — criar a collection `crawl_scope` no Qdrant (`create_collections.py`) +
payload schema, reaproveitando `content_hash`/`source` de `evidence.py`. Só
começa depois de você confirmar o checklist acima.
