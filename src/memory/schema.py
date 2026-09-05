"""
Fase 05 - 5.1: Schema de metadata de memória para o global_scope.

Decisão desta fase (confirmada com hp): a metadata estruturada das memórias
fica inteiramente no payload dos pontos do Qdrant, sem componente novo
(ex: PostgreSQL) — reaproveita a mesma collection já validada nas Fases
02/03, só adiciona campos novos ao payload que já existia. Se isso não se
mostrar suficiente com uso real, é revisável (regra 5 do projeto).

Três tipos de memória em 'global_scope':
  - "knowledge": chunk de documento ingerido diretamente
    (scripts/ingest_document.py, Fase 02) — fluxo já existente, sem mudança
    de comportamento, só passa a usar este módulo para não duplicar lógica.
  - "research": evidência de pesquisa web promovida do chat_scope via
    /save (passo 5.2, próxima entrega).
  - "manual": nota livre adicionada diretamente pelo usuário (passo 5.3),
    sem passar por uma busca prévia.

Este módulo centraliza a construção do payload e do ID do ponto para os
três casos, para as rotinas de ingestão / /save / nota manual não
duplicarem a mesma lógica (regra 2 do projeto: não reinventar o que já
existe).

Nota de nomenclatura: o campo de timestamp da Fase 02 se chamava
"ingested_at". A partir desta fase, o campo comum passa a se chamar
"saved_at" para os três tipos de memória (uniformidade para poder
listar/filtrar memórias de qualquer tipo do mesmo jeito no passo 5.4).
Como ainda não há documentos reais indexados em 'global_scope' neste
projeto, não há dado antigo para migrar — se isso mudar, uma migração
pontual de payload seria necessária antes de confiar em buscas por
"saved_at" em pontos antigos.
"""

import uuid
from datetime import datetime, timezone

MEMORY_TYPES = {"knowledge", "research", "manual"}


def memory_point_id(content_hash: str) -> str:
    """
    ID determinístico do ponto em global_scope, derivado do content_hash.

    Mesma convenção já usada desde a Fase 02 (Decision 023): o mesmo
    conteúdo sempre produz o mesmo UUID (uuid5, namespace fixo), então
    reingerir/repromover o mesmo texto sobrescreve o ponto existente em
    vez de duplicar. Isso também dedup automaticamente ENTRE os três tipos
    de memória: se um texto idêntico já existe como "knowledge" e depois
    é promovido como "research", os dois caem no mesmo ID — o upsert mais
    recente vence, sem duplicar o vetor.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, content_hash))


def build_memory_payload(
    *,
    text: str,
    content_hash: str,
    memory_type: str,
    source: str,
    tags: list[str] | None = None,
    origin_chat_id: str | None = None,
    extra: dict | None = None,
) -> dict:
    """
    Monta o payload padrão de uma memória em global_scope.

    Campos comuns aos três tipos: text, content_hash, source, memory_type,
    tags, saved_at.

    `origin_chat_id` é opcional e normalmente só se aplica a memórias do
    tipo "research" (de qual chat ela foi promovida) — omitido do payload
    quando não fornecido, em vez de gravado como None.

    `extra` permite campos específicos de um tipo sem forçar o schema
    comum a prever tudo de antemão (ex: chunk_index, que só faz sentido
    para "knowledge").
    """
    if memory_type not in MEMORY_TYPES:
        raise ValueError(
            f"memory_type inválido: {memory_type!r}. Válidos: {sorted(MEMORY_TYPES)}"
        )

    payload = {
        "text": text,
        "content_hash": content_hash,
        "source": source,
        "memory_type": memory_type,
        "tags": tags or [],
        "saved_at": datetime.now(timezone.utc).isoformat(),
    }

    if origin_chat_id is not None:
        payload["origin_chat_id"] = origin_chat_id

    if extra:
        payload.update(extra)

    return payload
