"""
Fase 05 - 5.3: Lógica da nota manual avulsa (memory_type="manual").

Diferença em relação ao /save (5.2): ali o ponto já existia em chat_scope
com vetor pronto (só reaproveitado). Aqui o texto é novo — precisa ser
embeddado via Ollama antes de inserir em global_scope. Reaproveita
embed_text(), já validado desde a Fase 02 (src/ingestion/embedding_client.py),
em vez de duplicar a chamada ao modelo de embedding.

Decisões confirmadas com hp antes de codar:
  - Texto chega como argumento direto (--text), não abre editor externo
    tipo git commit.
  - Campo "source" fixo em "manual" para todo ponto deste tipo — sem
    rótulo por nota. Tags (já suportadas pelo schema desde o 5.1) cobrem
    a necessidade de categorizar; "source" fixo é revisável com uso real
    (regra 5 do projeto), se um dia fizer falta diferenciar a origem de
    cada nota manual.

Import de embed_text no nível do módulo (não injetado por parâmetro) —
mesmo padrão já usado em src/coding/agent_loop.py (Fase 04): os testes
substituem add_note.embed_text por um fake via monkeypatch simples, sem
precisar de Ollama real rodando (ver tests/test_add_note.py).
"""

import os
import sys
import hashlib

from qdrant_client.models import PointStruct

from schema import memory_point_id, build_memory_payload, is_already_saved

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from embedding_client import embed_text

GLOBAL_COLLECTION = "global_scope"


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def add_note(client, text: str, tags: list[str] | None = None) -> dict:
    """
    Adiciona uma nota manual em global_scope.

    Se já existir uma memória idêntica (mesmo content_hash), não salva de
    novo e não chama embed_text — evita gastar uma chamada de embedding à
    toa para um conteúdo que já vai ser descartado por dedup.

    Retorna um resumo do resultado, para o chamador (CLI hoje, UI no
    futuro) decidir como reportar ao usuário.
    """
    text = text.strip()
    if not text:
        raise ValueError("Nota vazia: nada para salvar.")

    chash = content_hash(text)

    if is_already_saved(client, chash, collection=GLOBAL_COLLECTION):
        return {
            "salvo": False,
            "motivo": "já existe uma memória idêntica em global_scope",
            "content_hash": chash,
            "id": None,
        }

    vector = embed_text(text)

    payload = build_memory_payload(
        text=text,
        content_hash=chash,
        memory_type="manual",
        source="manual",
        tags=tags,
    )
    point = PointStruct(id=memory_point_id(chash), vector=vector, payload=payload)
    client.upsert(collection_name=GLOBAL_COLLECTION, points=[point])

    return {"salvo": True, "motivo": None, "content_hash": chash, "id": point.id}
