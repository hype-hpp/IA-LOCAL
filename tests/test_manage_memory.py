"""
Fase 05 - 5.4: Teste de list/get/editar/apagar memórias, com um Qdrant fake
em memória (retrieve, scroll com filtro genérico, upsert, delete,
set_payload) e embed_text fake via monkeypatch. Sem rede, sem
Qdrant/Ollama reais.
"""

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
import manage as manage_module
from manage import (
    list_memories,
    get_memory,
    update_tags,
    update_text,
    delete_memories,
)
from schema import memory_point_id
from add_note import content_hash


@dataclass
class FakePoint:
    id: str
    payload: dict = field(default_factory=dict)
    vector: list = field(default_factory=list)


class FakeQdrantClient:
    """
    Store em memória suficiente pra exercitar list/get/edit/delete de
    ponta a ponta: retrieve, scroll (com filtro genérico por igualdade ou
    'contém' em campo array), upsert, delete e set_payload.
    """

    def __init__(self, points=None):
        self._store = {p.id: p for p in (points or [])}

    def retrieve(self, collection_name, ids, with_payload=True, with_vectors=False):
        return [self._store[i] for i in ids if i in self._store]

    def scroll(self, collection_name, scroll_filter=None, limit=20, offset=None, with_payload=True, **kwargs):
        points = list(self._store.values())

        if scroll_filter is not None:
            def matches(p):
                for cond in scroll_filter.must:
                    val = cond.match.value
                    payload_val = p.payload.get(cond.key)
                    if isinstance(payload_val, list):
                        if val not in payload_val:
                            return False
                    elif payload_val != val:
                        return False
                return True

            points = [p for p in points if matches(p)]

        return points[:limit], None

    def upsert(self, collection_name, points):
        for p in points:
            self._store[p.id] = FakePoint(id=p.id, payload=dict(p.payload), vector=p.vector)

    def delete(self, collection_name, points_selector):
        for i in points_selector:
            self._store.pop(i, None)

    def set_payload(self, collection_name, payload, points):
        for i in points:
            if i in self._store:
                self._store[i].payload.update(payload)


def make_point(id_, memory_type, text, tags=None, **extra_payload):
    payload = {
        "memory_type": memory_type,
        "text": text,
        "content_hash": content_hash(text),
        "source": "fonte_teste",
        "tags": tags or [],
        "saved_at": "2026-01-01T00:00:00+00:00",
    }
    payload.update(extra_payload)
    return FakePoint(id=id_, payload=payload, vector=[0.1, 0.2])


def main():
    original_embed_text = manage_module.embed_text

    try:
        # --- list_memories ---
        p1 = make_point("id1", "manual", "primeira nota", tags=["a"])
        p2 = make_point("id2", "research", "evidência qualquer", tags=["b"], origin_chat_id="chat_X")
        p3 = make_point("id3", "manual", "segunda nota", tags=["a", "b"])
        client = FakeQdrantClient([p1, p2, p3])

        records, _ = list_memories(client)
        assert len(records) == 3
        print("[ok] list_memories sem filtro retorna todas as memórias.")

        records, _ = list_memories(client, memory_type="manual")
        assert {r["id"] for r in records} == {"id1", "id3"}
        print("[ok] list_memories filtra corretamente por memory_type.")

        records, _ = list_memories(client, tag="b")
        assert {r["id"] for r in records} == {"id2", "id3"}
        print("[ok] list_memories filtra corretamente por tag (campo array).")

        records, _ = list_memories(client, origin_chat_id="chat_X")
        assert {r["id"] for r in records} == {"id2"}
        print("[ok] list_memories filtra corretamente por origin_chat_id.")

        # --- get_memory ---
        assert get_memory(client, "id1")["text"] == "primeira nota"
        assert get_memory(client, "id_fantasma") is None
        print("[ok] get_memory retorna payload completo ou None se não existir.")

        # --- update_tags ---
        result = update_tags(client, "id1", ["novo_a", "novo_b"])
        assert result["editado"] is True
        assert client._store["id1"].payload["tags"] == ["novo_a", "novo_b"]
        assert client._store["id1"].payload["text"] == "primeira nota"  # texto intocado
        print("[ok] update_tags troca as tags sem mexer no texto nem no ID.")

        result = update_tags(client, "id_fantasma", ["x"])
        assert result["editado"] is False
        print("[ok] update_tags em ID inexistente reporta erro sem quebrar.")

        # --- update_text ---
        manage_module.embed_text = lambda text: [9.9, 9.9]
        result = update_text(client, "id3", "segunda nota editada")
        assert result["editado"] is True
        new_id = result["novo_id"]
        assert new_id != "id3"
        assert "id3" not in client._store, "ID antigo deveria ter sido apagado"
        assert client._store[new_id].payload["text"] == "segunda nota editada"
        assert client._store[new_id].payload["tags"] == ["a", "b"], "tags devem ser preservadas por padrão"
        assert client._store[new_id].payload["memory_type"] == "manual"
        assert client._store[new_id].vector == [9.9, 9.9]
        print("[ok] update_text gera novo ID, preserva memory_type/tags, usa vetor novo.")

        # --- update_text com override_tags ---
        p4 = make_point("id4", "manual", "quarta nota", tags=["velha"])
        client2 = FakeQdrantClient([p4])
        manage_module.embed_text = lambda text: [1.0, 1.0]
        result = update_text(client2, "id4", "quarta nota editada", override_tags=["nova"])
        assert result["editado"] is True
        assert client2._store[result["novo_id"]].payload["tags"] == ["nova"]
        print("[ok] update_text aplica override_tags quando informado.")

        # --- update_text: texto idêntico não faz nada ---
        p5 = make_point("id5", "manual", "texto igual")
        client3 = FakeQdrantClient([p5])
        result = update_text(client3, "id5", "texto igual")
        assert result["editado"] is False
        assert result["novo_id"] == "id5"
        assert "id5" in client3._store
        print("[ok] update_text com texto idêntico ao atual não faz nada.")

        # --- update_text: conflito com memória já existente ---
        chash_alvo = content_hash("texto que já existe em outro lugar")
        id_existente = memory_point_id(chash_alvo)
        p6 = make_point("id6", "manual", "texto original")
        p_conflito = make_point(id_existente, "manual", "texto que já existe em outro lugar")
        client4 = FakeQdrantClient([p6, p_conflito])
        manage_module.embed_text = lambda text: [0.0, 0.0]
        result = update_text(client4, "id6", "texto que já existe em outro lugar")
        assert result["editado"] is False
        assert "id6" in client4._store, "ponto original não deveria ser tocado em caso de conflito"
        print("[ok] update_text recusa edição que colidiria com memória já existente.")

        # --- delete_memories ---
        p7 = make_point("id7", "manual", "para apagar")
        p8 = make_point("id8", "manual", "para manter")
        client5 = FakeQdrantClient([p7, p8])
        result = delete_memories(client5, ["id7", "id_fantasma"])
        assert result["apagados"] == 1
        assert result["nao_encontrados"] == ["id_fantasma"]
        assert "id7" not in client5._store
        assert "id8" in client5._store
        print("[ok] delete_memories apaga só os IDs existentes e reporta os que não existem.")

        print("\nTodos os testes de list/edit/delete de memórias passaram.")

    finally:
        manage_module.embed_text = original_embed_text


if __name__ == "__main__":
    main()
