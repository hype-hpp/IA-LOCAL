"""
Fase 03 - 3.4: Teste de parse_variations_response. Lógica pura, sem Ollama, sem rede.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from query_expansion import parse_variations_response


def main():
    # Caso 1: JSON limpo e correto
    raw = '["reformulação um", "reformulação dois"]'
    result = parse_variations_response(raw, num_variations=3)
    assert result == ["reformulação um", "reformulação dois"], f"resultado inesperado: {result}"
    print("[ok] JSON limpo parseado corretamente.")

    # Caso 2: JSON envolto em cercas de código markdown
    raw = '```json\n["variação a"]\n```'
    result = parse_variations_response(raw, num_variations=3)
    assert result == ["variação a"], f"resultado inesperado: {result}"
    print("[ok] JSON com cercas de código markdown tratado.")

    # Caso 3: corta no num_variations, mesmo se o LLM mandar mais
    raw = '["a", "b", "c", "d", "e"]'
    result = parse_variations_response(raw, num_variations=2)
    assert result == ["a", "b"], f"esperado cortar em 2, veio {result}"
    print("[ok] Lista maior que num_variations é cortada.")

    # Caso 4: strings vazias/só espaço são descartadas
    raw = '["variação real", "  ", ""]'
    result = parse_variations_response(raw, num_variations=3)
    assert result == ["variação real"], f"resultado inesperado: {result}"
    print("[ok] Strings vazias descartadas.")

    # Caso 5: itens não-string são ignorados, não quebram o resto
    raw = '["boa", 123, null, "outra boa"]'
    result = parse_variations_response(raw, num_variations=3)
    assert result == ["boa", "outra boa"], f"resultado inesperado: {result}"
    print("[ok] Itens não-string ignorados sem quebrar o resto.")

    # Caso 6: lixo total -> lista vazia, sem exceção
    raw = "isso não é json de jeito nenhum"
    result = parse_variations_response(raw, num_variations=3)
    assert result == [], f"esperado lista vazia, veio {result}"
    print("[ok] Texto inválido retorna lista vazia.")

    # Caso 7: JSON válido mas não é uma lista -> lista vazia
    raw = '{"query": "não é uma lista"}'
    result = parse_variations_response(raw, num_variations=3)
    assert result == [], f"esperado lista vazia, veio {result}"
    print("[ok] JSON que não é lista retorna lista vazia.")

    print("\nTodos os testes de parsing de query_expansion passaram.")


if __name__ == "__main__":
    main()
