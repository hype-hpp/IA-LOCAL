"""
Fase 05 - 5.2: Lógica do mecanismo /save (promoção chat_scope -> global_scope).

Decisões confirmadas com hp antes de codar:
  - Seleção explícita: chat_id + lista de IDs específicos, não "promover
    tudo do chat de uma vez" — /save é curadoria deliberada, não dump em
    massa.
  - O ponto original permanece no chat_scope depois de promovido (cópia,
    não move) — some só quando o chat inteiro for apagado (comportamento
    padrão do escopo temporário, Decision 018).

Reaproveita o vetor já existente no ponto do chat_scope (with_vectors=True
na busca) em vez de reembeddar via Ollama — mesmo conteúdo, mesmo vetor,
sem chamada nova ao modelo de embedding (regra 1/2 do projeto).

A função save_memory() recebe um client já conectado, em vez de abrir a
conexão sozinha — permite testar toda a lógica de seleção/dedup com um
Qdrant fake em memória (tests/test_save_memory.py), sem precisar de Qdrant
real rodando. Mesmo padrão de fakes já usado no loop de iteração da
Fase 04 (tests/test_agent_loop.py).
"""

from qdrant_client.models import PointStruct

from schema import memory_point_id, build_memory_payload, is_already_saved

CHAT_COLLECTION = "chat_scope"
GLOBAL_COLLECTION = "global_scope"


def save_memory(client, chat_id: str, ids: list[str], tags: list[str] | None = None) -> dict:
    """
    Promove os pontos indicados de chat_scope para global_scope.

    Regras aplicadas, nesta ordem:
      1. IDs que não existem em chat_scope são reportados, não travam o resto.
      2. Pontos encontrados mas de um chat_id diferente do informado são
         ignorados (proteção contra ID digitado errado indo pro chat errado).
      3. Pontos sem content_hash no payload são ignorados (não deveria
         acontecer com o pipeline atual, mas não deve derrubar o script).
      4. Conteúdo cujo content_hash já existe em global_scope (de ingestão
         direta, de outra promoção anterior, ou repetido dentro do mesmo
         lote pedido agora) não é promovido de novo.

    Retorna um resumo com contagens e listas de aviso, para o chamador
    (CLI hoje, UI no futuro) decidir como reportar ao usuário.
    """
    found_points = client.retrieve(
        collection_name=CHAT_COLLECTION,
        ids=ids,
        with_payload=True,
        with_vectors=True,
    )
    found_ids = {str(p.id) for p in found_points}
    not_found = [i for i in ids if i not in found_ids]

    candidates = []
    wrong_chat = []
    for p in found_points:
        if p.payload.get("chat_id") != chat_id:
            wrong_chat.append(str(p.id))
            continue
        candidates.append(p)

    already_saved = 0
    missing_hash = []
    seen_hashes_this_run = set()
    new_points = []

    for p in candidates:
        chash = p.payload.get("content_hash")
        if not chash:
            missing_hash.append(str(p.id))
            continue
        if chash in seen_hashes_this_run or is_already_saved(client, chash, collection=GLOBAL_COLLECTION):
            already_saved += 1
            continue
        seen_hashes_this_run.add(chash)

        # Campos opcionais só existem em evidência de pesquisa web
        # (src/search/evidence.py) — omitidos do payload quando ausentes.
        extra = {}
        if p.payload.get("title"):
            extra["title"] = p.payload["title"]
        if p.payload.get("query"):
            extra["query"] = p.payload["query"]

        payload = build_memory_payload(
            text=p.payload.get("text", ""),
            content_hash=chash,
            memory_type="research",
            source=p.payload.get("source", ""),
            tags=tags,
            origin_chat_id=chat_id,
            extra=extra or None,
        )
        new_points.append(
            PointStruct(id=memory_point_id(chash), vector=p.vector, payload=payload)
        )

    if new_points:
        client.upsert(collection_name=GLOBAL_COLLECTION, points=new_points)

    return {
        "solicitados": len(ids),
        "promovidos": len(new_points),
        "ja_existiam_no_global": already_saved,
        "nao_encontrados_no_chat_scope": not_found,
        "chat_id_nao_bate": wrong_chat,
        "sem_content_hash": missing_hash,
    }
