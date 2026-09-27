"""
Fase 06 - 6.2: Teste do schema de payload do crawl_scope, com um Qdrant
fake em memória. Sem rede, sem Qdrant real — mesmo padrão de fakes já
usado em tests/test_save_memory.py (Fase 05).
"""

import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "crawler"))
from schema import crawl_point_id, build_crawl_payload, is_already_crawled


@dataclass
class FakePoint:
    id: str
    payload: dict


class FakeQdrantClient:
    """Reimplementa só o pedacinho da API do QdrantClient que
    is_already_crawled() realmente usa: scroll filtrado por content_hash."""

    def __init__(self, existing_hashes=None):
        self._hashes = set(existing_hashes or [])

    def scroll(self, collection_name, scroll_filter, limit=1, **kwargs):
        chash = None
        for cond in scroll_filter.must:
            if cond.key == "content_hash":
                chash = cond.match.value
        found = chash in self._hashes
        fake_hit = [FakePoint(id="x", payload={})] if found else []
        return fake_hit, None


def main():
    # Caso 1: mesmo content_hash sempre gera o mesmo ID (determinístico)
    id_a = crawl_point_id("abc123")
    id_b = crawl_point_id("abc123")
    id_c = crawl_point_id("outro_hash")
    assert id_a == id_b, "mesmo content_hash deveria gerar o mesmo ID"
    assert id_a != id_c, "content_hash diferente deveria gerar ID diferente"
    print("[ok] crawl_point_id é determinístico por content_hash.")

    # Caso 2: build_crawl_payload monta os campos esperados
    payload = build_crawl_payload(
        text="conteúdo de teste",
        content_hash="abc123",
        source="https://exemplo.com/pagina",
        crawl_id="crawl_teste_1",
        seed_url="https://exemplo.com/",
        query="documentação de teste",
        depth=1,
        chunk_index=0,
    )
    esperado = {"text", "content_hash", "source", "crawl_id", "seed_url", "query", "depth", "chunk_index", "crawled_at"}
    assert set(payload.keys()) == esperado, f"campos inesperados no payload: {set(payload.keys())}"
    assert payload["source"] == "https://exemplo.com/pagina"
    assert payload["crawl_id"] == "crawl_teste_1"
    assert payload["crawled_at"], "crawled_at não deveria vir vazio"
    print("[ok] build_crawl_payload monta os campos esperados.")

    # Caso 3: is_already_crawled encontra hash existente
    client = FakeQdrantClient(existing_hashes=["ja_existe"])
    assert is_already_crawled(client, "ja_existe") is True
    print("[ok] is_already_crawled retorna True para hash já indexado.")

    # Caso 4: is_already_crawled não encontra hash novo
    assert is_already_crawled(client, "hash_novo") is False
    print("[ok] is_already_crawled retorna False para hash novo.")

    print("\nTodos os testes do schema do crawl_scope passaram.")


if __name__ == "__main__":
    main()
