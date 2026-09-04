"""
Fase 04 - 4.2: CLI para testar a geração de código via Qwen3-Coder.

Uso:
    python scripts/generate_code.py "some os 10 primeiros números pares"
    python scripts/generate_code.py "some os 10 primeiros números pares" --run
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "coding"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "sandbox"))
from coder_client import generate_code, CoderError
from executor import run_code


def main():
    parser = argparse.ArgumentParser(description="Gera código Python via Qwen3-Coder")
    parser.add_argument("task", help="Tarefa em linguagem natural")
    parser.add_argument("--run", action="store_true", help="Executa o código gerado no sandbox (Fase 04.1) logo em seguida")
    args = parser.parse_args()

    print(f"Gerando código para: \"{args.task}\"\n")

    try:
        code = generate_code(args.task)
    except CoderError as e:
        print(f"[erro] {e}")
        return

    print("Código gerado:\n")
    print(code)

    if not args.run:
        return

    print("\nExecutando no sandbox...\n")
    result = run_code(code)
    print(f"exit_code={result.exit_code} timed_out={result.timed_out} success={result.success}")
    if result.stdout:
        print(f"\nstdout:\n{result.stdout}")
    if result.stderr:
        print(f"\nstderr:\n{result.stderr}")


if __name__ == "__main__":
    main()
