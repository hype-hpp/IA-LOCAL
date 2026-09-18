# Tutorial — Fase 05, passo 5.3 (Memória Manual Avulsa)

Este tutorial cobre **só** os arquivos entregues neste passo. Para setup
geral do projeto, ver `README.md`. Para progresso acumulado, ver
`docs/STATUS.md`.

## O que foi decidido neste passo (confirmado com hp antes de codar)

1. **Texto direto na linha de comando** (`--text "..."`), sem abrir editor
   externo tipo `git commit`.
2. **`source` fixo em `"manual"`** para toda nota deste tipo — sem rótulo
   por nota. Tags cobrem a necessidade de categorizar.

## Arquivos entregues

| Arquivo | Destino em `IA-LOCAL/` | O que é |
|---|---|---|
| `src/memory/add_note.py` | `src/memory/add_note.py` | Novo — lógica da nota manual (`add_note()`) |
| `scripts/add_memory.py` | `scripts/add_memory.py` | Novo — CLI fina |
| `tests/test_add_note.py` | `tests/test_add_note.py` | Novo — 3 casos, com fakes, sem rede |

`src/memory/schema.py` e `src/memory/save.py` **não mudaram neste passo** —
o schema já suportava `memory_type="manual"` desde o 5.1, nada novo para
adicionar lá.

## Diferença importante em relação ao /save (5.2)

No `/save`, o ponto já existe em `chat_scope` com vetor pronto — só é
copiado. Aqui o texto é **novo**, então precisa ser embeddado via Ollama
antes de entrar em `global_scope` (reaproveita `embed_text()` da Fase 02).
Por isso, se a nota já existir (mesmo `content_hash`), o script nem chama
o Ollama — evita gastar uma chamada de embedding à toa para um conteúdo
que vai ser descartado por dedup de qualquer forma.

## Padrão de teste usado

Mesmo padrão do `tests/test_agent_loop.py` (Fase 04): `embed_text` é
importado direto no módulo (`src/memory/add_note.py`), e o teste
substitui `add_note.embed_text` por uma função fake via monkeypatch
simples — sem precisar do Ollama real rodando, e sem inventar um
mecanismo de injeção de dependência novo só para isto.

## Como testar

```bash
# 1. Teste isolado da lógica (rápido, sem rede, sem Qdrant/Ollama reais)
python tests/test_add_note.py

# 2. Reconfirma que nada quebrou dos passos anteriores
python tests/test_memory_schema.py
python tests/test_save_memory.py

# 3. Teste real: salvar uma nota de verdade
python scripts/add_memory.py --text "IA-LOCAL usa Qdrant com duas collections: chat_scope e global_scope" --tags teste_5_3

# 4. Rodar o MESMO comando de novo — deve pular por dedup
python scripts/add_memory.py --text "IA-LOCAL usa Qdrant com duas collections: chat_scope e global_scope" --tags teste_5_3
```

### Checklist de validação

- [ ] `test_add_note.py` passa os 3 casos
- [ ] `test_memory_schema.py` e `test_save_memory.py` continuam passando
- [ ] Nota real salva mostra `[ok] Nota salva em 'global_scope' (id=...)`
- [ ] Rodar o mesmo comando de novo mostra
      `[skip] Nota não salva: já existe uma memória idêntica em global_scope`
- [ ] No dashboard do Qdrant, a nota salva tem `memory_type: "manual"`,
      `source: "manual"`, `tags: ["teste_5_3"]`

## Próximo passo (5.4)

Visualizar / editar / apagar memórias (regra 10 do projeto) — CLI para
listar memórias em `global_scope` (filtrando por `memory_type`/`tags`),
ver detalhe de uma, e apagar por ID.
