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

---

## Fase 05 (Memory) — EM ANDAMENTO

| Passo | Descrição | Status |
|---|---|---|
| 5.1 | Fundação: schema de memória em `global_scope` (`src/memory/schema.py`) | ✅ validado (teste sem rede) — pendente rodar `create_collections.py` + `ingest_document.py` no hardware real |
| 5.2 | Mecanismo `/save` (`src/memory/save.py` + `scripts/save_memory.py`) | ✅ validado (6 testes fake + promoção real no hardware, confirmado no repo via tarball) |
| 5.3 | Memória manual avulsa (`src/memory/add_note.py` + `scripts/add_memory.py`) | ✅ validado (3 testes fake + salvamento/dedup real no hardware, confirmado no repo via tarball) |
| 5.4 | Visualizar/editar/apagar memórias (`src/memory/manage.py` + `scripts/list_memories.py`/`edit_memory.py`/`delete_memory.py`) | ✅ validado (12 testes com Qdrant fake) — pendente teste real no hardware |
| 5.5 | Teste end-to-end + fechamento da fase | ⏳ pendente |

### Decisões tomadas até agora nesta fase

- **Metadata de memória só no payload do Qdrant**, sem componente novo (ex: PostgreSQL, que a Decision 004 previa para dados estruturados em geral) — decisão de hp, revisável se isso se mostrar insuficiente com uso real (regra 5 do projeto).
- **Interface continua CLI** nesta fase, não a UI Gradio/Streamlit prevista na Decision 019 — decisão de hp.
- **"Memória de conversa" fora do escopo mínimo da Fase 05** — decisão de hp: não existe Agent Core/loop de chat real ainda (só na Fase 07), então não faz sentido construir memória de conversa sem uma conversa de verdade acontecendo. Fase 05 foca em `/save` + memória semântica (`knowledge`) + memória de pesquisa (`research`) + nota manual avulsa (`manual`).
- **Três tipos de memória** definidos em `global_scope` via campo `memory_type`: `knowledge` (documento ingerido, Fase 02), `research` (evidência promovida via `/save`, 5.2), `manual` (nota livre, 5.3) — todos com o mesmo formato-base de payload (`src/memory/schema.py`), para poderem ser listados/filtrados de forma uniforme no passo 5.4.
- **Campo `ingested_at` renomeado para `saved_at`** em `ingest_document.py` (Fase 02), para ficar com o mesmo nome usado pelos outros dois tipos de memória. Sem dado real a migrar (nenhum documento indexado ainda no projeto).
- **`create_collections.py` deixou de pular a criação de índice** quando a collection já existe — agora índice é etapa separada, permitindo adicionar `memory_type` (novo, só em `global_scope`) numa instalação já em uso.
- **Bug de log corrigido (5.1, achado em teste real no hardware)**: a primeira versão do script assumia que `client.create_payload_index()` levantaria exceção se o índice já existisse, e usava isso para decidir entre imprimir `[ok] criado` ou `[skip] já existe`. Na prática, o Qdrant trata essa chamada como idempotente no servidor — nunca levanta exceção, sempre retorna sucesso — então o script sempre imprimia `[ok] criado`, mesmo rodando pela terceira vez seguida sem nada nunca para criar (nada quebrou, o índice não duplicou; só o log mentia). Corrigido checando o `payload_schema` da collection antes de decidir se precisa criar o índice, em vez de confiar em exceção.
- **Seleção explícita no `/save` (5.2)**: `chat_id` + lista de IDs específicos (`--ids`) — decisão de hp de não ter modo "promover tudo do chat de uma vez". `/save` é curadoria deliberada, não dump em massa.
- **Cópia, não move (5.2)**: o ponto original permanece em `chat_scope` depois de promovido — decisão de hp. Só some quando o chat inteiro for apagado (comportamento padrão do escopo temporário).
- **Reaproveitamento de vetor (5.2)**: a promoção usa o vetor já existente no ponto do `chat_scope` (`with_vectors=True`), sem reembeddar via Ollama — mesmo conteúdo, mesmo vetor, sem chamada nova ao modelo.
- **`is_already_saved()` centralizada em `schema.py` (5.2)**: mesma lógica de dedup por hash usada desde a Fase 02, agora compartilhada entre `/save` (5.2) e a nota manual que vem no 5.3, em vez de duplicar a consulta pela terceira vez. `ingest_document.py` manteve sua própria função local equivalente sem alteração, para não mexer de novo num arquivo já validado sem necessidade real.
- **`save_memory()` recebe o client já conectado**, em vez de abrir a conexão sozinha — permite testar a lógica de seleção/dedup com um Qdrant fake em memória (`tests/test_save_memory.py`), sem precisar de Qdrant real. Mesmo padrão de fakes já usado em `tests/test_agent_loop.py` (Fase 04).
- **Teste real do `/save` no hardware (5.2)**: pesquisa real via `web_research.py` (156 chunks em `chat_scope`) → 2 pontos promovidos com sucesso via `save_memory.py` → payload correto (`memory_type="research"`, `origin_chat_id`, `tags`) confirmado.
- **Nota manual avulsa (5.3)**: texto chega direto por `--text` (sem editor externo); `source` fixo em `"manual"` para todo ponto deste tipo, sem rótulo por nota — categorização fica por conta das `tags`, já suportadas desde o schema do 5.1.
- **Dedup evita chamada de embedding à toa (5.3)**: `add_note()` checa `is_already_saved()` (mesma função do 5.2) ANTES de chamar `embed_text()` — se a nota já existe, nem gasta uma chamada ao Ollama para um conteúdo que seria descartado de qualquer forma.
- **`embed_text` importado no nível do módulo em `add_note.py`, não injetado por parâmetro** — mesmo padrão já usado em `src/coding/agent_loop.py` (Fase 04): testes substituem `add_note.embed_text` por um fake via monkeypatch simples, sem inventar um novo mecanismo de injeção de dependência.
- **Nota manual do 5.3 validada no hardware real**: salva com sucesso (`global_scope` foi de 6 para 7 pontos), e o mesmo comando rodado de novo confirmou o dedup (`[skip] ... já existe uma memória idêntica`).
- **Editar texto sempre gera ID novo (5.4)**: como o ID em `global_scope` é derivado do `content_hash` (Decision 023), mudar o texto de uma memória necessariamente muda seu ID — decisão de hp de aceitar isso (em vez de, por exemplo, manter o ID fixo e só trocar o payload+vetor no lugar). O ponto antigo é apagado, o novo é inserido no lugar.
- **Editar tags não muda o ID (5.4)**: troca simples de payload via `set_payload`, sem reembedding — separado deliberadamente da edição de texto para não pagar o custo de reembeddar só para trocar uma tag.
- **Apagar só por ID explícito (5.4)** — decisão de hp: sem suporte a apagar em massa por filtro (`memory_type`/`tag`/`chat_id`) nesta fase, para reduzir risco de apagar mais do que o pretendido.
- **Confirmação interativa antes de apagar (5.4)**: `delete_memory.py` pede `[s/N]` por padrão, com `--yes` para pular em automação — proteção adicional não pedida explicitamente, mas coerente com a cautela da regra 11 do projeto para ferramentas que destroem dado.
- **`update_text` recusa colisão de conteúdo (5.4)**: se o texto novo já existe como outra memória (mesmo `content_hash`, logo mesmo ID via `memory_point_id()`), a edição é cancelada em vez de sobrescrever silenciosamente a memória existente — o ponto original permanece intocado nesse caso.
- **Sem índice de payload para `tags` ainda (5.4)**: filtro por tag funciona sem índice dedicado (Qdrant faz full scan), aceitável no volume atual (dataset pessoal pequeno); criar o índice em `create_collections.py` fica como ajuste futuro se a listagem ficar lenta com uso real (regra 5 do projeto).

**Fase 05 em andamento.** `06_DECISIONS.md` e `05_ROADMAP.md` do projeto principal ainda não foram atualizados com decisões formais numeradas — isso deve acontecer no fechamento da fase (passo 5.5), quando o conjunto final de decisões estiver estável.
