"""
Fase 05 - 5.2: Teste do mecanismo /save com um Qdrant fake em memória.
Sem rede, sem Qdrant real — mesmo padrão de fakes já usado em
tests/test_agent_loop.py (Fase 04) para testar lógica de controle sem
depender de infraestrutura externa.
"""

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from save import save_memory


@dataclass
class FakePoint:
    id: str
    payload: dict
    vector: list


class FakeQdrantClient:
    """
    Reimplementa só o pedacinho da API do QdrantClient que save_memory()
    e is_already_saved() realmente usam: retrieve, scroll (filtrado por
    content_hash) e upsert.
    """

    def __init__(self, chat_points, global_hashes=None):
        self._chat_points = {p.id: p for p in chat_points}
        self._global_hashes = set(global_hashes or [])
        self.upserted = []

    def retrieve(self, collection_name, ids, with_payload=True, with_vectors=True):
        return [self._chat_points[i] for i in ids if i in self._chat_points]

    def scroll(self, collection_name, scroll_filter, limit=1, **kwargs):
        chash = None
        for cond in scroll_filter.must:
            if cond.key == "content_hash":
                chash = cond.match.value
        found = chash in self._global_hashes
        fake_hit = [FakePoint(id="x", payload={}, vector=[])] if found else []
        return fake_hit, None

    def upsert(self, collection_name, points):
        self.upserted.extend(points)
        for p in points:
            self._global_hashes.add(p.payload["content_hash"])


def make_point(id_, chat_id, text, chash, vector=None, **extra_payload):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "content_hash": chash,
        "source": "http://exemplo.com",
    }
    payload.update(extra_payload)
    return FakePoint(id=id_, payload=payload, vector=vector or [0.1, 0.2, 0.3])


def main():
    # Caso 1: promoção simples de um ponto válido
    points = [make_point("p1", "chat_A", "texto de evidência", "hashA")]
    client = FakeQdrantClient(points)
    result = save_memory(client, "chat_A", ["p1"], tags=["projeto_x"])
    assert result["promovidos"] == 1, result
    assert len(client.upserted) == 1
    saved_payload = client.upserted[0].payload
    assert saved_payload["memory_type"] == "research"
    assert saved_payload["origin_chat_id"] == "chat_A"
    assert saved_payload["tags"] == ["projeto_x"]
    print("[ok] Promoção simples funciona e aplica memory_type/origin_chat_id/tags.")

    # Caso 2: ponto cujo hash já existe no global_scope -> não promove de novo
    points = [make_point("p2", "chat_A", "texto repetido", "hashB")]
    client = FakeQdrantClient(points, global_hashes={"hashB"})
    result = save_memory(client, "chat_A", ["p2"])
    assert result["promovidos"] == 0
    assert result["ja_existiam_no_global"] == 1
    assert len(client.upserted) == 0
    print("[ok] Conteúdo já existente no global_scope não é promovido de novo.")

    # Caso 3: ID que não existe no chat_scope é reportado, sem quebrar o resto
    points = [make_point("p3", "chat_A", "texto ok", "hashC")]
    client = FakeQdrantClient(points)
    result = save_memory(client, "chat_A", ["p3", "id_fantasma"])
    assert result["promovidos"] == 1
    assert result["nao_encontrados_no_chat_scope"] == ["id_fantasma"]
    print("[ok] ID inexistente é reportado sem quebrar a promoção dos outros.")

    # Caso 4: ponto existe mas é de outro chat_id -> ignorado, não promovido
    points = [make_point("p4", "chat_B", "texto de outro chat", "hashD")]
    client = FakeQdrantClient(points)
    result = save_memory(client, "chat_A", ["p4"])
    assert result["promovidos"] == 0
    assert result["chat_id_nao_bate"] == ["p4"]
    print("[ok] Ponto de outro chat_id é ignorado, não promovido por engano.")

    # Caso 5: dois IDs pedidos com o mesmo content_hash -> só o primeiro promove
    points = [
        make_point("p5a", "chat_A", "texto duplicado", "hashE"),
        make_point("p5b", "chat_A", "texto duplicado", "hashE"),
    ]
    client = FakeQdrantClient(points)
    result = save_memory(client, "chat_A", ["p5a", "p5b"])
    assert result["promovidos"] == 1
    assert result["ja_existiam_no_global"] == 1
    print("[ok] Duplicata de hash dentro do mesmo lote promove só uma vez.")

    # Caso 6: o vetor original é reaproveitado, sem reembedding
    custom_vector = [9.9, 8.8, 7.7]
    points = [
        make_point("p6", "chat_A", "texto com vetor customizado", "hashF", vector=custom_vector)
    ]
    client = FakeQdrantClient(points)
    save_memory(client, "chat_A", ["p6"])
    assert client.upserted[0].vector == custom_vector
    print("[ok] Vetor original do chat_scope é reaproveitado sem reembedding.")

    print("\nTodos os testes de /save passaram.")


if __name__ == "__main__":
    main()
