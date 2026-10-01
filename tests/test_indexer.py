"""
Fase 06 - 6.3: Teste do indexador (index_crawl_state) com Qdrant fake e
embed_texts fake via monkeypatch — sem rede, sem Qdrant/Ollama reais.
Mesmo padrão de monkeypatch já usado em tests/test_add_note.py (Fase 05).
Fase 06 - 6.5: FakeQdrantClient ganhou count()/delete() porque
index_crawl_state() agora chama enforce_storage_limit() (retention.py) ao
final de toda indexação.
"""

import os
import sys
from dataclasses import dataclass, field
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "crawler"))
import indexer as indexer_module
from indexer import index_crawl_state, content_hash


@dataclass
class FakePoint:
    id: str
    payload: dict


@dataclass
class FakePage:
    url: str
    markdown: str


@dataclass
class FakeCrawlState:
    knowledge_base: list
    metrics: dict = field(default_factory=dict)


def _match_value(filter_obj, key):
    for cond in filter_obj.must:
        if cond.key == key:
            return cond.match.value
    return None


class FakeQdrantClient:
    """Reimplementa scroll (dedup por content_hash E full-scan pra
    retention), count e delete (por crawl_id) e upsert — o suficiente pro
    indexer.py + retention.py, sem depender de um Qdrant real. Com poucos
    crawl_ids (como nestes testes) e DEFAULT_MAX_CRAWL_IDS=50, a retenção
    nunca chega a remover nada aqui — isso é coberto à parte em
    test_retention.py."""

    def __init__(self, existing_hashes=None):
        self._hashes = set(existing_hashes or [])
        self.upserted = []

    def scroll(self, collection_name, scroll_filter=None, limit=1, offset=None, **kwargs):
        if scroll_filter is not None:
            # Lookup de dedup por content_hash (is_already_crawled)
            chash = _match_value(scroll_filter, "content_hash")
            found = chash in self._hashes
            return ([FakePoint(id="x", payload={})] if found else []), None

        # Full-scan paginado (retention._earliest_crawled_at_per_crawl_id)
        start = offset or 0
        batch = self.upserted[start : start + limit]
        next_offset = start + limit if start + limit < len(self.upserted) else None
        return batch, next_offset

    def count(self, collection_name, count_filter):
        crawl_id = _match_value(count_filter, "crawl_id")
        n = sum(1 for p in self.upserted if p.payload.get("crawl_id") == crawl_id)
        return SimpleNamespace(count=n)

    def delete(self, collection_name, points_selector):
        crawl_id = _match_value(points_selector.filter, "crawl_id")
        self.upserted = [p for p in self.upserted if p.payload.get("crawl_id") != crawl_id]

    def upsert(self, collection_name, points):
        self.upserted.extend(points)
        for p in points:
            self._hashes.add(p.payload["content_hash"])


def main():
    original_embed_texts = indexer_module.embed_texts

    try:
        # Caso 1: página nova é chunkada, embedada e inserida em crawl_scope
        indexer_module.embed_texts = lambda texts: [[0.1, 0.2, 0.3] for _ in texts]

        state = FakeCrawlState(
            knowledge_base=[FakePage(url="https://exemplo.com/pagina-1", markdown="conteúdo de teste " * 20)],
            metrics={"depth_reached": 2},
        )
        client = FakeQdrantClient()
        result = index_crawl_state(
            state, crawl_id="crawl_1", seed_url="https://exemplo.com/", query="teste", client=client
        )

        assert result["pages"] == 1, result
        assert result["chunks_novos"] == 1, result
        assert result["chunks_pulados"] == 0, result
        assert len(client.upserted) == 1
        saved = client.upserted[0]
        assert saved.payload["crawl_id"] == "crawl_1"
        assert saved.payload["seed_url"] == "https://exemplo.com/"
        assert saved.payload["source"] == "https://exemplo.com/pagina-1"
        assert saved.payload["depth"] == 2, "depth deveria ser o depth_reached da execução"
        assert saved.vector == [0.1, 0.2, 0.3]
        print("[ok] Página nova é chunkada, embedada e inserida com o payload certo.")

        # Caso 2: chunk com texto idêntico a um já existente não é reinserido
        # nem gasta chamada de embedding (dedup global por content_hash)
        embed_calls = {"n": 0}

        def counting_embed(texts):
            embed_calls["n"] += 1
            return [[0.9, 0.9, 0.9] for _ in texts]

        indexer_module.embed_texts = counting_embed
        texto_repetido = "conteúdo já indexado antes " * 20
        # content_hash precisa ser calculado sobre o texto já normalizado
        # por chunk_text() (join com espaço único), não sobre a string
        # crua — chunk_text reformata espaçamento ao juntar as palavras.
        from chunking import chunk_text as _chunk_text_for_test
        chash = content_hash(_chunk_text_for_test(texto_repetido)[0])
        client2 = FakeQdrantClient(existing_hashes={chash})
        state2 = FakeCrawlState(
            knowledge_base=[FakePage(url="https://exemplo.com/pagina-2", markdown=texto_repetido)],
            metrics={"depth_reached": 1},
        )
        result2 = index_crawl_state(
            state2, crawl_id="crawl_2", seed_url="https://exemplo.com/", query="teste", client=client2
        )
        assert result2["chunks_novos"] == 0, result2
        assert result2["chunks_pulados"] == 1, result2
        assert embed_calls["n"] == 0, "não deveria chamar embed_texts se não há chunk novo"
        assert len(client2.upserted) == 0
        print("[ok] Chunk já existente (mesmo content_hash) não é reinserido, sem gastar embedding.")

        # Caso 3: página sem texto (markdown vazio) é ignorada, sem erro
        indexer_module.embed_texts = lambda texts: [[0.0, 0.0, 0.0] for _ in texts]
        state3 = FakeCrawlState(
            knowledge_base=[FakePage(url="https://exemplo.com/vazia", markdown="   ")],
            metrics={"depth_reached": 0},
        )
        client3 = FakeQdrantClient()
        result3 = index_crawl_state(
            state3, crawl_id="crawl_3", seed_url="https://exemplo.com/", query="teste", client=client3
        )
        assert result3["chunks_novos"] == 0
        assert result3["chunks_pulados"] == 0
        assert len(client3.upserted) == 0
        print("[ok] Página com markdown vazio é ignorada, sem erro.")

        print("\nTodos os testes do indexador do crawl_scope passaram.")

    finally:
        indexer_module.embed_texts = original_embed_texts


if __name__ == "__main__":
    main()
