# Tutorial — Fase 04, Passo 4.1 (Infra do Sandbox)

Este tutorial cobre **apenas os arquivos entregues neste passo**. Não acumula
histórico de passos anteriores (isso fica no `README.md` e no `docs/STATUS.md`).

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `sandbox/Dockerfile` | `IA-LOCAL/sandbox/Dockerfile` |
| `scripts/build_sandbox.sh` | `IA-LOCAL/scripts/build_sandbox.sh` |
| `src/sandbox/__init__.py` | `IA-LOCAL/src/sandbox/__init__.py` |
| `src/sandbox/executor.py` | `IA-LOCAL/src/sandbox/executor.py` |
| `tests/test_sandbox_executor.py` | `IA-LOCAL/tests/test_sandbox_executor.py` |

Nenhum arquivo existente foi modificado neste passo — tudo é novo.

## O que cada coisa faz

- **`sandbox/Dockerfile`**: imagem do sandbox de execução, `python:3.11-slim` +
  `numpy`, `pandas`, `requests`, `beautifulsoup4`, `matplotlib`, `scipy`
  pré-instalados (Decision 020). Sem `ENTRYPOINT` fixo — o comando real é
  passado pelo `executor.py` no momento do `docker run`.
- **`scripts/build_sandbox.sh`**: builda a imagem localmente com a tag
  `ia-local-sandbox:latest`. Rodar de novo sempre que o Dockerfile mudar.
- **`src/sandbox/executor.py`**: função `run_code(code, timeout=30, ...)` que
  sobe um container **efêmero** (`docker run --rm`), roda o código recebido
  como um script Python, e devolve um `ExecutionResult` com `stdout`,
  `stderr`, `exit_code`, `timed_out` e `error`. Duas decisões de arquitetura
  confirmadas com você antes de escrever este arquivo:
  - Container novo e descartável a cada execução (não um container
    persistente com `docker exec`).
  - Sem rede por padrão (`--network none`).

  Além disso, o executor aplica limites de memória (512m), CPU (1 core),
  número de processos (`--pids-limit 100`), remove todas as capabilities
  Linux (`--cap-drop ALL`) e bloqueia escalonamento de privilégio
  (`--security-opt no-new-privileges`) — proteção padrão de sandbox, não uma
  decisão em aberto (regra 11 do projeto). O único volume montado é um
  diretório temporário criado e apagado pelo próprio módulo, nunca o `/home`
  do usuário.

  Erros do **código do usuário** (exceptions, exit code != 0, timeout) nunca
  viram exceção Python — viram campos do `ExecutionResult`. Só uma falha de
  **infraestrutura** (ex: Docker não instalado) usa o campo `error`. Isso
  importa para o passo 4.4 (loop de iteração): o chamador só precisa checar
  campos, sem `try/except` espalhado.
- **`tests/test_sandbox_executor.py`**: valida código simples, código com
  erro, bloqueio de rede, timeout, uso de pacote pré-instalado, e limpeza do
  diretório temporário.

## Como testar

```bash
# 1. Colocar os arquivos nos caminhos da tabela acima

# 2. Buildar a imagem do sandbox
chmod +x scripts/build_sandbox.sh
./scripts/build_sandbox.sh

# 3. Teste manual rápido (smoke test do próprio módulo)
python src/sandbox/executor.py

# 4. Rodar o teste completo
python tests/test_sandbox_executor.py
```

## Checklist de validação

- [ ] `./scripts/build_sandbox.sh` builda sem erro e a imagem aparece em `docker images`
- [ ] `python src/sandbox/executor.py` imprime `success=True` e o stdout esperado
- [ ] `python tests/test_sandbox_executor.py` termina com `Todos os testes do executor do sandbox passaram.`
- [ ] Depois de rodar os testes, ` ` não mostra containers órfãos do sandbox (o `--rm` deve limpar tudo sozinho)
- [ ] Nenhum diretório `ia_local_sandbox_*` sobra em `/tmp` depois dos testes

## Próximo passo (4.2)

Com o executor validado, o passo 4.2 cobre a integração do Qwen3-Coder como
tool do orquestrador (mesmo padrão da Decision 016/025): uma função que
recebe uma tarefa em linguagem natural e devolve código gerado, pronto para
ser passado ao `run_code()` deste passo.
