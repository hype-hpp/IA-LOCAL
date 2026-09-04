"""
Fase 04 - 4.3: CLI para testar o loop de iteração completo (Qwen3-Coder + sandbox).

Uso:
    python scripts/solve_task.py "tarefa em linguagem natural"
    python scripts/solve_task.py "tarefa em linguagem natural" --max-attempts 5
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "coding"))
from agent_loop import solve_task, DEFAULT_MAX_ATTEMPTS


def main():
    parser = argparse.ArgumentParser(description="Resolve uma tarefa via Qwen3-Coder + sandbox, com auto-correção")
    parser.add_argument("task", help="Tarefa em linguagem natural")
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS, help="Número máximo de tentativas")
    args = parser.parse_args()

    print(f"Tarefa: \"{args.task}\" (max_attempts={args.max_attempts})\n")

    result = solve_task(args.task, max_attempts=args.max_attempts)

    for i, attempt in enumerate(result.attempts, 1):
        status = "sucesso" if attempt.result.success else "falhou"
        print(f"--- Tentativa {i}: {status} ---")
        print(attempt.code)
        if attempt.result.stdout:
            print(f"\nstdout:\n{attempt.result.stdout}")
        if not attempt.result.success and attempt.result.stderr:
            print(f"\nstderr:\n{attempt.result.stderr}")
        print()

    print("=" * 40)
    if result.success:
        print(f"[ok] Resolvido em {result.attempts_used} tentativa(s).")
    else:
        print(f"[falhou] Não resolveu em {result.attempts_used} tentativa(s) (limite: {args.max_attempts}).")


if __name__ == "__main__":
    main()
