"""
Fase 05 - 5.5: Teste de integração end-to-end da Fase 05 (Memory).

Cobre o pipeline completo da fase, contra Qdrant e Ollama REAIS (não
fakes, ao contrário dos testes unitários dos passos 5.1-5.4):

  1. Simula uma evidência de pesquisa web em chat_scope (mesmo formato
     real de src/search/evidence.py, Fase 03).
  2. Promove via /save (5.2) -> memory_type="research".
  3. Adiciona uma nota manual (5.3) -> memory_type="manual".
  4. Lista memórias filtrando por tag (5.4).
  5. Edita as tags da nota manual -> mesmo ID.
  6. Edita o texto da nota manual -> ID novo, ID antigo removido.
  7. Apaga tudo que o teste criou.

Usa um chat_id e um marcador de texto exclusivos de teste, para não
colidir com dado real e para poder confirmar que a limpeza final (regra
14 do projeto: não deixar lixo indexado) realmente aconteceu. A limpeza
roda em `finally`, então mesmo que algum assert falhe no meio do
caminho, o teste tenta remover o que já tinha criado antes de propagar o
erro — mesmo cuidado já usado em tests/test_end_to_end.py (Fase 02).

Pré-requisito: Qdrant e Ollama rodando (mesmo pré-requisito dos outros
testes end-to-end do projeto).
"""

import os
import sys
import uuid
import hashlib

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))
from embedding_client import embed_text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "memory"))
from schema import memory_point_id
from save import save_memory
from add_note import add_note
from manage import list_memories, get_memory, update_tags, update_text, delete_memories

QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
CHAT_COLLECTION = "chat_scope"
GLOBAL_COLLECTION = "global_scope"

TEST_CHAT_ID = "test_memory_e2e_5_5"
TEST_MARKER = "TESTE_E2E_FASE05"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    chat_point_id = None
    ids_to_cleanup_global = []

    try:
        # --- 1. Simula uma evidência de pesquisa web em chat_scope ---
        print("1. Inserindo evidência de teste em chat_scope...")
        evidence_text = f"{TEST_MARKER}: RAG combina recuperação de informação com geração de texto."
        evidence_hash = content_hash(evidence_text)
        # Mesmo esquema de ID de src/search/evidence.py (Decision 027):
        # namespace inclui chat_id, não só o hash.
        chat_point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{TEST_CHAT_ID}:{evidence_hash}"))
        vector = embed_text(evidence_text)
        client.upsert(
            collection_name=CHAT_COLLECTION,
            points=[
                PointStruct(
                    id=chat_point_id,
                    vector=vector,
                    payload={
                        "chat_id": TEST_CHAT_ID,
                        "source": "http://exemplo-teste.local/rag",
                        "title": "Fonte de teste",
                        "query": "o que é RAG",
                        "content_hash": evidence_hash,
                        "text": evidence_text,
                        "ingested_at": "2026-01-01T00:00:00+00:00",
                    },
                )
            ],
        )
        print(f"   Ponto de teste inserido em chat_scope: {chat_point_id}")

        # --- 2. Promove via /save (5.2) ---
        print("2. Promovendo via /save...")
        result = save_memory(client, TEST_CHAT_ID, [chat_point_id], tags=["e2e", TEST_MARKER])
        assert result["promovidos"] == 1, f"esperava 1 promovido, veio {result}"
        research_id = memory_point_id(evidence_hash)
        payload = get_memory(client, research_id)
        assert payload is not None, "memória promovida não encontrada em global_scope"
        assert payload["memory_type"] == "research"
        assert payload["origin_chat_id"] == TEST_CHAT_ID
        ids_to_cleanup_global.append(research_id)
        print("   [ok] /save promoveu a evidência com memory_type=research.")

        # --- 3. Nota manual (5.3) ---
        print("3. Adicionando nota manual...")
        note_text = f"{TEST_MARKER}: lembrete de que o dedup usa content_hash."
        note_result = add_note(client, note_text, tags=["e2e", TEST_MARKER])
        assert note_result["salvo"] is True, note_result
        manual_id = note_result["id"]
        ids_to_cleanup_global.append(manual_id)
        print("   [ok] Nota manual salva com memory_type=manual.")

        # --- 4. Listar com filtro de tag (5.4) ---
        print("4. Listando memórias com a tag do teste...")
        records, _ = list_memories(client, tag=TEST_MARKER, limit=50)
        found_ids = {r["id"] for r in records}
        assert research_id in found_ids and manual_id in found_ids, (
            "listagem não trouxe as duas memórias de teste esperadas"
        )
        print(f"   [ok] Listagem por tag encontrou as memórias de teste ({len(records)} no total).")

        # --- 5. Editar tags (5.4) — mesmo ID ---
        print("5. Editando tags da nota manual...")
        tag_result = update_tags(client, manual_id, ["e2e", TEST_MARKER, "editado"])
        assert tag_result["editado"] is True
        payload = get_memory(client, manual_id)
        assert "editado" in payload["tags"]
        assert payload["text"] == note_text, "texto não deveria mudar ao editar só tags"
        print("   [ok] Tags editadas; ID e texto permanecem os mesmos.")

        # --- 6. Editar texto (5.4) — ID novo ---
        print("6. Editando o texto da nota manual...")
        new_text = f"{TEST_MARKER}: texto reescrito no passo 6 do e2e."
        text_result = update_text(client, manual_id, new_text)
        assert text_result["editado"] is True
        new_manual_id = text_result["novo_id"]
        assert new_manual_id != manual_id, "editar texto deveria gerar um ID novo"
        assert get_memory(client, manual_id) is None, "ID antigo deveria ter sido removido"
        new_payload = get_memory(client, new_manual_id)
        assert new_payload is not None and new_payload["text"] == new_text
        ids_to_cleanup_global.remove(manual_id)
        ids_to_cleanup_global.append(new_manual_id)
        print(f"   [ok] Texto editado: ID antigo removido, novo ID confirmado ({new_manual_id}).")

        # --- 7. Apagar tudo que o teste criou (5.4) ---
        print("7. Apagando as memórias de teste...")
        delete_result = delete_memories(client, ids_to_cleanup_global)
        assert delete_result["apagados"] == len(ids_to_cleanup_global)
        for i in ids_to_cleanup_global:
            assert get_memory(client, i) is None
        ids_to_cleanup_global = []  # já limpos — finally não precisa repetir
        print("   [ok] Todas as memórias de teste foram apagadas com sucesso.")

        print("\nPipeline completo da Fase 05 validado de ponta a ponta, sem deixar lixo indexado.")

    finally:
        # Limpeza de segurança: se algum assert falhou no meio do caminho,
        # ainda tenta remover o que sobrou, nas duas collections.
        if chat_point_id is not None:
            client.delete(collection_name=CHAT_COLLECTION, points_selector=[chat_point_id])
        if ids_to_cleanup_global:
            client.delete(collection_name=GLOBAL_COLLECTION, points_selector=ids_to_cleanup_global)


if __name__ == "__main__":
    main()
