"""
Fase 04 - 4.3: Teste do loop de iteração (agent_loop).

Lógica pura: substitui generate_code() e run_code() por versões falsas
(monkeypatch simples, sem lib externa) para testar só o CONTROLE do loop
— quantas tentativas, quando para, o que é repassado como erro — sem
depender de Ollama nem Docker rodando de verdade.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "coding"))
import agent_loop
from coder_client import CoderError

ExecutionResult = agent_loop.ExecutionResult


def make_result(success: bool, stderr: str = "", exit_code: int = 0) -> ExecutionResult:
    return ExecutionResult(
        stdout="",
        stderr=stderr,
        exit_code=(0 if success else (exit_code or 1)),
        timed_out=False,
    )


def main():
    original_generate_code = agent_loop.generate_code
    original_run_code = agent_loop.run_code

    try:
        # Caso 1: sucesso já na primeira tentativa
        agent_loop.generate_code = lambda task, previous_code=None, error=None: "print(1)"
        agent_loop.run_code = lambda code, **kw: make_result(success=True)

        result = agent_loop.solve_task("tarefa qualquer")
        assert result.success, "esperava sucesso na 1a tentativa"
        assert result.attempts_used == 1, f"esperava 1 tentativa, veio {result.attempts_used}"
        print("[ok] Sucesso na primeira tentativa: para no attempts_used=1.")

        # Caso 2: falha, falha, sucesso na 3a -> confirma retry e repasse do erro
        call_log = []

        def fake_generate(task, previous_code=None, error=None):
            call_log.append((previous_code, error))
            return f"codigo_tentativa_{len(call_log)}"

        attempts_counter = {"n": 0}

        def fake_run(code, **kw):
            attempts_counter["n"] += 1
            if attempts_counter["n"] < 3:
                return make_result(success=False, stderr=f"erro na tentativa {attempts_counter['n']}")
            return make_result(success=True)

        agent_loop.generate_code = fake_generate
        agent_loop.run_code = fake_run

        result = agent_loop.solve_task("tarefa qualquer", max_attempts=5)
        assert result.success, "esperava sucesso na 3a tentativa"
        assert result.attempts_used == 3, f"esperava 3 tentativas, veio {result.attempts_used}"
        assert call_log[0] == (None, None), "1a chamada deveria ser geração nova (sem previous_code/error)"
        assert call_log[1][0] == "codigo_tentativa_1", "2a chamada deveria receber o código da 1a tentativa"
        assert "erro na tentativa 1" in call_log[1][1], "2a chamada deveria receber o erro da 1a tentativa"
        print("[ok] Falha->falha->sucesso: 3 tentativas, erro repassado corretamente a cada retry.")

        # Caso 3: sempre falha -> para no max_attempts, success=False
        agent_loop.generate_code = lambda task, previous_code=None, error=None: "codigo_ruim"
        agent_loop.run_code = lambda code, **kw: make_result(success=False, stderr="sempre falha")

        result = agent_loop.solve_task("tarefa qualquer", max_attempts=4)
        assert not result.success, "esperava success=False após esgotar tentativas"
        assert result.attempts_used == 4, f"esperava 4 tentativas, veio {result.attempts_used}"
        assert result.final_code == "codigo_ruim"
        print("[ok] Sempre falha: para exatamente em max_attempts, success=False.")

        # Caso 4: geração falha (CoderError) logo na 1a tentativa -> para sem tentar executar
        def raise_coder_error(task, previous_code=None, error=None):
            raise CoderError("Ollama fora do ar")

        run_call_count = {"n": 0}

        def run_should_not_be_called(code, **kw):
            run_call_count["n"] += 1
            return make_result(success=True)

        agent_loop.generate_code = raise_coder_error
        agent_loop.run_code = run_should_not_be_called

        result = agent_loop.solve_task("tarefa qualquer")
        assert not result.success, "esperava success=False quando a geração falha"
        assert result.attempts_used == 0, "não deveria haver tentativas registradas"
        assert run_call_count["n"] == 0, "run_code não deveria ser chamado se a geração falhou"
        print("[ok] CoderError na geração: loop para imediatamente, sem tentar executar.")

        print("\nTodos os testes do agent_loop passaram.")

    finally:
        agent_loop.generate_code = original_generate_code
        agent_loop.run_code = original_run_code


if __name__ == "__main__":
    main()
