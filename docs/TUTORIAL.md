# Tutorial — Fase 06, passo 6.3 (Indexação em crawl_scope)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `indexer.py` | `src/crawler/indexer.py` | Novo — liga `crawl_adaptive()` (6.1) + `chunking.py`/`embedding_client.py` (Fase 02) + `schema.py` (6.2) |
| `test_indexer.py` | `tests/test_indexer.py` | Novo — teste isolado com fakes, sem rede |

Nenhum arquivo existente foi modificado neste passo.

## O que o `indexer.py` faz

`index_crawl_state(state, crawl_id, seed_url, query, client=None)`:

1. Para cada página em `state.knowledge_base` (retorno de `crawl_adaptive()`, 6.1), chunka o markdown com `chunk_text()` (mesma função da Fase 02).
2. Para cada chunk, calcula `content_hash` e pula se já existe em `crawl_scope` (`is_already_crawled`, 6.2 — dedup **global**, não por `crawl_id`).
3. Embeda em lote os chunks novos (`embed_texts()`, Fase 02) e insere em `crawl_scope` com o payload de `build_crawl_payload()` (6.2).
4. Retorna um resumo: `{"pages": N, "chunks_novos": N, "chunks_pulados": N}`.

`state` é aceito por duck typing (só precisa de `.knowledge_base` com itens
`.url`/`.markdown` e `.metrics` com `depth_reached`) — o indexador não
importa o tipo `CrawlState` do `crawl4ai`, pra não acoplar essa peça ao
tipo exato devolvido pelo 6.1.

### Nota honesta sobre o campo `depth`

O `AdaptiveCrawler` **não rastreia profundidade por página individual** —
só uma variável local dentro do laço do `digest()` e o
`metrics["depth_reached"]` final (profundidade máxima alcançada na
execução inteira). Por isso `depth` no payload de cada chunk é o
`depth_reached` da execução inteira (mesmo valor pra todo chunk desse
`crawl_id`), **não** a profundidade exata daquela página específica.
Rastrear por página exigiria forkar o laço interno do `digest()` (mesma
discussão do 6.1) — não fizemos isso sem necessidade comprovada (regra 1
do projeto). Se isso fizer falta de verdade mais pra frente (ex: ranquear
por proximidade da semente), é um ajuste pontual a fazer no 6.1.

## Validação prévia (antes de chegar até você)

Rodei os 3 casos do `test_indexer.py` de verdade (Qdrant fake +
`embed_texts` fake via monkeypatch, mesmo padrão de `test_add_note.py` da
Fase 05):

1. Página nova é chunkada, embedada e inserida com o payload certo (`crawl_id`, `seed_url`, `source`, `depth`).
2. Chunk com `content_hash` já existente não é reinserido **e não gasta chamada de embedding** (dedup antes do embed, mesmo princípio de `add_note.py`).
3. Página com markdown vazio é ignorada, sem erro.

Achei e corrigi um bug no meu próprio teste antes de entregar (não no
código): eu tinha calculado o `content_hash` esperado sobre a string crua
do teste, mas `chunk_text()` normaliza espaçamento ao juntar as palavras
— então o hash tem que ser calculado sobre o chunk já processado, não
sobre o texto de entrada bruto. Corrigido e revalidado.

**Não** testei contra Qdrant/Ollama reais — isso só existe no seu
hardware.

## Como testar

```bash
# 1. Teste isolado (rápido, sem rede)
python tests/test_indexer.py
```

Ainda não tem CLI pra rodar isso de ponta a ponta contra um site real —
isso é o 6.6 (`scripts/crawl.py`), que junta `crawl_adaptive()` (6.1) +
`index_crawl_state()` (6.3) num comando só. Se quiser validar o indexador
contra o Qdrant real antes disso, dá pra rodar manualmente num `python -c`
combinando `crawl_adaptive()` (6.1) com `index_crawl_state()` — me avisa
se preferir que eu monte esse smoke test agora em vez de esperar o 6.6.

### Checklist de validação

- [ ] `test_indexer.py` roda sem erro, os 3 passos aparecem com `[ok]`

## Próximo passo

6.4 — ativar o Smart Cache nativo do Crawl4AI (`CacheMode`) no fetch do
crawler, pra atualização incremental entre execuções. Só começa depois de
você confirmar o checklist acima.
