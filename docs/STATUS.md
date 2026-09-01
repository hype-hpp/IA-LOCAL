# Status — Fase 02 (RAG / Knowledge)

| Passo | Descrição | Status |
|---|---|---|
| 2.1 | Estrutura de diretórios (chats/ vs knowledge/) | ✅ validado |
| 2.2 | Qdrant rodando + collections `chat_scope`/`global_scope` | ✅ validado |
| 2.3 | Embedding via Qwen3-Embedding-4B (Ollama) | ✅ validado |
| 2.4 | Parser + chunking + ingestão com dedup | ✅ validado |
| 2.5 | Hybrid search (dense + BM25/sparse) via RRF | ✅ validado |
| 2.6 | Reranker | ⏳ próximo |

## Decisões-chave desta fase

- Duas collections separadas por escopo (não uma única com filtro).
- `VECTOR_SIZE=2560`, confirmado com `qwen3-embedding:4b` oficial do Ollama.
- Chunking por palavras (250/overlap 40), não por caracteres/tokens.
- ID do ponto no Qdrant = UUID determinístico a partir do `content_hash`.
- BM25 em memória (`rank_bm25`), reconstruído por busca — não sparse vectors nativos do Qdrant (evita complexidade/modelo extra sem necessidade comprovada).
- Fusão dense+sparse via RRF (k=60), não normalização de score.

(Detalhes completos de cada decisão devem ir para o `06_DECISIONS.md` do projeto principal, não duplicados aqui.)
