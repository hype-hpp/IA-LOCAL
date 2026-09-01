"""
Fase 02 - 2.5c: Hybrid search.

Fluxo:
  1. Busca dense no Qdrant (embedding da query vs vetores indexados)
  2. Busca sparse via BM25 em memória
  3. Funde as duas listas rankeadas com RRF
  4. Retorna top_k com texto e fonte, prontos para uso
"""

import os
import sys

from qdrant_client import QdrantClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from embedding_client import embed_text

from bm25_index import build_bm25_index, search_bm25
from fusion import reciprocal_rank_fusion

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION = "global_scope"


def hybrid_search(
    query: str,
    top_k: int = 10,
    dense_k: int = 20,
    sparse_k: int = 20,
) -> list[dict]:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # 1. Dense
    query_vector = embed_text(query)
    dense_points = client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=dense_k,
        with_payload=True,
    ).points
    dense_ids = [str(p.id) for p in dense_points]
    payload_lookup = {str(p.id): p.payload for p in dense_points}

    # 2. Sparse
    bm25_idx = build_bm25_index(client, collection=COLLECTION)
    sparse_results = search_bm25(bm25_idx, query, top_k=sparse_k)
    sparse_ids = [doc_id for doc_id, _ in sparse_results]

    # Preenche payload_lookup para ids que só vieram do BM25
    id_to_index = {doc_id: i for i, doc_id in enumerate(bm25_idx.ids)}
    for doc_id in sparse_ids:
        if doc_id not in payload_lookup:
            i = id_to_index[doc_id]
            payload_lookup[doc_id] = {
                "text": bm25_idx.texts[i],
                "source": bm25_idx.sources[i],
            }

    # 3. Fusão
    fused = reciprocal_rank_fusion(dense_ids, sparse_ids)

    # 4. Monta resultado final
    results = []
    for doc_id, score in fused[:top_k]:
        payload = payload_lookup.get(doc_id, {})
        results.append(
            {
                "id": doc_id,
                "score": round(score, 4),
                "source": payload.get("source"),
                "text": payload.get("text"),
            }
        )

    return results
