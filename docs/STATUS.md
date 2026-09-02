# Status — Progresso do Projeto

## Fase 02 (RAG / Knowledge) — CONCLUÍDA

| Passo | Descrição | Status |
|---|---|---|
| 2.1 | Estrutura de diretórios (chats/ vs knowledge/) | ✅ validado |
| 2.2 | Qdrant rodando + collections `chat_scope`/`global_scope` | ✅ validado |
| 2.3 | Embedding via Qwen3-Embedding-4B (Ollama) | ✅ validado |
| 2.4 | Parser + chunking + ingestão com dedup | ✅ validado |
| 2.5 | Hybrid search (dense + BM25/sparse) via RRF | ✅ validado |
| 2.6 | Reranker via GPT-OSS | ✅ validado |

### Decisões-chave desta fase

- Duas collections separadas por escopo (não uma única com filtro).
- `VECTOR_SIZE=2560`, confirmado com `qwen3-embedding:4b` oficial do Ollama.
- Chunking por palavras (250/overlap 40), não por caracteres/tokens.
- ID do ponto no Qdrant = UUID determinístico a partir do `content_hash`.
- BM25 em memória (`rank_bm25`), reconstruído por busca — não sparse vectors nativos do Qdrant.
- Fusão dense+sparse via RRF (k=60), não normalização de score.
- Reranker via GPT-OSS (sem modelo dedicado), grammar-constrained JSON Schema.

(Detalhes completos de cada decisão ficam no `06_DECISIONS.md` do projeto principal, não duplicados aqui.)

---

## Fase 03 (Web Search + Browser) — EM ANDAMENTO

| Passo | Descrição | Status |
|---|---|---|
| 3.1 | SearXNG (infra) + cliente de busca (`searxng_client.py`) | ✅ validado |
| 3.2 | Fetch + extração de conteúdo via Crawl4AI (`page_fetcher.py`) | ✅ validado |
| 3.3 | Pipeline de evidências (dedup + chunking + chat_scope, `evidence.py` + `web_research.py`) | ✅ validado |
| 3.4 | Multi-query via GPT-OSS (`query_expansion.py` + `multi_query.py`) | ⏳ aguardando validação |
| 3.5 | Testes finais de integração + fechamento da fase | pendente |

### Decisões-chave desta fase (confirmadas até agora)

- Extração de conteúdo via **Crawl4AI** (já usa Playwright por baixo e entrega markdown limpo, evita montar Playwright + lib de extração separada).
- Evidências de pesquisa web vão para **chat_scope** por padrão (temporário, promovível via `/save`).
- Multi-query entra já na Fase 03, via GPT-OSS gerando variações da query (reaproveita o padrão de "worker" já usado no reranker).
