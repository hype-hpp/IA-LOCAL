# Tutorial — Fase 03, Passo 3.3 (Pipeline de evidências)

Este tutorial cobre **apenas os arquivos entregues neste passo**. Não acumula
histórico de passos anteriores (isso fica no `README.md` e no `docs/STATUS.md`).

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `src/search/evidence.py` | `IA-LOCAL/src/search/evidence.py` |
| `scripts/web_research.py` | `IA-LOCAL/scripts/web_research.py` |
| `tests/test_evidence_dedup.py` | `IA-LOCAL/tests/test_evidence_dedup.py` |
| `tests/test_evidence_index.py` | `IA-LOCAL/tests/test_evidence_index.py` |

## O que cada coisa faz

- **`evidence.py`**: junta o que os passos anteriores produziram — `build_evidence_chunks()` pega os resultados do `page_fetcher` (3.2), ignora páginas que falharam ou vieram vazias, e reaproveita `chunking.py` (Fase 02) para dividir o conteúdo. `index_evidence()` deduplica por hash (mesmo princípio do `ingest_document.py`, mas escopado por `chat_id`) e insere no `chat_scope` do Qdrant.
- **`web_research.py`**: o orquestrador end-to-end — recebe uma pergunta, busca no SearXNG (3.1), faz fetch das URLs candidatas (3.2), monta e indexa as evidências (3.3), tudo num só comando.
- **`test_evidence_dedup.py`**: testa a lógica pura de `build_evidence_chunks()` e `content_hash()` — sem rede, roda sempre.
- **`test_evidence_index.py`**: testa `index_evidence()` de verdade contra o Qdrant + Ollama, confirmando que reindexar o mesmo conteúdo não duplica.

## Decisão confirmada neste passo

Evidências de pesquisa web vão para o **`chat_scope`** por padrão (Decision 018) — são tratadas como temporárias, ligadas a uma conversa específica, e só viram conhecimento permanente se você promover via `/save` (mecanismo da Fase 05). O dedup é escopado por `chat_id`: o mesmo conteúdo pode existir em dois chats diferentes sem conflito, mas dentro do mesmo chat não duplica.

## Como testar

```bash
cd ~/IA-LOCAL

# 1. Teste rápido, sem rede
python tests/test_evidence_dedup.py

# 2. Teste de integração (precisa Ollama + Qdrant no ar)
python tests/test_evidence_index.py

# 3. Fluxo completo de verdade
python scripts/web_research.py "o que é RAG em inteligência artificial" --chat-id teste_3_3

# 4. Rode de novo o MESMO comando — os chunks repetidos devem ser pulados (dedup)
python scripts/web_research.py "o que é RAG em inteligência artificial" --chat-id teste_3_3
```

## Checklist de validação

- [ ] `test_evidence_dedup.py` termina com `Todos os testes de evidência (lógica pura) passaram.`
- [ ] `test_evidence_index.py` termina com `Todos os testes de indexação de evidências passaram.`
- [ ] `web_research.py` mostra as 4 etapas (busca → fetch → chunks → indexação) com números fazendo sentido
- [ ] Rodar o mesmo `web_research.py` de novo mostra `novos=0` e `pulados=N` (dedup funcionando)
- [ ] Dashboard do Qdrant (`http://localhost:6333/dashboard`) mostra os pontos no `chat_scope` com payload `chat_id`, `source`, `query`, `content_hash`, `text`

## Próximo passo (3.4)

Multi-query: em vez de buscar só a query literal do usuário, gerar variações via GPT-OSS antes de acionar o SearXNG (reaproveita o padrão de "worker" já usado no reranker da Fase 02, Decision 025).
