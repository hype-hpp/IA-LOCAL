# Tutorial — Fase 05, passo 5.5 (Teste End-to-End + Fechamento da Fase)

Este tutorial cobre **só** o arquivo entregue neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## Arquivo entregue

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `tests/test_memory_e2e.py` | `tests/test_memory_e2e.py` | Novo — teste de integração end-to-end da Fase 05 inteira |

Nenhum outro arquivo muda neste passo.

## O que o teste cobre

Pipeline completo da fase, contra Qdrant e Ollama **reais** (ao contrário
dos testes dos passos 5.1-5.4, que usam fakes):

1. Insere uma evidência de teste em `chat_scope` (mesmo formato real de
   `src/search/evidence.py`, Fase 03) — sem precisar rodar
   `web_research.py` de verdade.
2. Promove essa evidência via `/save` (5.2) e confirma `memory_type="research"`.
3. Adiciona uma nota manual (5.3) e confirma `memory_type="manual"`.
4. Lista memórias filtrando por uma tag de teste (5.4) e confirma que as
   duas aparecem.
5. Edita as tags da nota manual e confirma que o ID e o texto não mudam.
6. Edita o texto da nota manual e confirma que o ID muda (o antigo some).
7. Apaga tudo que o teste criou, nas duas collections, e confirma que
   sumiu de verdade.

Um `chat_id` e um marcador de texto exclusivos de teste
(`test_memory_e2e_5_5` / `TESTE_E2E_FASE05`) evitam colidir com dado
real. A limpeza roda em `finally` — mesmo que algum `assert` falhe no
meio do caminho, o teste tenta remover o que já tinha criado antes de
propagar o erro, para nunca deixar lixo indexado (regra 14 do projeto).

## Validação prévia (antes de chegar até você)

Simulei a lógica inteira do teste com um Qdrant fake em memória e um
`embed_text` fake, para pegar qualquer erro de lógica/import antes de te
pedir para rodar no hardware — passou de ponta a ponta. O teste real
ainda precisa ser confirmado com Qdrant/Ollama de verdade, que só existem
no seu ambiente.

## Como testar

```bash
# Único teste que falta rodar
python tests/test_memory_e2e.py
```

Saída esperada: sete blocos numerados, cada um terminando em `[ok]`, e a
mensagem final `Pipeline completo da Fase 05 validado de ponta a ponta,
sem deixar lixo indexado.`

### Checklist de validação

- [ ] `test_memory_e2e.py` roda sem erro, os 7 passos numerados aparecem com `[ok]`
- [ ] Depois de rodar, `python scripts/list_memories.py --tag TESTE_E2E_FASE05` não retorna nada (confirma que a limpeza funcionou e não sobrou lixo)
- [ ] `global_scope` e `chat_scope` voltam ao mesmo total de pontos de antes do teste

## Fechamento da Fase 05

Junto com este passo, os documentos mestres do projeto (fora deste
repositório) foram atualizados:

- `05_ROADMAP.md`: Fase 05 marcada `CONCLUIDO`, com lista de entregas
- `06_DECISIONS.md`: Decisions 036 a 042 registradas
- `08_ESTRUTURA.md`: `src/memory/` e os novos scripts/testes adicionados
- `04_CURRENT_STATE.md`: seção "Memory (Fase 05) — CONCLUÍDA" adicionada, "Memory System" marcado na arquitetura final

Depois de rodar o teste e confirmar o checklist acima, a Fase 05 está
formalmente encerrada. Próxima: Fase 06 (Adaptive Crawler), a começar
quando você der o sinal.
