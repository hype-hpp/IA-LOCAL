# Tutorial — Fase 04, Passo 4.4 (Fechamento da Fase)

Cobre apenas os arquivos deste passo. Histórico completo fica no `README.md`
e no `docs/STATUS.md`.

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `tests/test_coding_agent_e2e.py` | `IA-LOCAL/tests/test_coding_agent_e2e.py` |
| `src/__init__.py` | `IA-LOCAL/src/__init__.py` |
| `src/ingestion/__init__.py` | `IA-LOCAL/src/ingestion/__init__.py` |
| `src/retrieval/__init__.py` | `IA-LOCAL/src/retrieval/__init__.py` |

Os três `__init__.py` são a limpeza pendente apontada nas verificações
anteriores do repo (só `src/search/`, `src/sandbox/` e `src/coding/` tinham
o arquivo). São vazios, não mudam nenhum comportamento — só deixam o repo
consistente com o que o `08_ESTRUTURA.md` sempre descreveu.

## O que o teste e2e cobre

`tests/test_coding_agent_e2e.py` testa o pipeline **inteiro** da Fase 04,
com Ollama e Docker reais (diferente do `test_agent_loop.py` do 4.3, que
usa fakes):

1. Tarefa simples → deve resolver (idealmente na 1ª tentativa).
2. Tarefa que tende a exigir correção (arquivo inexistente) → só confirma
   que o loop roda até o fim sem travar; não afirma que vai ter sucesso,
   porque isso depende de como o modelo decide contornar (o comportamento
   de auto-correção de verdade já foi confirmado manualmente no 4.3).
3. Tarefa que **exige rede** → essa falha é determinística de propósito:
   não depende de criatividade do modelo, o sandbox genuinamente não tem
   rede (`--network none`, Decision 031). É o jeito mais confiável de testar
   "esgota as tentativas sem travar" sem depender de o modelo cooperar em
   falhar.

## Como testar

```bash
# 1. Colocar os 4 arquivos nos caminhos da tabela acima

# 2. Rodar o teste e2e (precisa de Docker + Ollama com qwen3-coder:30b)
python tests/test_coding_agent_e2e.py

# 3. Conferir que os __init__.py não quebraram nenhum import existente —
#    rodar a suíte toda de novo por segurança
python tests/test_chunking.py
python tests/test_rrf.py
python tests/test_llm_reranker_parsing.py
python tests/test_sandbox_executor.py
python tests/test_coder_client_parsing.py
python tests/test_agent_loop.py
```

## Checklist de validação

- [ ] `python tests/test_coding_agent_e2e.py` termina com "Teste end-to-end do Coding Agent (Fase 04) passou."
- [ ] Os testes das fases anteriores (chunking, rrf, reranker parsing, etc.) continuam passando depois de adicionar os `__init__.py`
- [ ] `git status` mostra só os 4 arquivos novos, nada mais mudou por acidente

## Depois de validar

Assim que você confirmar o resultado do teste, eu preparo a atualização dos
documentos mestres do projeto (fora do repositório Git):

- `05_ROADMAP.md` — Fase 04 muda de `PENDENTE` para `CONCLUIDO`, com a lista `Entregue:`
- `06_DECISIONS.md` — Decisions 031 a 035 (as decisões tomadas ao longo da fase)
- `08_ESTRUTURA.md` — adiciona `sandbox/`, `src/sandbox/`, `src/coding/` e os novos scripts/testes à árvore
- `04_CURRENT_STATE.md` — marca os itens da Fase 04 como concluídos no checklist geral

Só fecho esses documentos depois da sua confirmação — mesma regra 18 do
projeto (nada avança sem ser testado no hardware real primeiro).
