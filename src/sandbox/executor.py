"""
Fase 04 - 4.1: Executor do sandbox de código (Docker).

Decisões tomadas neste passo (perguntadas ao usuário antes de escrever
este arquivo, ver 06_DECISIONS.md para o registro formal):

- Container EFÊMERO por execução (`docker run --rm`), não um container
  persistente com `docker exec`. Prioriza isolamento sobre latência de
  cold start (~1-2s por chamada) — aceitável, já que o coding agent não
  é uma rota de conversação de baixa latência.
- SEM REDE por padrão (`--network none`). Código gerado que precise de
  rede vai falhar de propósito; decisão consciente para reduzir a
  superfície de risco de executar código não confiável. Revisável
  (regra 5 do projeto) se algum caso de uso real exigir rede.

Outras proteções adicionadas neste passo (engenharia padrão de sandbox,
não decisões em aberto — regra 11 do projeto: toda ferramenta
potencialmente destrutiva opera em sandbox):
- Limite de memória e CPU (evita um código gerado travar a máquina host).
- `--pids-limit` (evita fork bomb).
- `--cap-drop ALL` + `--security-opt no-new-privileges` (reduz superfície
  de escalonamento de privilégio dentro do container).
- Único volume montado é um diretório temporário criado por este módulo
  (nunca o /home do usuário — Decision 020).

Erros do CÓDIGO DO USUÁRIO (exceptions, exit code != 0, timeout) nunca
viram exceção Python aqui — viram campos de ExecutionResult, para o
chamador (o loop de iteração do 4.4) poder decidir o que fazer sem
try/except. Só uma falha de INFRAESTRUTURA (ex: Docker não instalado)
usa o campo `error`.
"""

import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from typing import Optional

IMAGE_NAME = os.environ.get("SANDBOX_IMAGE", "ia-local-sandbox:latest")

DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MEMORY_LIMIT = "512m"
DEFAULT_CPU_LIMIT = "1"
DEFAULT_PIDS_LIMIT = "100"

SCRIPT_FILENAME = "script.py"


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: Optional[int]
    timed_out: bool
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and self.error is None


def run_code(
    code: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit: str = DEFAULT_MEMORY_LIMIT,
    cpu_limit: str = DEFAULT_CPU_LIMIT,
) -> ExecutionResult:
    """
    Executa `code` (código Python) dentro de um container Docker efêmero e
    isolado (sem rede, com limites de memória/CPU/pids), e retorna
    stdout/stderr/exit_code encapsulados em ExecutionResult.
    """
    run_id = uuid.uuid4().hex[:8]
    tmp_dir = tempfile.mkdtemp(prefix=f"ia_local_sandbox_{run_id}_")

    try:
        script_path = os.path.join(tmp_dir, SCRIPT_FILENAME)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # --cap-drop ALL remove CAP_DAC_OVERRIDE: sem ela, o root DENTRO do
        # container não consegue ler arquivos que não sejam dele mesmo,
        # mesmo sendo root. tempfile.mkdtemp() cria o diretório com 0700
        # (só o dono no HOST pode acessar), então sem relaxar o bit "outros"
        # a leitura falha com "Permission denied" (visto em teste real).
        # Seguro relaxar aqui: é um script efêmero, sem dado sensível,
        # apagado no finally logo abaixo.
        os.chmod(tmp_dir, 0o755)
        os.chmod(script_path, 0o644)

        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", memory_limit,
            "--cpus", cpu_limit,
            "--pids-limit", DEFAULT_PIDS_LIMIT,
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "-v", f"{tmp_dir}:/sandbox",
            "-w", "/sandbox",
            IMAGE_NAME,
            "python", SCRIPT_FILENAME,
        ]

        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as e:
            return ExecutionResult(
                stdout=(e.stdout or ""),
                stderr=(e.stderr or ""),
                exit_code=None,
                timed_out=True,
            )
        except FileNotFoundError:
            return ExecutionResult(
                stdout="",
                stderr="",
                exit_code=None,
                timed_out=False,
                error=(
                    "Docker não encontrado no PATH. O sandbox precisa do "
                    "Docker instalado e do daemon rodando."
                ),
            )

        return ExecutionResult(
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            timed_out=False,
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    # smoke test manual
    result = run_code("print('hello from sandbox')\nprint(2 + 2)")
    print(f"exit_code={result.exit_code} timed_out={result.timed_out} success={result.success}")
    print(f"stdout: {result.stdout!r}")
    print(f"stderr: {result.stderr!r}")
