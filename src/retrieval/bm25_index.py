"""
Fase 02 - 2.5b: Índice BM25 (sparse/lexical) em memória.

Decisão: BM25 em memória via rank_bm25, reconstruído a cada busca por
enquanto (dataset pessoal, custo de reconstrução é baixo). Se o corpus
crescer a ponto de isso pesar, medir antes de trocar por algo mais
complexo (sparse vectors nativos do Qdrant) — regra 5 do projeto.
"""

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
from qdrant_client import QdrantClient

SCROLL_BATCH_SIZE = 256


def tokenize(text: str) -> list[str]:
    """Tokenização simples: minúsculas + apenas sequências alfanuméricas."""
    return re.findall(r"\w+", text.lower())


@dataclass
class BM25Index:
    bm25: BM25Okapi
    ids: list[str]
    texts: list[str]
    sources: list[str]


def build_bm25_index(client: QdrantClient, collection: str = "global_scope") -> BM25Index:
    """Varre toda a collection e monta um índice BM25 em memória."""
    ids, texts, sources = [], [], []
    offset = None

    while True:
        points, offset = client.scroll(
            collection_name=collection,
            limit=SCROLL_BATCH_SIZE,
            offset=offset,
            with_payload=True,
        )
        for point in points:
            ids.append(str(point.id))
            texts.append(point.payload.get("text", ""))
            sources.append(point.payload.get("source", ""))
        if offset is None:
            break

    tokenized_corpus = [tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

    return BM25Index(bm25=bm25, ids=ids, texts=texts, sources=sources)


def search_bm25(index: BM25Index, query: str, top_k: int = 20) -> list[tuple[str, float]]:
    """Retorna [(point_id, score_bm25), ...] ordenado por relevância."""
    if index.bm25 is None:
        return []

    scores = index.bm25.get_scores(tokenize(query))
    ranked = sorted(zip(index.ids, scores), key=lambda pair: pair[1], reverse=True)
    return ranked[:top_k]
