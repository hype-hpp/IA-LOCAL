"""
Fase 04 - 4.1: Teste do executor do sandbox.

Pré-requisitos:
    - Docker instalado e o daemon rodando
    - Imagem construída: ./scripts/build_sandbox.sh
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "sandbox"))
from executor import run_code


def main():
    print("1. Código simples (stdout esperado)...")
    result = run_code("print('ola do sandbox')\nprint(1 + 1)")
    assert result.success, f"esperava sucesso, veio: {result}"
    assert "ola do sandbox" in result.stdout
    assert "2" in result.stdout
    print("   [ok]")

    print("2. Código com erro (exit_code != 0, sem lançar exceção Python aqui)...")
    result = run_code("raise ValueError('erro proposital')")
    assert not result.success, "esperava falha, mas success=True"
    assert result.exit_code != 0
    assert "ValueError" in result.stderr
    print("   [ok]")

    print("3. Sem acesso à rede (deve falhar ao tentar conectar)...")
    result = run_code(
        "import requests\n"
        "requests.get('http://example.com', timeout=3)\n"
    )
    assert not result.success, "esperava falha por falta de rede, mas teve sucesso"
    print("   [ok] (rede bloqueada como esperado)")

    print("4. Timeout (código que roda mais que o limite)...")
    result = run_code("import time\ntime.sleep(10)", timeout=2)
    assert result.timed_out, f"esperava timed_out=True, veio: {result}"
    print("   [ok]")

    print("5. Pacote pré-instalado disponível (numpy)...")
    result = run_code("import numpy as np\nprint(np.array([1, 2, 3]).sum())")
    assert result.success, f"esperava sucesso, veio: {result}"
    assert "6" in result.stdout
    print("   [ok]")

    print("6. Diretórios temporários não deixam lixo para trás...")
    import tempfile
    before = set(os.listdir(tempfile.gettempdir()))
    run_code("print('teste de limpeza')")
    after = set(os.listdir(tempfile.gettempdir()))
    leftover = [d for d in (after - before) if d.startswith("ia_local_sandbox_")]
    assert not leftover, f"diretório temporário não foi limpo: {leftover}"
    print("   [ok]")

    print("\nTodos os testes do executor do sandbox passaram.")


if __name__ == "__main__":
    main()
