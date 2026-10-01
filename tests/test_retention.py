"""
Fase 06 - 6.5: Teste do limite de armazenamento (enforce_storage_limit)
com Qdrant fake em memória — sem rede.
"""

import os
import sys
from dataclasses import dataclass
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "crawler"))
from retention import enforce_storage_limit


@dataclass
class FakePoint:
    id: str
    payload: dict


def _match_value(filter_obj, key):
    for cond in filter_obj.must:
        if cond.key == key:
            return cond.match.value
    return None


class FakeQdrantClient:
    """Mesmo espírito do fake de test_indexer.py: scroll full-scan
    paginado, count e delete por crawl_id — sem Qdrant real."""

    def __init__(self, points):
        self.points = list(points)

    def scroll(self, collection_name, scroll_filter=None, limit=1, offset=None, **kwargs):
        start = offset or 0
        batch = self.points[start : start + limit]
        next_offset = start + limit if start + limit < len(self.points) else None
        return batch, next_offset

    def count(self, collection_name, count_filter):
        crawl_id = _match_value(count_filter, "crawl_id")
        n = sum(1 for p in self.points if p.payload.get("crawl_id") == crawl_id)
        return SimpleNamespace(count=n)

    def delete(self, collection_name, points_selector):
        crawl_id = _match_value(points_selector.filter, "crawl_id")
        self.points = [p for p in self.points if p.payload.get("crawl_id") != crawl_id]


def make_points(crawl_id, n, crawled_at):
    return [
        FakePoint(id=f"{crawl_id}-{i}", payload={"crawl_id": crawl_id, "crawled_at": crawled_at})
        for i in range(n)
    ]


def main():
    # Caso 1: dentro do limite -> não remove nada
    points = make_points("crawl_A", 3, "2026-01-01T00:00:00")
    client = FakeQdrantClient(points)
    result = enforce_storage_limit(client, max_crawl_ids=5)
    assert result == {"crawl_ids_antes": 1, "crawl_ids_removidos": [], "pontos_removidos": 0}
    assert len(client.points) == 3, "nada deveria ter sido removido"
    print("[ok] Dentro do limite, nada é removido.")

    # Caso 2: passou do limite -> remove a(s) execução(ões) mais antiga(s)
    # INTEIRA(S), nunca metade de uma execução
    points = (
        make_points("crawl_velha", 2, "2026-01-01T00:00:00")   # mais antiga
        + make_points("crawl_media", 4, "2026-01-02T00:00:00")
        + make_points("crawl_nova", 1, "2026-01-03T00:00:00")  # mais recente
    )
    client = FakeQdrantClient(points)
    result = enforce_storage_limit(client, max_crawl_ids=2)

    assert result["crawl_ids_antes"] == 3, result
    assert result["crawl_ids_removidos"] == ["crawl_velha"], result
    assert result["pontos_removidos"] == 2, result
    # Só a execução mais antiga sai; as outras duas continuam intactas e completas
    remaining_crawl_ids = {p.payload["crawl_id"] for p in client.points}
    assert remaining_crawl_ids == {"crawl_media", "crawl_nova"}, remaining_crawl_ids
    assert len(client.points) == 5, "crawl_media (4) + crawl_nova (1) deveriam sobrar inteiras"
    print("[ok] Passou do limite: remove a execução mais antiga inteira, preserva o resto intacto.")

    # Caso 3: passou por mais de uma execução de diferença -> remove várias,
    # da mais antiga pra mais nova, até caber no teto
    points = (
        make_points("crawl_1", 1, "2026-01-01T00:00:00")
        + make_points("crawl_2", 1, "2026-01-02T00:00:00")
        + make_points("crawl_3", 1, "2026-01-03T00:00:00")
        + make_points("crawl_4", 1, "2026-01-04T00:00:00")
    )
    client = FakeQdrantClient(points)
    result = enforce_storage_limit(client, max_crawl_ids=1)
    assert result["crawl_ids_removidos"] == ["crawl_1", "crawl_2", "crawl_3"], result
    assert {p.payload["crawl_id"] for p in client.points} == {"crawl_4"}
    print("[ok] Remove várias execuções antigas de uma vez até caber no teto.")

    print("\nTodos os testes do limite de armazenamento (6.5) passaram.")


if __name__ == "__main__":
    main()
