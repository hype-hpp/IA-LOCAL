"""
Fase 02 - teste de parse_rerank_response. Lógica pura, sem Ollama, sem rede.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "retrieval"))
from llm_reranker import parse_rerank_response


def main():
    # Caso 1: JSON limpo e correto
    raw = '[{"index": 0, "score": 9}, {"index": 1, "score": 3}]'
    result = parse_rerank_response(raw, num_candidates=2)
    assert result == {0: 9.0, 1: 3.0}, f"resultado inesperado: {result}"
    print("[ok] JSON limpo parseado corretamente.")

    # Caso 2: JSON envolto em cercas de código markdown
    raw = '```json\n[{"index": 0, "score": 5}]\n```'
    result = parse_rerank_response(raw, num_candidates=1)
    assert result == {0: 5.0}, f"resultado inesperado: {result}"
    print("[ok] JSON com cercas de código markdown tratado.")

    # Caso 3: índice fora do intervalo é ignorado, não quebra tudo
    raw = '[{"index": 0, "score": 8}, {"index": 99, "score": 5}]'
    result = parse_rerank_response(raw, num_candidates=2)
    assert result == {0: 8.0}, f"resultado inesperado: {result}"
    print("[ok] Índice fora do intervalo ignorado sem quebrar o resto.")

    # Caso 4: lixo total -> dict vazio, sem exceção
    raw = "isso não é json de jeito nenhum"
    result = parse_rerank_response(raw, num_candidates=2)
    assert result == {}, f"esperado dict vazio, veio {result}"
    print("[ok] Texto inválido retorna dict vazio sem quebrar.")

    # Caso 5: JSON válido mas não é uma lista -> dict vazio
    raw = '{"index": 0, "score": 5}'
    result = parse_rerank_response(raw, num_candidates=1)
    assert result == {}, f"esperado dict vazio, veio {result}"
    print("[ok] JSON que não é lista retorna dict vazio.")

    print("\nTodos os testes de parsing do reranker passaram.")


if __name__ == "__main__":
    main()
