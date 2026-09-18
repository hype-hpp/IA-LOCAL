"""
Fase 05 - 5.3: Teste da nota manual (add_note) com Qdrant fake e embed_text
fake via monkeypatch — sem rede, sem Qdrant/Ollama reais. Mesmo padrão de
monkeypatch já usado em tests/test_agent_loop.py (Fase 04).
"""

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
import add_note as add_note_module
from add_note import add_note, content_hash


@dataclass
class FakePoint:
    id: str
    payload: dict


class FakeQdrantClient:
    """Reimplementa só scroll (dedup por content_hash) e upsert."""

    def __init__(self, global_hashes=None):
        self._global_hashes = set(global_hashes or [])
        self.upserted = []

    def scroll(self, collection_name, scroll_filter, limit=1, **kwargs):
        chash = None
        for cond in scroll_filter.must:
            if cond.key == "content_hash":
                chash = cond.match.value
        found = chash in self._global_hashes
        return ([FakePoint(id="x", payload={})] if found else []), None

    def upsert(self, collection_name, points):
        self.upserted.extend(points)
        for p in points:
            self._global_hashes.add(p.payload["content_hash"])


def main():
    original_embed_text = add_note_module.embed_text

    try:
        # Caso 1: nota nova é salva, com vetor vindo do embed_text (fake)
        add_note_module.embed_text = lambda text: [0.1, 0.2, 0.3]
        client = FakeQdrantClient()
        result = add_note(client, "Lembrar de revisar o índice memory_type depois", tags=["projeto"])
        assert result["salvo"] is True, result
        assert len(client.upserted) == 1
        saved = client.upserted[0]
        assert saved.payload["memory_type"] == "manual"
        assert saved.payload["source"] == "manual"
        assert saved.payload["tags"] == ["projeto"]
        assert saved.vector == [0.1, 0.2, 0.3]
        print("[ok] Nota nova salva com memory_type=manual, source=manual, vetor do embed_text.")

        # Caso 2: nota com texto idêntico a uma já existente -> não salva de novo, não chama embed_text
        embed_calls = {"n": 0}

        def counting_embed(text):
            embed_calls["n"] += 1
            return [0.9, 0.9, 0.9]

        add_note_module.embed_text = counting_embed
        texto = "Texto que já existe em global_scope"
        chash = content_hash(texto)
        client2 = FakeQdrantClient(global_hashes={chash})
        result = add_note(client2, texto)
        assert result["salvo"] is False, result
        assert embed_calls["n"] == 0, "não deveria chamar embed_text se já existe (evita custo à toa)"
        assert len(client2.upserted) == 0
        print("[ok] Nota duplicada não é salva de novo e não gasta chamada de embedding.")

        # Caso 3: texto vazio (ou só espaços) levanta erro, não salva memória vazia
        add_note_module.embed_text = lambda text: [0.0, 0.0, 0.0]
        client3 = FakeQdrantClient()
        try:
            add_note(client3, "    ")
            assert False, "deveria ter levantado ValueError para texto vazio"
        except ValueError:
            print("[ok] Texto vazio levanta ValueError em vez de salvar memória vazia.")

        print("\nTodos os testes da nota manual passaram.")

    finally:
        add_note_module.embed_text = original_embed_text


if __name__ == "__main__":
    main()
