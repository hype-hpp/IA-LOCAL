# Tutorial — Fase 04, Passo 4.3 (Loop de Iteração)

Cobre apenas os arquivos deste passo. Histórico completo fica no `README.md`
e no `docs/STATUS.md`.

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `src/coding/agent_loop.py` | `IA-LOCAL/src/coding/agent_loop.py` |
| `tests/test_agent_loop.py` | `IA-LOCAL/tests/test_agent_loop.py` |
| `scripts/solve_task.py` | `IA-LOCAL/scripts/solve_task.py` |

Nada dos passos 4.1/4.2 foi modificado.

## O que cada coisa faz

- **`src/coding/agent_loop.py`**: função `solve_task(task, max_attempts=3)` que
  fecha o ciclo completo da Fase 04:
  1. `generate_code(task)` (4.2) → código
  2. `run_code(código)` no sandbox (4.1)
  3. Sucesso → retorna.
  4. Falha → `generate_code(task, previous_code=código, error=stderr)` (modo
     correção) → volta pro passo 2, até `max_attempts` tentativas.

  Não teve decisão de arquitetura nova neste passo — é só orquestração dos
  dois módulos já validados, sem duplicar lógica de prompt ou de execução.

  Um detalhe que vale destacar: erro de **infraestrutura na geração**
  (`CoderError`, ex: Ollama fora do ar) não é tratado como "tentativa que
  falhou e pode ser corrigida" — não faz sentido pedir pro modelo corrigir
  um código que nem chegou a ser gerado. Nesse caso o loop para na hora,
  com `attempts_used=0`, pra quem chama conseguir distinguir "o código
  gerado não funcionou" de "não deu nem pra gerar código".

- **`tests/test_agent_loop.py`**: testa só o **controle do loop**, com
  `generate_code()` e `run_code()` substituídos por versões falsas
  (monkeypatch simples, sem lib externa) — não chama Ollama nem Docker de
  verdade. Cobre: sucesso na 1ª tentativa, falha→falha→sucesso na 3ª
  (confirmando que o erro certo é repassado a cada retry), sempre falha até
  esgotar `max_attempts`, e `CoderError` na geração interrompendo o loop
  sem tentar executar nada.

- **`scripts/solve_task.py`**: CLI para rodar o loop completo de verdade
  (Ollama + Docker reais), mostrando cada tentativa, o código gerado, e se
  no final resolveu ou esgotou as tentativas.

## Como testar

```bash
# 1. Colocar os arquivos nos caminhos da tabela acima

# 2. Teste de controle do loop (rápido, sem rede, sem Docker)
python tests/test_agent_loop.py

# 3. Teste real, tarefa simples que deve resolver de primeira
python scripts/solve_task.py "somar os 10 primeiros números pares"

# 4. Teste real forçando correção — peça algo ambíguo o suficiente pra
#    aumentar a chance do modelo errar na 1a tentativa e você ver o
#    retry acontecer
python scripts/solve_task.py "ler um arquivo chamado dados.csv e imprimir a soma da coluna 'valor'" --max-attempts 3
```

## Checklist de validação

- [ ] `python tests/test_agent_loop.py` termina com "Todos os testes do agent_loop passaram."
- [ ] `python scripts/solve_task.py "..."` resolve uma tarefa simples em 1 tentativa
- [ ] Alguma tarefa (pode forçar com algo mais complicado) mostra pelo menos 2 tentativas no output, confirmando que o retry com correção está funcionando de verdade
- [ ] Uma tarefa proposital-mente impossível (ex: "leia um arquivo que não existe e imprima seu conteúdo") esgota as `max_attempts` e termina com `[falhou]`, sem travar nem lançar exceção não tratada

## Próximo passo (4.4 — fechamento da fase)

Teste de integração end-to-end da Fase 04 completa, atualização do
`05_ROADMAP.md`, registro das Decisions novas em `06_DECISIONS.md`,
atualização do `08_ESTRUTURA.md` e `04_CURRENT_STATE.md` — e aproveitar pra
limpar os `__init__.py` que ainda faltam em `src/`, `src/ingestion/` e
`src/retrieval/` (pendência apontada na verificação do repo real).
