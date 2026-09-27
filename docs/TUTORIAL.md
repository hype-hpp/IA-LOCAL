# Tutorial — Fase 06, passo 6.2 (Collection `crawl_scope` + Schema de Payload)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `create_collections.py` | `scripts/create_collections.py` | **Substitui** o antigo — adiciona a collection `crawl_scope` |
| `schema.py` | `src/crawler/schema.py` | Novo — payload/ID/dedup do `crawl_scope` |
| `test_crawl_schema.py` | `tests/test_crawl_schema.py` | Novo — teste isolado, sem rede |

## O que mudou em `create_collections.py`

- `COLLECTIONS` ganhou `"crawl_scope"` — terceiro escopo, separado de
  `chat_scope`/`global_scope` (decisão de hp na Fase 06).
- `COMMON_INDEXES`/`SCOPED_INDEXES` viraram um único `COLLECTION_INDEXES`
  por collection. Motivo: `crawl_scope` não tem campo `chat_id` (usa
  `crawl_id`) — aplicar o `COMMON_INDEXES` de sempre também nele criaria
  um índice pra um campo que nunca existe no payload dessa collection.
- **Os índices de `chat_scope`/`global_scope` continuam exatamente os
  mesmos de antes** (`chat_id`/`source`/`content_hash`, e mais
  `memory_type` em `global_scope`) — confirmei isso rodando o módulo e
  inspecionando `COLLECTION_INDEXES` antes de entregar. Não é regressão,
  é só reorganização.

## O que o `schema.py` do crawl_scope faz

Mesma ideia do `src/memory/schema.py` (Fase 05): centraliza payload e ID
do ponto pro pipeline de indexação (6.3) não duplicar lógica.

- `crawl_point_id(content_hash)` — UUID determinístico (`uuid5`), mesma
  convenção desde a Fase 02. Diferença importante: aqui o dedup é
  **global** dentro de `crawl_scope` (não escopado por `crawl_id`, ao
  contrário do `chat_scope` que escopa por `chat_id`) — recrawlear a
  mesma página em execuções diferentes sobrescreve o ponto existente em
  vez de duplicar.
- `build_crawl_payload(...)` — monta o payload: `text`, `content_hash`,
  `source` (URL da página), `crawl_id` (identifica a execução do
  crawler, análogo a `chat_id`), `seed_url`, `query`, `depth`,
  `chunk_index`, `crawled_at`.
- `is_already_crawled(client, content_hash)` — mesmo padrão de
  `is_already_saved()` da Fase 05, aplicado ao `crawl_scope`.

## Validação prévia (antes de chegar até você)

- `test_crawl_schema.py` rodado de verdade com um Qdrant fake em memória
  (mesmo padrão de `test_save_memory.py`, Fase 05) — os 4 casos
  passaram: ID determinístico, payload com os campos certos, dedup
  encontrando hash existente e não encontrando hash novo.
- `create_collections.py` — sintaxe validada e `COLLECTIONS`/
  `COLLECTION_INDEXES` conferidos por import direto. **Não** rodei contra
  um Qdrant real (isso só existe no seu hardware).

## Como testar

```bash
# 1. Teste isolado do schema (rápido, sem rede)
python tests/test_crawl_schema.py

# 2. Criar a collection de verdade (precisa do Qdrant rodando)
python scripts/create_collections.py
```

Saída esperada do passo 2: `crawl_scope` aparece como `[ok] Collection
'crawl_scope' criada (dim=2560, distance=COSINE)`, com os 3 índices
(`crawl_id`, `source`, `content_hash`) criados em seguida. Rodar de novo
deve mostrar tudo como `[skip]` (idempotente).

### Checklist de validação

- [ ] `test_crawl_schema.py` roda sem erro, os 4 passos aparecem com `[ok]`
- [ ] `create_collections.py` roda sem erro contra o Qdrant real e cria `crawl_scope`
- [ ] Rodar `create_collections.py` de novo mostra tudo `[skip]` (nada duplicado)
- [ ] `chat_scope`/`global_scope` continuam com o mesmo `points_count` de antes (confirma que não mexeu no que já existia)

## Próximo passo

6.3 — normalizar o `knowledge_base` retornado por `crawl_adaptive()` (6.1)
pro formato de chunks + dedup (`schema.py`, 6.2) + inserção real em
`crawl_scope`, reaproveitando `chunking.py`/`embedding_client.py`. Só
começa depois de você confirmar o checklist acima.
