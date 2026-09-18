"""
Fase 05 - 5.4: CLI para apagar memórias de global_scope, por ID explícito.

Uso:
    python scripts/delete_memory.py --ids id1,id2
    python scripts/delete_memory.py --ids id1,id2 --yes   # sem pedir confirmação

Decisão de hp: apagar é só por ID explícito (sem filtro em massa por
memory_type/tag/chat_id) — cada apagamento é uma escolha deliberada.
Confirmação interativa por padrão (como um "rm -i"), pulável com --yes
para uso em script/automação.
"""

import os
import sys
import argparse

from qdrant_client import QdrantClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from manage import delete_memories, GLOBAL_COLLECTION

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


def parse_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description="Apaga memórias de global_scope por ID")
    parser.add_argument("--ids", required=True, help="IDs a apagar, separados por vírgula")
    parser.add_argument("--yes", action="store_true", help="Não pedir confirmação antes de apagar")
    args = parser.parse_args()

    ids = parse_list(args.ids)
    if not ids:
        print("Nenhum ID válido informado em --ids. Nada a fazer.")
        return

    if not args.yes:
        resposta = input(f"Confirma apagar {len(ids)} memória(s) de '{GLOBAL_COLLECTION}'? [s/N] ")
        if resposta.strip().lower() != "s":
            print("Cancelado.")
            return

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    result = delete_memories(client, ids)

    print(f"Solicitados: {result['solicitados']}")
    print(f"Apagados: {result['apagados']}")
    if result["nao_encontrados"]:
        print(f"[aviso] IDs não encontrados (nada a apagar): {result['nao_encontrados']}")

    total = client.get_collection(GLOBAL_COLLECTION).points_count
    print(f"Total de pontos em '{GLOBAL_COLLECTION}' agora: {total}")


if __name__ == "__main__":
    main()
