# Tutorial — Fase 03, Passo 3.5 (Fechamento da fase)

Este tutorial cobre **apenas os arquivos entregues neste passo**. Não acumula
histórico de passos anteriores (isso fica no `README.md` e no `docs/STATUS.md`).

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `tests/test_web_research_e2e.py` | `IA-LOCAL/tests/test_web_research_e2e.py` |

Além disso, os documentos-mestre do projeto (fora do repositório Git, mantidos separadamente) foram atualizados para refletir a Fase 03 concluída: `05_ROADMAP.md`, `06_DECISIONS.md` (Decisions 026-030), `08_ESTRUTURA.md` e `04_CURRENT_STATE.md`.

## O que cada coisa faz

- **`test_web_research_e2e.py`**: teste de integração cobrindo o pipeline inteiro da Fase 03 de ponta a ponta — multi-query (3.4) → busca no SearXNG (3.1) → fetch/extração via Crawl4AI (3.2) → montagem e indexação de evidências no `chat_scope` (3.3) — chamando as funções diretamente (não via subprocess), o que permite validar cada etapa com asserts específicos. Usa um `chat_id` isolado e limpa antes/depois, como os outros testes de integração da Fase 02/03.

## Como testar

```bash
cd ~/IA-LOCAL
python tests/test_web_research_e2e.py
```

Precisa de SearXNG, Ollama (embedding + GPT-OSS) e Qdrant todos no ar — é o teste mais "pesado" da Fase 03, roda o fluxo real completo.

## Checklist de validação

- [ ] `test_web_research_e2e.py` termina com `Pipeline completo da Fase 03 validado de ponta a ponta.`
- [ ] Nenhum dado de teste sobra no `chat_scope` depois (o `cleanup()` roda no início e no fim)

## Fase 03 — Resumo do que foi entregue

| Passo | Entrega |
|---|---|
| 3.1 | SearXNG (infra) + `searxng_client.py` |
| 3.2 | `page_fetcher.py` (fetch + extração via Crawl4AI) |
| 3.3 | `evidence.py` + `web_research.py` (dedup, chunking, inserção no chat_scope) |
| 3.4 | `query_expansion.py` + `multi_query.py` (multi-query via GPT-OSS) |
| 3.5 | `test_web_research_e2e.py` + fechamento da documentação |

## Próxima fase

Fase 04 — Coding Agent + Sandbox (Qwen3-Coder como Tool + Docker sandbox), conforme `05_ROADMAP.md`. Me avisa quando quiser começar que a gente aplica o mesmo processo de mini-passos.
