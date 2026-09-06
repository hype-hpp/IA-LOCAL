"""
Fase 05 - 5.2: CLI do mecanismo /save.

Uso:
    python scripts/save_memory.py --chat-id <chat_id> --ids <id1,id2,...> [--tags tag1,tag2]

Como descobrir os IDs de um chat_id agora: pelo dashboard do Qdrant
(http://localhost:6333/dashboard), filtrando a collection chat_scope por
payload.chat_id. Uma forma mais direta de buscar isso fica para quando
houver UI (Fase 08) ou uma necessidade real antes disso (regra 1 do projeto).
"""

import os
import sys
import argparse

from qdrant_client import QdrantClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from save import save_memory, GLOBAL_COLLECTION

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


def parse_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Promove pontos do chat_scope para o global_scope (/save)"
    )
    parser.add_argument("--chat-id", required=True, help="chat_id de origem dos pontos")
    parser.add_argument(
        "--ids", required=True, help="IDs dos pontos a promover, separados por vírgula"
    )
    parser.add_argument(
        "--tags", default=None, help="Tags a aplicar na memória promovida, separadas por vírgula"
    )
    args = parser.parse_args()

    ids = parse_list(args.ids)
    tags = parse_list(args.tags)

    if not ids:
        print("Nenhum ID válido informado em --ids. Nada a fazer.")
        return

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    print(f"Promovendo {len(ids)} ponto(s) do chat '{args.chat_id}' para '{GLOBAL_COLLECTION}'...")
    result = save_memory(client, args.chat_id, ids, tags)

    print(f"\nSolicitados: {result['solicitados']}")
    print(f"Promovidos: {result['promovidos']}")
    print(f"Já existiam no global_scope (pulados): {result['ja_existiam_no_global']}")
    if result["nao_encontrados_no_chat_scope"]:
        print(f"[aviso] IDs não encontrados no chat_scope: {result['nao_encontrados_no_chat_scope']}")
    if result["chat_id_nao_bate"]:
        print(f"[aviso] IDs encontrados mas de outro chat_id (ignorados): {result['chat_id_nao_bate']}")
    if result["sem_content_hash"]:
        print(f"[aviso] IDs sem content_hash no payload (ignorados): {result['sem_content_hash']}")

    total = client.get_collection(GLOBAL_COLLECTION).points_count
    print(f"\nTotal de pontos em '{GLOBAL_COLLECTION}' agora: {total}")


if __name__ == "__main__":
    main()
