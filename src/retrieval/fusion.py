"""
Fase 02 - 2.5a: Reciprocal Rank Fusion (RRF).

Combina múltiplas listas rankeadas (ex: resultado dense + resultado sparse)
em uma única lista, sem precisar normalizar as escalas de score de cada uma
(esse é o problema que o RRF resolve: cosine similarity e BM25 score não
são comparáveis diretamente, mas a POSIÇÃO no ranking é).

Fórmula: score(doc) = soma, para cada lista em que o doc aparece, de 1/(k + rank)
k=60 é o valor padrão usado na literatura original (Cormack et al.).
"""

DEFAULT_K = 60


def reciprocal_rank_fusion(*ranked_lists: list[str], k: int = DEFAULT_K) -> list[tuple[str, float]]:
    """
    Recebe N listas de IDs (cada uma já ordenada da mais relevante pra menos)
    e retorna uma lista única (id, score_fundido) ordenada por relevância combinada.
    """
    scores: dict[str, float] = {}

    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)
