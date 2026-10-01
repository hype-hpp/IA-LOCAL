"""
Fase 06 - 6.5: Limite de armazenamento do crawl_scope.

Isso não vem do crawl4ai — é política nossa (regra 13 do projeto:
limitar armazenamento, cache e crawling; regra 14: evitar indexação de
conteúdo irrelevante acumulando pra sempre).

Decisões (hp, 6.5):
  - Quando o número de EXECUÇÕES (crawl_id) distintas em crawl_scope
    passar do teto, remove sozinho as execuções mais antigas INTEIRAS
    (todos os pontos daquele crawl_id de uma vez, nunca metade de uma
    execução) — mantém cada crawl_id coerente.
  - Automático, mas com log do que foi removido — diferente da Decision
    040 do /memory (apagar só por ID explícito, sem automação), porque
    aqui é uma rotina de manutenção que roda a cada indexação, não um
    comando destrutivo disparado manualmente pelo usuário sobre memória
    curada à mão.
"""

import os

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

from schema import COLLECTION

DEFAULT_MAX_CRAWL_IDS = int(os.environ.get("CRAWL_SCOPE_MAX_CRAWL_IDS", "50"))
SCROLL_BATCH_SIZE = 256


def _earliest_crawled_at_per_crawl_id(client: QdrantClient) -> dict:
    """Varre crawl_scope inteiro (só os campos crawl_id/crawled_at do
    payload, sem vetor) e retorna {crawl_id: crawled_at mais antigo}."""
    earliest = {}
    offset = None
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION,
            limit=SCROLL_BATCH_SIZE,
            offset=offset,
            with_payload=["crawl_id", "crawled_at"],
            with_vectors=False,
        )
        for point in points:
            crawl_id = point.payload.get("crawl_id")
            crawled_at = point.payload.get("crawled_at")
            if crawl_id is None or crawled_at is None:
                continue
            if crawl_id not in earliest or crawled_at < earliest[crawl_id]:
                earliest[crawl_id] = crawled_at
        if offset is None:
            break
    return earliest


def enforce_storage_limit(
    client: QdrantClient, max_crawl_ids: int = DEFAULT_MAX_CRAWL_IDS
) -> dict:
    """
    Se o número de execuções (crawl_id) distintas em crawl_scope passar
    de max_crawl_ids, apaga as execuções mais antigas INTEIRAS (todos os
    pontos daquele crawl_id), da mais antiga pra mais nova, até voltar
    dentro do limite. Imprime um log de cada execução removida.

    Retorna um resumo: {"crawl_ids_antes": N, "crawl_ids_removidos": [...],
    "pontos_removidos": N}.
    """
    earliest = _earliest_crawled_at_per_crawl_id(client)
    total_crawl_ids = len(earliest)

    if total_crawl_ids <= max_crawl_ids:
        return {"crawl_ids_antes": total_crawl_ids, "crawl_ids_removidos": [], "pontos_removidos": 0}

    ordered_oldest_first = sorted(earliest.items(), key=lambda item: item[1])
    n_to_remove = total_crawl_ids - max_crawl_ids
    to_remove = [crawl_id for crawl_id, _ in ordered_oldest_first[:n_to_remove]]

    pontos_removidos = 0
    for crawl_id in to_remove:
        crawl_id_filter = Filter(must=[FieldCondition(key="crawl_id", match=MatchValue(value=crawl_id))])

        n_points = client.count(collection_name=COLLECTION, count_filter=crawl_id_filter).count
        client.delete(collection_name=COLLECTION, points_selector=FilterSelector(filter=crawl_id_filter))
        pontos_removidos += n_points

        print(
            f"[retention] Removida execução '{crawl_id}' de crawl_scope "
            f"({n_points} pontos, mais antiga desde {earliest[crawl_id]})"
        )

    print(
        f"[retention] crawl_scope tinha {total_crawl_ids} execuções "
        f"(teto: {max_crawl_ids}); removidas {len(to_remove)}, "
        f"restam {max_crawl_ids}."
    )

    return {
        "crawl_ids_antes": total_crawl_ids,
        "crawl_ids_removidos": to_remove,
        "pontos_removidos": pontos_removidos,
    }
