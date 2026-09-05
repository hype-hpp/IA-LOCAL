"""
Fase 05 - 5.1: Teste do schema de memória. Lógica pura, sem rede, sem Qdrant.
Roda rápido e não deveria quebrar nunca sozinho.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from schema import memory_point_id, build_memory_payload, MEMORY_TYPES


def main():
    # Caso 1: mesmo content_hash -> sempre o mesmo ID
    id_a = memory_point_id("hash123")
    id_b = memory_point_id("hash123")
    assert id_a == id_b, "mesmo content_hash deveria gerar o mesmo ID"
    print("[ok] ID determinístico para o mesmo content_hash.")

    # Caso 2: content_hash diferente -> ID diferente
    id_c = memory_point_id("hash456")
    assert id_a != id_c, "content_hash diferentes deveriam gerar IDs diferentes"
    print("[ok] IDs diferentes para content_hash diferentes.")

    # Caso 3: payload básico para cada tipo válido de memória
    for mtype in MEMORY_TYPES:
        payload = build_memory_payload(
            text="texto de teste",
            content_hash="hashXYZ",
            memory_type=mtype,
            source="fonte_teste",
        )
        assert payload["memory_type"] == mtype
        assert payload["tags"] == []
        assert "saved_at" in payload
        assert "origin_chat_id" not in payload
    print("[ok] Payload básico correto para os três tipos de memória.")

    # Caso 4: memory_type inválido levanta erro, não falha silenciosamente
    try:
        build_memory_payload(
            text="x", content_hash="h", memory_type="invalido", source="s"
        )
        assert False, "deveria ter levantado ValueError"
    except ValueError:
        print("[ok] memory_type inválido levanta ValueError.")

    # Caso 5: origin_chat_id só aparece no payload quando fornecido
    payload_sem = build_memory_payload(
        text="x", content_hash="h", memory_type="knowledge", source="s"
    )
    assert "origin_chat_id" not in payload_sem
    payload_com = build_memory_payload(
        text="x", content_hash="h", memory_type="research", source="s",
        origin_chat_id="chat_abc",
    )
    assert payload_com["origin_chat_id"] == "chat_abc"
    print("[ok] origin_chat_id incluído só quando fornecido.")

    # Caso 6: tags e extra são aplicados corretamente
    payload = build_memory_payload(
        text="x", content_hash="h", memory_type="knowledge", source="s",
        tags=["projeto", "importante"],
        extra={"chunk_index": 3},
    )
    assert payload["tags"] == ["projeto", "importante"]
    assert payload["chunk_index"] == 3
    print("[ok] tags e extra aplicados corretamente.")

    print("\nTodos os testes do schema de memória passaram.")


if __name__ == "__main__":
    main()
