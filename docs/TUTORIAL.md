# Tutorial — Fase 05, passo 5.4 (Visualizar / Editar / Apagar Memórias)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## O que foi decidido neste passo (confirmado com hp antes de codar)

1. **"Editar" cobre tags E texto**. Editar tags é uma troca simples de
   payload (sem reembedding, mesmo ID). Editar texto reembedda via Ollama
   e **gera um ID novo** — o ID é derivado do hash do conteúdo (Decision
   023 / `schema.py`), então texto novo = hash novo = ID novo. O ponto
   antigo é apagado.
2. **Apagar é só por ID explícito** (um ou vários) — sem filtro em massa
   por `memory_type`/`tag`/`chat_id`. Decisão de hp: mais seguro.
3. Confirmação interativa antes de apagar de verdade (`[s/N]`), pulável
   com `--yes` para uso em automação — proteção padrão de ferramenta
   destrutiva, não pedida explicitamente mas coerente com a regra 11 do
   projeto (cautela com o que pode destruir dado).

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `src/memory/manage.py` | `src/memory/manage.py` | Novo — `list_memories()`, `get_memory()`, `update_tags()`, `update_text()`, `delete_memories()` |
| `scripts/list_memories.py` | `scripts/list_memories.py` | Novo — listar com filtros, ou ver detalhe de uma por `--id` |
| `scripts/edit_memory.py` | `scripts/edit_memory.py` | Novo — editar tags e/ou texto |
| `scripts/delete_memory.py` | `scripts/delete_memory.py` | Novo — apagar por ID, com confirmação |
| ` .py` | `tests/test_manage_memory.py` | Novo — 12 casos, com Qdrant fake, sem rede |

`schema.py`, `save.py` e `add_note.py` **não mudam neste passo**.

## Atenção: editar texto troca o ID

Isso é o detalhe mais importante deste passo. Se você editar o **texto**
de uma memória:

```bash
python scripts/edit_memory.py --id 13574b09-a154-59ca-a225-2526fb616122 --text "texto corrigido"
```
13574b09-a154-59ca-a225-2526fb616122
O ID `abc-123` deixa de existir depois disso. O script imprime o novo ID
no final (`Novo ID: ...`) — anote se for referenciar essa memória de
novo (ex: pra apagar ou editar de novo depois).

Editar só as **tags** não tem esse problema — o ID permanece o mesmo:

```bash
python scripts/edit_memory.py --id 13574b09-a154-59ca-a225-2526fb616122 --tags nova_tag,outra_tag
```

## Proteções embutidas em `update_text`

- Editar para o **mesmo texto que já está lá** não faz nada (`editado: False`, sem gastar embedding).
- Editar para um texto que **já existe como outra memória** é recusado
  (evitaria colidir os dois no mesmo ID e sobrescrever a outra memória
  sem querer) — o ponto original permanece intocado.

## Como testar

```bash
# 1. Teste isolado da lógica (rápido, sem rede, sem Qdrant/Ollama reais)
python tests/test_manage_memory.py

# 2. Reconfirma que nada quebrou dos passos anteriores
python tests/test_memory_schema.py
python tests/test_save_memory.py
python tests/test_add_note.py

# 3. Teste real: listar o que já está em global_scope
python scripts/list_memories.py

# 4. Filtrar por tipo e por tag
python scripts/list_memories.py --memory-type manual
python scripts/list_memories.py --tag teste_5_3

# 5. Ver o detalhe completo de uma memória (pegue um ID do passo 3)
python scripts/list_memories.py --id b7c666fb-4a03-5fc9-9714-4da905545ae2

# 6. Editar só as tags (mesmo ID depois)
python scripts/edit_memory.py --id b7c666fb-4a03-5fc9-9714-4da905545ae2 --tags teste_5_4

# 7. Editar o texto (ID novo depois — anote o que o script imprimir)
python scripts/edit_memory.py --id b7c666fb-4a03-5fc9-9714-4da905545ae2 --text "texto atualizado no 5.4"

# 8. Apagar (vai pedir confirmação [s/N])
python scripts/delete_memory.py --ids b7c666fb-4a03-5fc9-9714-4da905545ae2
```

### Checklist de validação

- [ ] `test_manage_memory.py` passa os 12 casos
- [ ] `test_memory_schema.py`, `test_save_memory.py`, `test_add_note.py` continuam passando
- [ ] `list_memories.py` sem filtro mostra todas as memórias reais já salvas
- [ ] Filtro por `--memory-type` e por `--tag` funciona no dado real
- [ ] `--id` mostra o detalhe completo (texto inteiro, não truncado)
- [ ] `edit_memory.py --tags` troca as tags mantendo o mesmo ID (confirme com `list_memories.py --id`)
- [ ] `edit_memory.py --text` gera um ID novo, o antigo some (confirme que `list_memories.py --id ID_ANTIGO` não encontra mais nada)
- [ ] `delete_memory.py` pede confirmação, cancela se você responder diferente de "s", e apaga de fato se confirmar

## Fase 05 — o que falta

Só o passo 5.5: teste end-to-end cobrindo o pipeline completo da fase
(ingestão → `/save` → nota manual → listar → editar → apagar) e o
fechamento formal (roadmap, decisions, estrutura, current_state).
