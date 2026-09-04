"""
Fase 04 - 4.2: Teste de extract_code(). Lógica pura, sem Ollama, sem rede.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "coding"))
from coder_client import extract_code, build_prompt


def main():
    # Caso 1: bloco cercado com a tag "python"
    raw = "Aqui está o código:\n```python\nprint('oi')\n```\nEspero que ajude."
    result = extract_code(raw)
    assert result == "print('oi')", f"resultado inesperado: {result!r}"
    print("[ok] Bloco cercado com tag 'python' extraído corretamente.")

    # Caso 2: bloco cercado sem tag de linguagem
    raw = "```\nx = 1\nprint(x)\n```"
    result = extract_code(raw)
    assert result == "x = 1\nprint(x)", f"resultado inesperado: {result!r}"
    print("[ok] Bloco cercado sem tag de linguagem extraído corretamente.")

    # Caso 3: sem cerca nenhuma -> fallback tolerante, devolve o texto inteiro
    raw = "print('sem cerca nenhuma')"
    result = extract_code(raw)
    assert result == "print('sem cerca nenhuma')", f"resultado inesperado: {result!r}"
    print("[ok] Resposta sem cerca tratada como fallback (texto inteiro).")

    # Caso 4: múltiplos blocos cercados -> extrai só o primeiro
    raw = "```python\nprimeiro = 1\n```\ntexto no meio\n```python\nsegundo = 2\n```"
    result = extract_code(raw)
    assert result == "primeiro = 1", f"resultado inesperado: {result!r}"
    print("[ok] Múltiplos blocos: extraído apenas o primeiro.")

    # Caso 5: resposta vazia -> string vazia (generate_code() trata isso como erro)
    result = extract_code("")
    assert result == "", f"esperado string vazia, veio: {result!r}"
    print("[ok] Resposta vazia retorna string vazia.")

    # Caso 6: build_prompt sem previous_code/error -> prompt de geração nova
    prompt = build_prompt("somar dois números")
    assert "somar dois números" in prompt
    assert "Código anterior" not in prompt
    print("[ok] build_prompt() sem contexto de erro monta prompt de geração nova.")

    # Caso 7: build_prompt com previous_code/error -> prompt de correção
    prompt = build_prompt("somar dois números", previous_code="print(1+", error="SyntaxError")
    assert "Código anterior" in prompt
    assert "print(1+" in prompt
    assert "SyntaxError" in prompt
    print("[ok] build_prompt() com contexto de erro monta prompt de correção.")

    print("\nTodos os testes de parsing do coder_client passaram.")


if __name__ == "__main__":
    main()
