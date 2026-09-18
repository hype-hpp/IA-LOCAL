"""
Fase 05 - 5.3: CLI da nota manual avulsa (memory_type="manual").

Uso:
    python scripts/add_memory.py --text "texto da nota" [--tags tag1,tag2]
"""

import os
import sys
import argparse

from qdrant_client import QdrantClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from add_note import add_note, GLOBAL_COLLECTION

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


def parse_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description="Adiciona uma nota manual em global_scope")
    parser.add_argument("--text", required=True, help="Texto da nota a memorizar")
    parser.add_argument("--tags", default=None, help="Tags a aplicar, separadas por vírgula")
    args = parser.parse_args()

    tags = parse_list(args.tags)

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    result = add_note(client, args.text, tags=tags)

    if result["salvo"]:
        print(f"[ok] Nota salva em '{GLOBAL_COLLECTION}' (id={result['id']}).")
    else:
        print(f"[skip] Nota não salva: {result['motivo']} (content_hash={result['content_hash']}).")

    total = client.get_collection(GLOBAL_COLLECTION).points_count
    print(f"Total de pontos em '{GLOBAL_COLLECTION}' agora: {total}")


if __name__ == "__main__":
    main()
