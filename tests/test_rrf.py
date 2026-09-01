"""
Fase 02 - teste da fusão RRF. Lógica pura, sem Qdrant, sem Ollama, sem rede.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "retrieval"))
from fusion import reciprocal_rank_fusion


def main():
    # Caso 1: mesmo doc aparece bem rankeado nas duas listas -> deve ganhar
    dense = ["docA", "docB", "docC"]
    sparse = ["docA", "docC", "docB"]
    result = reciprocal_rank_fusion(dense, sparse)
    assert result[0][0] == "docA", f"esperado docA em 1º lugar, veio {result[0][0]}"
    print("[ok] Doc bem rankeado nas duas listas vence.")

    # Caso 2: doc só aparece em uma lista ainda entra no resultado
    dense = ["docX", "docY"]
    sparse = ["docZ"]
    result = reciprocal_rank_fusion(dense, sparse)
    ids = [doc_id for doc_id, _ in result]
    assert set(ids) == {"docX", "docY", "docZ"}, f"faltou algum doc: {ids}"
    print("[ok] Docs exclusivos de uma lista aparecem no resultado combinado.")

    # Caso 3: doc que aparece nas duas listas pontua mais que um que só aparece em uma
    dense = ["docP", "docQ"]
    sparse = ["docQ", "docP"]
    result = reciprocal_rank_fusion(dense, sparse)
    scores = dict(result)
    only_dense_score = reciprocal_rank_fusion(["docSolo"])[0][1]
    assert scores["docQ"] > only_dense_score, "doc em duas listas deveria pontuar mais"
    print("[ok] Doc presente em duas listas pontua mais que doc solo.")

    # Caso 4: listas vazias não quebram
    result = reciprocal_rank_fusion([], [])
    assert result == [], "listas vazias deveriam retornar resultado vazio"
    print("[ok] Listas vazias tratadas corretamente.")

    print("\nTodos os testes de RRF passaram.")


if __name__ == "__main__":
    main()
