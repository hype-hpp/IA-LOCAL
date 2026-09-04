"""
Fase 04 - 4.3: Loop de iteração (gera -> executa -> corrige -> executa de novo).

Fluxo:
    1. generate_code(task) -> código
    2. run_code(código) no sandbox (Fase 04.1)
    3. Se sucesso -> retorna.
    4. Se falha -> generate_code(task, previous_code=código, error=<stderr>)
       -> volta pro passo 2, até `max_attempts` tentativas.

Reaproveita os dois módulos já validados nos passos anteriores sem duplicar
lógica: `coder_client.generate_code()` (4.2) e `sandbox.executor.run_code()`
(4.1). Nenhuma decisão de arquitetura nova neste passo — só orquestração do
que já existe.

Erro de infraestrutura na geração (CoderError, ex: Ollama fora do ar) não é
tratado como "tentativa falha que pode ser corrigida" — não faz sentido
pedir pro modelo corrigir um código que nem foi gerado. Nesse caso o loop
para imediatamente e retorna sucesso=False com zero tentativas registradas,
para o chamador distinguir "o código gerado não funcionou" de "não deu nem
pra gerar código".
"""

import os
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))
from coder_client import generate_code, CoderError

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sandbox"))
from executor import run_code, ExecutionResult

DEFAULT_MAX_ATTEMPTS = 5


@dataclass
class Attempt:
    code: str
    result: ExecutionResult


@dataclass
class IterationResult:
    success: bool
    task: str
    final_code: str
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def attempts_used(self) -> int:
        return len(self.attempts)


def _format_error_for_retry(result: ExecutionResult) -> str:
    """Monta o texto de erro que volta pro Qwen3-Coder no modo de correção."""
    if result.timed_out:
        return "A execução excedeu o tempo limite (possível loop infinito ou operação muito lenta)."
    if result.error:
        return f"Erro de infraestrutura ao executar: {result.error}"
    return result.stderr or (
        f"Código terminou com exit_code={result.exit_code}, mas sem mensagem em stderr."
    )


def solve_task(
    task: str,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    timeout: Optional[int] = None,
) -> IterationResult:
    """
    Gera código para `task` e tenta executá-lo no sandbox, corrigindo
    automaticamente em caso de erro, até `max_attempts` tentativas.
    """
    attempts: list[Attempt] = []
    previous_code: Optional[str] = None
    error: Optional[str] = None

    for _ in range(max_attempts):
        try:
            if previous_code is not None:
                code = generate_code(task, previous_code=previous_code, error=error)
            else:
                code = generate_code(task)
        except CoderError:
            # Falha ao GERAR (não ao executar) — não há o que corrigir, para o loop.
            break

        run_kwargs = {"timeout": timeout} if timeout is not None else {}
        result = run_code(code, **run_kwargs)
        attempts.append(Attempt(code=code, result=result))

        if result.success:
            return IterationResult(success=True, task=task, final_code=code, attempts=attempts)

        previous_code = code
        error = _format_error_for_retry(result)

    final_code = attempts[-1].code if attempts else ""
    return IterationResult(success=False, task=task, final_code=final_code, attempts=attempts)


if __name__ == "__main__":
    # smoke test manual
    r = solve_task("Imprimir os 5 primeiros números primos")
    print(f"success={r.success} attempts_used={r.attempts_used}")
    print(f"\nCódigo final:\n{r.final_code}")
    if r.attempts:
        print(f"\nstdout da última tentativa:\n{r.attempts[-1].result.stdout}")
