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

## Fase 03 (Web Search + Browser) — CONCLUÍDA

| Passo | Descrição | Status |
|---|---|---|
| 3.1 | SearXNG (infra) + cliente de busca (`searxng_client.py`) | ✅ validado |
| 3.2 | Fetch + extração de conteúdo via Crawl4AI (`page_fetcher.py`) | ✅ validado |
| 3.3 | Pipeline de evidências (dedup + chunking + chat_scope, `evidence.py` + `web_research.py`) | ✅ validado |
| 3.4 | Multi-query via GPT-OSS (`query_expansion.py` + `multi_query.py`) | ✅ validado |
| 3.5 | Teste de integração end-to-end + fechamento da fase | ✅ validado |

### Decisões-chave desta fase

- Extração de conteúdo via **Crawl4AI** (já usa Playwright por baixo e entrega markdown limpo, evita montar Playwright + lib de extração separada).
- Evidências de pesquisa web vão para **chat_scope** por padrão (temporário, promovível via `/save`).
- Multi-query entra já na Fase 03, via GPT-OSS gerando variações da query (reaproveita o padrão de "worker" já usado no reranker).

---

## Fase 04 (Coding Agent + Sandbox) — CONCLUÍDA

| Passo | Descrição | Status |
|---|---|---|
| 4.1 | Infra do sandbox (`Dockerfile` + `executor.py`, container efêmero + isolamento) | ✅ validado |
| 4.2 | Tool Qwen3-Coder (`coder_client.py`, gera/corrige código via Ollama) | ✅ validado |
| 4.3 | Loop de iteração (`agent_loop.py`, executa → erro → corrige → executa de novo) | ✅ validado |
| 4.4 | Teste end-to-end + fechamento da fase (`test_coding_agent_e2e.py` + `__init__.py` faltantes) | ✅ validado |

### Decisões tomadas até agora nesta fase

- Container **efêmero** por execução (`docker run --rm`), não container persistente com `docker exec` — prioriza isolamento sobre latência de cold start.
- **Sem rede por padrão** (`--network none`) no sandbox — reduz superfície de risco de código não confiável; revisável se algum caso real precisar de rede (regra 5 do projeto).
- Limites de memória/CPU/pids + `--cap-drop ALL` + `--security-opt no-new-privileges` como proteção padrão de sandbox (regra 11 do projeto), não como decisão em aberto.
- **Bug corrigido (4.1)**: `--cap-drop ALL` remove `CAP_DAC_OVERRIDE`, então o root dentro do container não conseguia ler o script montado (dono do host, permissão `0700`). Corrigido relaxando a permissão do diretório/arquivo temporário antes do `docker run` (`0755`/`0644`).
- **Geração de código sem JSON Schema forçado** (4.2): ao contrário do reranker/query-expansion, o Qwen3-Coder responde em um bloco ```` ```python ```` cercado, extraído via regex.
- `generate_code()` cobre geração nova E correção (via `previous_code`/`error` opcionais) na mesma função — o loop de iteração (4.3) reaproveita sem duplicar lógica de prompt.
- **Loop de iteração (4.3)**: `CoderError` na geração (falha de infraestrutura) interrompe o loop imediatamente, sem contar como tentativa — diferente de uma execução que falhou por erro no código, que é elegível a correção automática.
- Validado empiricamente que `qwen3-coder:30b` é a tag correta no Ollama.
- **`DEFAULT_MAX_ATTEMPTS` ajustado de 3 para 5** (mudança feita por hp após validar o 4.3 em uso real; possível revisão futura para 10, a confirmar com mais uso real, regra 5 do projeto).
- Teste real do 4.3 confirmou o retry funcionando ponta a ponta: tarefa de leitura de CSV inexistente levou 3 tentativas até o Qwen3-Coder contornar sozinho (usando `tempfile` em vez de escrever em `/sandbox`, sem permissão de escrita sem `CAP_DAC_OVERRIDE`) — possível ajuste futuro se o sandbox precisar permitir escrita de arquivos de saída (ex: gráficos do matplotlib).
- **Teste e2e (4.4)**: a primeira versão do teste 3 (rede bloqueada) pediu só "imprimir o status code" — o Qwen3-Coder capturou a exceção de conexão com `try/except` e saiu com `exit_code=0`, contando como "sucesso" mesmo sem cumprir a tarefa de verdade (achado real em teste no hardware). Corrigido proibindo `try/except` explicitamente na instrução da tarefa, forçando o erro de rede a se propagar de verdade.
- **Limpeza de `__init__.py`** (4.4): adicionados os que faltavam em `src/`, `src/ingestion/` e `src/retrieval/`, deixando o repo consistente com o `08_ESTRUTURA.md` (pendência identificada nas verificações do repo real ao longo da fase).

**Fase 04 encerrada.** Documentos mestres (`05_ROADMAP.md`, `06_DECISIONS.md` — Decisions 031 a 035 —, `08_ESTRUTURA.md`, `04_CURRENT_STATE.md`) atualizados fora deste repositório.
