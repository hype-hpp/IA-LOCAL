"""
Fase 05 - 5.4: CLI para editar uma memória existente em global_scope.

Uso:
    # Só trocar as tags (mantém o mesmo ID)
    python scripts/edit_memory.py --id <memory_id> --tags tag1,tag2

    # Trocar o texto (GERA UM ID NOVO — o antigo deixa de existir)
    python scripts/edit_memory.py --id <memory_id> --text "novo texto da memória"

    # Trocar texto E tags de uma vez (também gera ID novo)
    python scripts/edit_memory.py --id <memory_id> --text "novo texto" --tags tag1,tag2

ATENÇÃO: como o ID é derivado do hash do conteúdo, editar --text sempre
troca o ID da memória. Anote o "novo_id" impresso no final se for
referenciar essa memória de novo depois.
"""

import os
import sys
import argparse

from qdrant_client import QdrantClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from manage import update_tags, update_text, GLOBAL_COLLECTION

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))


def parse_list(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def main():
    parser = argparse.ArgumentParser(description="Edita tags e/ou texto de uma memória em global_scope")
    parser.add_argument("--id", required=True, help="ID da memória a editar")
    parser.add_argument("--text", default=None, help="Novo texto (gera um ID novo)")
    parser.add_argument("--tags", default=None, help="Novas tags, separadas por vírgula (substitui as atuais)")
    args = parser.parse_args()

    if args.text is None and args.tags is None:
        print("Nada para editar: informe --text e/ou --tags.")
        return

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    tags = parse_list(args.tags)

    if args.text is not None:
        result = update_text(client, args.id, args.text, override_tags=tags)
        if result["editado"]:
            print(f"[ok] Texto atualizado. Novo ID: {result['novo_id']} (o ID antigo '{args.id}' não existe mais).")
        else:
            print(f"[skip] Não editado: {result['motivo']}")
    else:
        result = update_tags(client, args.id, tags)
        if result["editado"]:
            print(f"[ok] Tags atualizadas para {tags} (ID '{args.id}' inalterado).")
        else:
            print(f"[skip] Não editado: {result['motivo']}")

    total = client.get_collection(GLOBAL_COLLECTION).points_count
    print(f"Total de pontos em '{GLOBAL_COLLECTION}' agora: {total}")


if __name__ == "__main__":
    main()
