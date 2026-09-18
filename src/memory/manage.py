"""
Fase 05 - 5.4: Visualizar / editar / apagar memórias (regra 10 do projeto).

Decisões confirmadas com hp antes de codar:
  - "Editar" cobre tanto tags (troca simples de payload, sem reembedding)
    quanto texto (apaga o ponto antigo e reinsere com texto novo,
    reembeddando via Ollama). IMPORTANTE: como o ID do ponto em
    global_scope é derivado do content_hash do texto (Decision 023 /
    schema.py), editar o TEXTO de uma memória sempre gera um ID NOVO — o
    antigo deixa de existir. Editar só as tags mantém o mesmo ID.
  - Apagar é só por ID explícito (um ou vários) — sem apagar em massa por
    filtro (memory_type/tag/chat_id). Decisão de hp: mais seguro, cada
    apagamento é uma escolha explícita, não um filtro que pode pegar mais
    do que o esperado.

Reaproveita content_hash() de add_note.py e memory_point_id()/
build_memory_payload()/is_already_saved() de schema.py — nenhuma lógica
de hash ou payload duplicada aqui (regra 2 do projeto).
"""

import os
import sys

from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

from schema import memory_point_id, build_memory_payload, is_already_saved

sys.path.insert(0, os.path.dirname(__file__))
from add_note import content_hash

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
from embedding_client import embed_text

GLOBAL_COLLECTION = "global_scope"
PREVIEW_LENGTH = 150


def _build_filter(memory_type=None, tag=None, origin_chat_id=None):
    conditions = []
    if memory_type:
        conditions.append(FieldCondition(key="memory_type", match=MatchValue(value=memory_type)))
    if tag:
        # Match num campo array: Qdrant considera "bate" se o valor está
        # presente na lista (comportamento nativo para payload em array).
        conditions.append(FieldCondition(key="tags", match=MatchValue(value=tag)))
    if origin_chat_id:
        conditions.append(FieldCondition(key="origin_chat_id", match=MatchValue(value=origin_chat_id)))
    return Filter(must=conditions) if conditions else None


def list_memories(client, memory_type=None, tag=None, origin_chat_id=None, limit=20, offset=None):
    """
    Lista memórias em global_scope, com preview truncado do texto.

    Sem índice de payload dedicado para 'tags' (o dataset pessoal atual é
    pequeno demais para justificar isso agora — regra 1/5 do projeto: se
    a listagem ficar lenta com uso real, criar o índice em
    create_collections.py é a correção natural).
    """
    scroll_filter = _build_filter(memory_type, tag, origin_chat_id)

    points, next_offset = client.scroll(
        collection_name=GLOBAL_COLLECTION,
        scroll_filter=scroll_filter,
        limit=limit,
        offset=offset,
        with_payload=True,
    )

    records = []
    for p in points:
        payload = p.payload or {}
        text = payload.get("text", "")
        preview = text if len(text) <= PREVIEW_LENGTH else text[:PREVIEW_LENGTH] + "..."
        records.append({
            "id": str(p.id),
            "memory_type": payload.get("memory_type"),
            "source": payload.get("source"),
            "tags": payload.get("tags", []),
            "saved_at": payload.get("saved_at"),
            "preview": preview,
        })

    return records, next_offset


def get_memory(client, memory_id: str) -> dict | None:
    """Retorna o payload completo de uma memória, ou None se não existir."""
    found = client.retrieve(collection_name=GLOBAL_COLLECTION, ids=[memory_id], with_payload=True)
    return found[0].payload if found else None


def update_tags(client, memory_id: str, tags: list[str]) -> dict:
    """
    Substitui a lista de tags de uma memória existente. Não mexe no
    conteúdo nem no ID — troca simples de payload, sem reembedding.
    """
    found = client.retrieve(collection_name=GLOBAL_COLLECTION, ids=[memory_id], with_payload=False)
    if not found:
        return {"editado": False, "motivo": "memória não encontrada"}

    client.set_payload(
        collection_name=GLOBAL_COLLECTION,
        payload={"tags": tags},
        points=[memory_id],
    )
    return {"editado": True, "motivo": None}


def update_text(client, memory_id: str, new_text: str, override_tags: list[str] | None = None) -> dict:
    """
    Substitui o TEXTO de uma memória existente.

    Como o ID é derivado do content_hash do texto, isso sempre resulta
    num ID novo — o ponto antigo é apagado e um novo é inserido no lugar,
    com o texto reembeddado via Ollama. Metadata (memory_type, source,
    origin_chat_id, tags, e campos extras como chunk_index/title/query)
    é preservada do ponto antigo, exceto quando `override_tags` é
    informado, que substitui as tags no mesmo passo.
    """
    new_text = new_text.strip()
    if not new_text:
        raise ValueError("Texto vazio: nada para salvar.")

    found = client.retrieve(collection_name=GLOBAL_COLLECTION, ids=[memory_id], with_payload=True)
    if not found:
        return {"editado": False, "motivo": "memória não encontrada", "novo_id": None}

    old_payload = found[0].payload or {}
    new_chash = content_hash(new_text)

    if new_chash == old_payload.get("content_hash"):
        return {"editado": False, "motivo": "texto idêntico ao atual, nada mudou", "novo_id": memory_id}

    if is_already_saved(client, new_chash, collection=GLOBAL_COLLECTION):
        return {
            "editado": False,
            "motivo": "já existe outra memória com esse texto exato (edição cancelada para não sobrescrevê-la)",
            "novo_id": None,
        }

    vector = embed_text(new_text)

    extra = {}
    for key in ("chunk_index", "title", "query"):
        if key in old_payload:
            extra[key] = old_payload[key]

    new_payload = build_memory_payload(
        text=new_text,
        content_hash=new_chash,
        memory_type=old_payload.get("memory_type", "manual"),
        source=old_payload.get("source", "manual"),
        tags=override_tags if override_tags is not None else old_payload.get("tags"),
        origin_chat_id=old_payload.get("origin_chat_id"),
        extra=extra or None,
    )
    new_id = memory_point_id(new_chash)

    # Insere o novo ponto ANTES de apagar o antigo: se algo falhar entre
    # os dois passos, fica uma duplicata (recuperável), não uma perda de
    # dado (irrecuperável).
    client.upsert(
        collection_name=GLOBAL_COLLECTION,
        points=[PointStruct(id=new_id, vector=vector, payload=new_payload)],
    )
    client.delete(collection_name=GLOBAL_COLLECTION, points_selector=[memory_id])

    return {"editado": True, "motivo": None, "novo_id": new_id}


def delete_memories(client, ids: list[str]) -> dict:
    """Apaga memórias por ID explícito. IDs inexistentes são reportados, não travam o resto."""
    found = client.retrieve(collection_name=GLOBAL_COLLECTION, ids=ids, with_payload=False)
    found_ids = {str(p.id) for p in found}
    not_found = [i for i in ids if i not in found_ids]

    if found_ids:
        client.delete(collection_name=GLOBAL_COLLECTION, points_selector=list(found_ids))

    return {
        "solicitados": len(ids),
        "apagados": len(found_ids),
        "nao_encontrados": not_found,
    }
