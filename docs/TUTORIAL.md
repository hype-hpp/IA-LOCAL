# Tutorial — Fase 05, passo 5.2 (Mecanismo /save)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## O que foi decidido neste passo (confirmado com hp antes de codar)

1. **Seleção explícita**: `chat_id` + lista de IDs específicos (`--ids`) —
   não existe "promover tudo do chat de uma vez". `/save` é curadoria
   deliberada, não dump em massa.
2. **Cópia, não move**: o ponto original permanece no `chat_scope` depois
   de promovido. Só some quando o chat inteiro for apagado (comportamento
   padrão do escopo temporário, Decision 018).
3. Reaproveita o **vetor já existente** no ponto do `chat_scope`
   (`with_vectors=True`) em vez de reembeddar via Ollama.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `src/memory/schema.py` | `src/memory/schema.py` | **Substitui o do 5.1** — adiciona `is_already_saved()` |
| `src/memory/save.py` | `src/memory/save.py` | Novo — lógica de promoção (`save_memory()`) |
| `scripts/save_memory.py` | `scripts/save_memory.py` | Novo — CLI fina, só parseia argumentos |
| `tests/test_save_memory.py` | `tests/test_save_memory.py` | Novo — testa `save_memory()` com Qdrant fake, sem rede |

Apague os arquivos antigos antes de copiar os novos por cima.

## Por que ficou em dois arquivos (`save.py` + `save_memory.py`)

Mesmo padrão já usado na Fase 04 (`src/coding/agent_loop.py` +
`scripts/solve_task.py`): lógica de verdade em `src/` (importável,
testável com fakes), CLI fina em `scripts/` (só argparse + prints).

## Como descobrir os IDs de um chat para promover

Por enquanto, via dashboard do Qdrant
(`http://localhost:6333/dashboard`), filtrando a collection `chat_scope`
por `payload.chat_id`. Uma forma mais direta de buscar isso (ex: listar
por texto) fica para quando houver UI (Fase 08) ou se sentir falta antes
disso — regra 1 do projeto, não construir sem necessidade real.

## Como testar

```bash
# 1. Teste isolado da lógica de /save (rápido, sem rede, sem Qdrant real,
#    usa um Qdrant fake em memória — mesmo padrão do 4.3)
python tests/test_save_memory.py

# 2. Reconfirma que o schema.py atualizado não quebrou o teste do 5.1
python tests/test_memory_schema.py

# 3. Teste real: promover uma evidência de pesquisa web de verdade
#    a) Rode uma pesquisa via scripts/web_research.py (Fase 03) pra ter
#       evidência real em chat_scope, e anote o chat_id usado
#    b) No dashboard do Qdrant, pegue 1-2 IDs de pontos daquele chat_id
#    c) Promova:
python scripts/save_memory.py --chat-id SEU_CHAT_ID --ids ID1,ID2 --tags teste_5_2
```

### Checklist de validação

- [ ] `test_save_memory.py` passa todos os 6 casos
- [ ] `test_memory_schema.py` (do 5.1) continua passando
- [ ] `save_memory.py` real promove os IDs pedidos e mostra
      `Promovidos: N` correto
- [ ] Rodar o **mesmo comando de novo** (mesmos IDs) deve mostrar
      `Promovidos: 0` e `Já existiam no global_scope (pulados): N` — confirma dedup
- [ ] No dashboard, o(s) ponto(s) promovido(s) em `global_scope` têm
      `memory_type: "research"`, `origin_chat_id`, `tags` (se informado),
      e o texto batendo com o original do `chat_scope`
- [ ] O ponto original ainda existe em `chat_scope` (não foi removido)
- [ ] Pedir um ID inexistente (ex: `--ids ID_QUE_NAO_EXISTE`) não quebra o
      script — aparece em `[aviso] IDs não encontrados no chat_scope`

## Próximo passo (5.3)

Memória manual avulsa: comando para adicionar uma nota livre direto no
`global_scope` (`memory_type="manual"`), sem precisar de uma busca prévia
— reaproveitando `memory_point_id()`, `build_memory_payload()` e
`is_already_saved()` já existentes em `src/memory/schema.py`.
