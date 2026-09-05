# Tutorial — Fase 05, passo 5.1 (Fundação de Memória)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## O que foi decidido neste passo (confirmado com hp antes de codar)

1. **Metadata de memória fica só no payload do Qdrant** — sem componente
   novo (nada de PostgreSQL por enquanto).
2. **Interface continua sendo CLI** — nada de UI Gradio/Streamlit ainda
   nesta fase.
3. **"Memória de conversa" fica fora do escopo da Fase 05** — não existe
   Agent Core/loop de chat real ainda (só chega na Fase 07). Esta fase foca
   em `/save` + memória semântica + memória de pesquisa.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `src/memory/__init__.py` | `src/memory/__init__.py` | Novo pacote `src/memory/` |
| `src/memory/schema.py` | `src/memory/schema.py` | Novo — schema de metadata de memória (3 tipos: `knowledge`, `research`, `manual`) |
| `scripts/create_collections.py` | `scripts/create_collections.py` | **Substitui o antigo** — adiciona índice `memory_type` em `global_scope` |
| `scripts/ingest_document.py` | `scripts/ingest_document.py` | **Substitui o antigo** — passa a usar `src/memory/schema.py` |
| `tests/test_memory_schema.py` | `tests/test_memory_schema.py` | Novo teste, sem rede |

Apague os arquivos antigos antes de copiar os novos por cima (regra do
`README.md` — evita arquivo "fantasma" desatualizado).

## O que muda no comportamento existente

- **`create_collections.py`**: antes, os índices de payload só eram
  criados junto com uma collection nova (se a collection já existisse, o
  bloco inteiro era pulado). Agora a criação de índice é uma etapa
  separada, sempre executada e tolerante a "índice já existe" — assim dá
  pra rodar o script de novo numa instalação já em uso e ganhar o índice
  novo (`memory_type`) sem recriar nada.
- **`ingest_document.py`**: o campo de payload `ingested_at` foi
  substituído por `saved_at` (nome comum aos três tipos de memória, para
  o passo 5.4 poder listar/filtrar todos do mesmo jeito). `chunk_index`
  continua igual. Novos campos: `memory_type: "knowledge"` e `tags: []`
  em todo ponto gerado por este script.
- Como ainda não há documento real indexado em `global_scope` neste
  projeto, não existe dado antigo para migrar. Se isso mudar antes deste
  passo ser rodado, avise antes de reingerir.

## Como testar

```bash
# 1. Teste isolado do schema (rápido, sem rede, sem Qdrant)
python tests/test_memory_schema.py

# 2. Rodar create_collections.py de novo — mesmo com as collections já
#    existentes, deve criar o índice novo 'memory_type' em global_scope
python scripts/create_collections.py

# 3. Reingerir um documento de teste — confirma que memory_type/tags/saved_at
#    aparecem no payload (ver no dashboard do Qdrant, http://localhost:6333/dashboard)
python scripts/ingest_document.py knowledge/documents/algum_arquivo.md
```

### Checklist de validação

- [ ] `test_memory_schema.py` passa todos os asserts
- [ ] `create_collections.py` roda sem erro numa instalação já existente e
      mostra `[ok] Índice 'memory_type' criado em 'global_scope'.`
- [ ] Rodar `create_collections.py` uma segunda vez mostra
      `[skip] Índice 'memory_type' em 'global_scope' já existe (...)` — confirma idempotência
- [ ] Um novo ponto ingerido via `ingest_document.py` tem no payload:
      `memory_type: "knowledge"`, `tags: []`, `saved_at` (não mais `ingested_at`)
- [ ] `chunk_index` continua presente no payload, sem mudança

## Próximo passo (5.2)

Mecanismo `/save`: promoção de pontos do `chat_scope` → `global_scope`
(por `chat_id`), usando `memory_point_id()` e `build_memory_payload()`
deste passo com `memory_type="research"`, reaproveitando o dedup por
`content_hash` já validado na Fase 02.
