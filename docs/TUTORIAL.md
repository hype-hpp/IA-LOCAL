# Tutorial — Fase 03, Passo 3.4 (Multi-query via GPT-OSS)

Este tutorial cobre **apenas os arquivos entregues neste passo**. Não acumula
histórico de passos anteriores (isso fica no `README.md` e no `docs/STATUS.md`).

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `src/search/query_expansion.py` | `IA-LOCAL/src/search/query_expansion.py` |
| `src/search/multi_query.py` | `IA-LOCAL/src/search/multi_query.py` |
| `scripts/web_research.py` | `IA-LOCAL/scripts/web_research.py` (substitui o do 3.3 — mesma ideia, agora com multi-query) |
| `tests/test_query_expansion_parsing.py` | `IA-LOCAL/tests/test_query_expansion_parsing.py` |
| `tests/test_multi_query_dedup.py` | `IA-LOCAL/tests/test_multi_query_dedup.py` |

## O que cada coisa faz

- **`query_expansion.py`**: reaproveita o GPT-OSS (já residente na VRAM, mesmo princípio do reranker — Decision 025) para gerar variações da pergunta do usuário via prompt + JSON Schema forçado. Se o LLM falhar ou não devolver nada parseável, retorna lista vazia — não é erro fatal, só significa que a busca segue só com a query original.
- **`multi_query.py`**: junta a query original com as variações (`merge_queries`, sem duplicatas), busca cada uma no SearXNG, e deduplica os resultados por URL (`_dedup_by_url`) — a mesma página não aparece duas vezes só porque foi encontrada por duas queries diferentes.
- **`web_research.py`**: agora usa multi-query por padrão. Flag `--no-multi-query` pula a geração de variações (útil pra debug ou pra comparar antes/depois). Flag `--num-variations` controla quantas variações gerar (default 3).
- **`test_query_expansion_parsing.py`** e **`test_multi_query_dedup.py`**: testam a lógica pura (parsing da resposta do LLM, merge de queries, dedup por URL) sem precisar de rede — mesmo padrão do `test_llm_reranker_parsing.py` da Fase 02.

## Decisão confirmada neste passo

Multi-query entra na Fase 03 (não ficou pra depois), reaproveitando o GPT-OSS como worker — mesmo padrão já estabelecido no reranker (Decision 025) e no roteamento código/geral (Decision 016): usar o modelo já residente na VRAM para tarefas auxiliares em vez de subir lógica ou modelo dedicado.

## Como testar

```bash
cd ~/IA-LOCAL

# 1. Testes rápidos, sem rede
python tests/test_query_expansion_parsing.py
python tests/test_multi_query_dedup.py

# 2. Fluxo completo com multi-query (padrão)
python scripts/web_research.py "o que é RAG em inteligência artificial" --chat-id teste_3_4

# 3. Comparação: mesma busca sem multi-query
python scripts/web_research.py "o que é RAG em inteligência artificial" --chat-id teste_3_4 --no-multi-query
```

## Checklist de validação

- [ ] `test_query_expansion_parsing.py` termina com `Todos os testes de parsing de query_expansion passaram.`
- [ ] `test_multi_query_dedup.py` termina com `Todos os testes de multi_query (lógica pura) passaram.`
- [ ] `web_research.py` (com multi-query) mostra as queries geradas antes da busca, e o número de URLs únicas após dedup
- [ ] Rodar com `--no-multi-query` mostra só a query original na lista de "Queries usadas"
- [ ] Nenhuma URL duplicada aparece entre os candidatos finais

## Próximo passo (3.5)

Fechamento da Fase 03: revisão geral, testes de integração end-to-end cobrindo o pipeline completo, e atualização dos documentos-mestre (`05_ROADMAP.md`, `06_DECISIONS.md`, `08_ESTRUTURA.md`) — igual foi feito ao fechar a Fase 02.
