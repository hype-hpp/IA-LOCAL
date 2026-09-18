"""
Fase 05 - 5.4: CLI para listar/ver memórias em global_scope.

Uso:
    # Listar com filtros (todos opcionais)
    python scripts/list_memories.py [--memory-type manual|research|knowledge] [--tag TAG] [--chat-id CHAT_ID] [--limit 20]

    # Ver o detalhe completo de UMA memória por ID (ignora os filtros acima)
    python scripts/list_memories.py --id <memory_id>
"""

import os
import sys
import argparse

from qdrant_client import QdrantClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from manage import list_memories, get_memory

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


def print_detail(payload: dict) -> None:
    print(f"memory_type : {payload.get('memory_type')}")
    print(f"source      : {payload.get('source')}")
    print(f"tags        : {payload.get('tags', [])}")
    print(f"saved_at    : {payload.get('saved_at')}")
    print(f"content_hash: {payload.get('content_hash')}")
    if payload.get("origin_chat_id"):
        print(f"origin_chat_id: {payload.get('origin_chat_id')}")
    if payload.get("title"):
        print(f"title       : {payload.get('title')}")
    if payload.get("query"):
        print(f"query       : {payload.get('query')}")
    if "chunk_index" in payload:
        print(f"chunk_index : {payload.get('chunk_index')}")
    print(f"\ntexto completo:\n{payload.get('text', '')}")


def main():
    parser = argparse.ArgumentParser(description="Lista ou vê memórias em global_scope")
    parser.add_argument("--id", default=None, help="Ver o detalhe completo de uma memória específica")
    parser.add_argument("--memory-type", default=None, choices=["knowledge", "research", "manual"])
    parser.add_argument("--tag", default=None, help="Filtra por uma tag")
    parser.add_argument("--chat-id", default=None, help="Filtra por origin_chat_id (só memórias tipo research)")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    if args.id:
        payload = get_memory(client, args.id)
        if payload is None:
            print(f"Memória '{args.id}' não encontrada em global_scope.")
            return
        print(f"id: {args.id}\n")
        print_detail(payload)
        return

    records, next_offset = list_memories(
        client,
        memory_type=args.memory_type,
        tag=args.tag,
        origin_chat_id=args.chat_id,
        limit=args.limit,
    )

    if not records:
        print("Nenhuma memória encontrada com esses filtros.")
        return

    for r in records:
        print(f"[{r['memory_type']}] {r['id']}")
        print(f"  source: {r['source']}  tags: {r['tags']}  saved_at: {r['saved_at']}")
        print(f"  {r['preview']}")
        print()

    print(f"{len(records)} memória(s) mostrada(s).")
    if next_offset is not None:
        print("(há mais resultados além do --limit atual; aumente --limit para ver mais)")


if __name__ == "__main__":
    main()
