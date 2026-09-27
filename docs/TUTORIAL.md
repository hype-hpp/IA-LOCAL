# Tutorial — Fase 06, passo 6.4 (Smart Cache — Atualização Incremental)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `adaptive.py` | `src/crawler/adaptive.py` | **Substitui** o do 6.1 — acrescenta `CachedAdaptiveCrawler` |
| `test_smart_cache.py` | `tests/test_smart_cache.py` | Novo — teste isolado, sem rede |

`src/crawler/schema.py`, `src/crawler/indexer.py` e os testes do 6.2/6.3
não mudaram.

## Achado técnico que motivou este passo

Fui checar como o `AdaptiveCrawler` nativo faz fetch de página, pra ligar
o Smart Cache que vocês decidiram usar (achado do 6.1). Descobri que ele
usa um único método interno, `_crawl_with_preview()`, tanto pra semente
quanto pra cada link seguido — e esse método monta o `CrawlerRunConfig`
**sem especificar `cache_mode`**. O default do `crawl4ai==0.9.2` pra isso
é `CacheMode.BYPASS` (bypassa cache pra leitura E escrita). Ou seja: **sem
essa mudança, o `AdaptiveCrawler` nunca usava o Smart Cache**, mesmo ele
existindo na lib.

## O que o `CachedAdaptiveCrawler` faz

Subclasse de `AdaptiveCrawler` que sobrescreve só `_crawl_with_preview()`
— reproduz os mesmos parâmetros do método original (`link_preview_config`,
`score_links`) e acrescenta `cache_mode=CacheMode.ENABLED`. É um método
"privado" da lib (prefixo `_`), não uma interface pública como
`CrawlStrategy` — risco aceito e documentado no código: se uma versão
futura do `crawl4ai` mudar essa assinatura interna, a sobrescrita para de
valer e volta a cair no bypass padrão (não quebra, só deixa de cachear).

`crawl_adaptive()` ganhou o parâmetro `use_smart_cache: bool = True`
(default ligado). O cache persiste em `~/.crawl4ai/crawl4ai.db` (sqlite,
já é o comportamento nativo da lib) — funciona **entre execuções
separadas** do crawler, não só dentro de uma mesma chamada.

Como isso cobre "atualização incremental": revisitar uma URL não muda
mais o corpo inteiro se o servidor confirmar via ETag/Last-Modified (ou o
hash do `<head>`, fallback nativo) que nada mudou. E mesmo se o conteúdo
vier de novo por algum motivo, o dedup por `content_hash` (6.2/6.3) evita
reindexar/reembeddar à toa. As duas camadas trabalham juntas.

## Validação prévia (antes de chegar até você)

Não dá pra testar isso contra rede real aqui no meu ambiente (minha lista
de domínios permitidos não inclui sites arbitrários tipo
`docs.crawl4ai.com`), então fiz o que dava pra fazer sem rede:

1. **Confirmei no código-fonte real do `crawl4ai==0.9.2`** (baixado do PyPI) que `CrawlerRunConfig` tem `cache_mode: CacheMode = CacheMode.BYPASS` como default, e que `_crawl_with_preview()` não passa `cache_mode` — confirmando o problema antes de "consertar".
2. **`test_smart_cache.py`**: substitui o `AsyncWebCrawler` por um fake que só grava o `CrawlerRunConfig` recebido (sem rede nenhuma) — confirma que `CachedAdaptiveCrawler._crawl_with_preview()` de fato usa `cache_mode=CacheMode.ENABLED`, e que `score_links`/`link_preview_config` continuam iguais ao original (a sobrescrita não perdeu nada).
3. **`test_adaptive_crawler.py` (6.1) rodado de novo** — sem regressão, os 5 casos continuam passando.

**O que só dá pra confirmar no seu hardware**: que o cache de verdade
evita reservar corpo de página não mudada numa segunda execução — isso
exige rede real e rodar `crawl_adaptive()` duas vezes seguidas contra o
mesmo `start_url`.

## Como testar

```bash
# 1. Testes isolados (rápido, sem rede)
python tests/test_smart_cache.py
python tests/test_adaptive_crawler.py   # confirma que não regrediu

# 2. Smoke test manual real (rede + Chromium) — rodar duas vezes seguidas
python src/crawler/adaptive.py
python src/crawler/adaptive.py
```

Não tem um jeito fácil de "ver" o cache funcionando só pela saída do
smoke test atual (ele não imprime hit/miss). Se quiser confirmar de
verdade que a segunda rodada usou cache, dá pra inspecionar
`~/.crawl4ai/crawl4ai.db` diretamente, ou eu adiciono um print de
diagnóstico no smoke test — me avisa se quiser isso antes do 6.5.

### Checklist de validação

- [ ] `test_smart_cache.py` roda sem erro, os 2 passos aparecem com `[ok]`
- [ ] `test_adaptive_crawler.py` continua passando sem erro (sem regressão)
- [ ] (opcional) rodar `python src/crawler/adaptive.py` duas vezes e confirmar que `~/.crawl4ai/crawl4ai.db` foi criado/atualizado

## Próximo passo

6.5 — limite de armazenamento do crawler (cap de nº de chunks/páginas em
`crawl_scope` — isso é nosso, não vem da lib). Só começa depois de você
confirmar o checklist acima.
