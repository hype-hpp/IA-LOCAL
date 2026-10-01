# Tutorial — Fase 06, passo 6.5 (Limite de Armazenamento do crawl_scope)

Este tutorial cobre **só** os arquivos entregues neste passo. Setup
geral: `README.md`. Progresso acumulado: `docs/STATUS.md`.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `retention.py` | `src/crawler/retention.py` | Novo — limite de armazenamento (regra 13 do projeto) |
| `indexer.py` | `src/crawler/indexer.py` | **Substitui** o do 6.3 — chama `enforce_storage_limit()` ao final de toda indexação |
| `test_indexer.py` | `tests/test_indexer.py` | **Substitui** — fake ganhou `count()`/`delete()` |
| `test_retention.py` | `tests/test_retention.py` | Novo — teste isolado, sem rede |

## Decisões (suas, desta conversa)

- Quando `crawl_scope` passa do teto: **automático com aviso** — apaga sozinho, mas imprime um log de cada execução removida.
- O teto conta **execuções (`crawl_id`) inteiras**, não chunks soltos — nunca sobra metade de uma execução.

## O que o `retention.py` faz

`enforce_storage_limit(client, max_crawl_ids=DEFAULT_MAX_CRAWL_IDS)`:

1. Varre `crawl_scope` inteiro (só os campos `crawl_id`/`crawled_at` do payload, sem vetor — leve) e acha a data mais antiga de cada `crawl_id`.
2. Se o número de `crawl_id`s distintos passar do teto, apaga as execuções mais antigas **inteiras** (via filtro nativo do Qdrant por `crawl_id`, que já tem índice desde o 6.2), da mais antiga pra mais nova, até caber no teto.
3. Imprime um log por execução removida (`crawl_id`, quantos pontos, desde quando) e um resumo no final.

`DEFAULT_MAX_CRAWL_IDS` vem de `CRAWL_SCOPE_MAX_CRAWL_IDS` (env var), default **50** — ajustável sem mexer no código.

`index_crawl_state()` (6.3) agora chama isso **sempre**, mesmo quando não há chunk novo pra indexar — porque uma execução anterior pode já ter deixado o total acima do teto, e o resumo retornado ganhou a chave `"retention"`.

## Validação prévia (antes de chegar até você)

Rodei os 4 casos do `test_retention.py` de verdade, com Qdrant fake:

1. Dentro do limite → nada é removido.
2. Passou do limite por 1 → remove só a execução mais antiga, inteira; as outras ficam intactas (nem uma removida a mais, nem chunk perdido de execução que devia ficar).
3. Passou do limite por várias → remove todas as antigas necessárias, da mais antiga pra mais nova, até caber.

E os 3 casos do `test_indexer.py` de novo, sem regressão (o fake ganhou `count()`/`delete()` mas o comportamento de indexação continua igual).

**Não** testei contra Qdrant real — isso só existe no seu hardware. Com o
`crawl_scope` ainda em 0 pontos (última vez que você rodou), a retenção
não vai fazer nada visível ainda — só entra em ação depois de várias
execuções reais de crawl.

## Como testar

```bash
python tests/test_retention.py
python tests/test_indexer.py   # confirma que não regrediu
```

Não tem ainda como rodar isso "de ponta a ponta" contra o Qdrant real —
falta o 6.6 (`scripts/crawl.py`), que vai chamar `crawl_adaptive()` (6.1)
+ `index_crawl_state()` (6.3, já com retention embutida) num comando só.

### Checklist de validação

- [ ] `test_retention.py` roda sem erro, os 3 passos aparecem com `[ok]`
- [ ] `test_indexer.py` continua passando (sem regressão)

## Próximo passo

6.6 — `scripts/crawl.py` (CLI) + teste de integração ponta a ponta,
juntando tudo (6.1 a 6.5) num comando só contra o Qdrant/Ollama reais.
Esse é o último passo planejado da Fase 06 antes do fechamento (roadmap,
decisions, estrutura, current_state).
