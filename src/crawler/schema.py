"""
Fase 06 - 6.2: Schema de payload para o crawl_scope.

Mesma ideia da Fase 05 (src/memory/schema.py): centraliza a construção do
payload e do ID do ponto, para o pipeline de indexação (6.3) e qualquer
outro consumidor futuro não duplicarem a mesma lógica (regra 2 do
projeto). Reaproveita o padrão de dedup por content_hash desde a Fase 02
(Decision 023) e os nomes de campo 'source'/'content_hash' já usados em
evidence.py (Fase 03) e ingest_document.py (Fase 02).

Diferença central para os outros dois escopos: aqui a identidade de
origem é 'crawl_id' (uma execução do crawler adaptativo, análogo ao
chat_id do chat_scope) e não chat_id nem memory_type.
"""

import uuid
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

COLLECTION = "crawl_scope"


def crawl_point_id(content_hash: str) -> str:
    """
    ID determinístico do ponto em crawl_scope, derivado do content_hash.

    Mesma convenção usada desde a Fase 02 (Decision 023) e reaproveitada
    no global_scope (Fase 05): o mesmo conteúdo sempre produz o mesmo
    UUID (uuid5, namespace fixo). Diferente do chat_scope (que namespacia
    por chat_id + hash, permitindo o mesmo texto em chats diferentes),
    aqui o dedup é GLOBAL dentro de crawl_scope — recrawlear a mesma
    página em execuções diferentes sobrescreve o ponto existente em vez
    de duplicar, cobrindo parte da "atualização incremental" do roadmap
    desta fase.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, content_hash))


def build_crawl_payload(
    *,
    text: str,
    content_hash: str,
    source: str,
    crawl_id: str,
    seed_url: str,
    query: str,
    depth: int,
    chunk_index: int = 0,
) -> dict:
    """
    Monta o payload padrão de um chunk em crawl_scope.

    - source: URL da página específica de onde o chunk veio (mesmo nome
      de campo usado em evidence.py/ingest_document.py).
    - crawl_id: identifica a execução do crawler que gerou este ponto
      (análogo a chat_id em chat_scope) — permite rastrear/filtrar por
      execução sem misturar com o dedup global por content_hash.
    - seed_url / query / depth: contexto de como o AdaptiveCrawler (6.1)
      chegou nessa página.
    """
    return {
        "text": text,
        "content_hash": content_hash,
        "source": source,
        "crawl_id": crawl_id,
        "seed_url": seed_url,
        "query": query,
        "depth": depth,
        "chunk_index": chunk_index,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
    }


def is_already_crawled(client: QdrantClient, content_hash: str) -> bool:
    """
    Verifica se um chunk com esse content_hash já existe em crawl_scope.

    Dedup GLOBAL (não escopado por crawl_id) — mesmo padrão de
    is_already_saved() em src/memory/schema.py (Fase 05), aqui aplicado
    à collection crawl_scope.
    """
    result, _ = client.scroll(
        collection_name=COLLECTION,
        scroll_filter=Filter(
            must=[FieldCondition(key="content_hash", match=MatchValue(value=content_hash))]
        ),
        limit=1,
    )
    return len(result) > 0
