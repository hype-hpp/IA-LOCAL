# IA Local — Fase 02 (RAG / Knowledge)

## Estrutura do projeto

```
IA-LOCAL/
├── docker-compose.yml       # sobe o Qdrant
├── requirements.txt         # dependências Python
├── README.md                # este arquivo
├── .gitignore                # gerado por scripts/setup_dirs.sh
│
├── scripts/                  # ferramentas administrativas (rodar manualmente, uma vez ou sob demanda)
│   ├── setup_dirs.sh           # cria chats/, knowledge/, data/
│   ├── create_collections.py   # cria as collections do Qdrant (idempotente)
│   └── ingest_document.py      # ingesta um documento real no global_scope
│
├── src/                       # código de produção do sistema
│   └── ingestion/
│       ├── __init__.py
│       ├── embedding_client.py   # embed_text() / embed_texts() via Ollama
│       ├── parser.py              # leitura de .md/.txt
│       └── chunking.py            # chunking por palavras com overlap
│
├── tests/                     # testes de validação (rodar sempre que mexer no pipeline)
│   ├── test_embedding_dim.py
│   ├── test_end_to_end.py
│   └── test_chunking.py
│
├── chats/                     # escopo temporário (Decision 018) — criado pelo setup_dirs.sh
│   └── {chat_id}/
│
├── knowledge/                 # escopo global/persistente (Decision 018)
│   ├── documents/
│   └── cache/
│
└── data/
    └── qdrant/                # storage do Qdrant (volume do docker-compose)
```

## Convenção adotada

- `scripts/` = coisas que você roda manualmente uma vez ou ocasionalmente (setup, migrações, criação de collections). Nunca é importado por outro código.
- `src/` = código de produção, importável, que vai crescer nas próximas fases (`src/ingestion/`, depois `src/retrieval/`, `src/agent/`, etc.)
- `tests/` = scripts de validação. Rodar depois de qualquer mudança no pipeline de ingestão.

## Setup (do zero)

```bash
cd ~/IA-LOCAL

# 1. Estrutura de diretórios (idempotente, pode rodar de novo sem medo)
chmod +x scripts/setup_dirs.sh
./scripts/setup_dirs.sh

# 2. Subir o Qdrant
docker compose up -d
curl http://localhost:6333/healthz

# 3. Dependências Python
source ~/crawler-ai/bin/activate
pip install -r requirements.txt

# 4. Criar as collections (idempotente — pula se já existir)
python scripts/create_collections.py

# 5. Modelo de embedding
ollama pull qwen3-embedding:4b

# 6. Validar o pipeline
python tests/test_embedding_dim.py
python tests/test_end_to_end.py
```

## Status validado no hardware real

- [x] Qdrant rodando, healthz OK
- [x] Collections `chat_scope` e `global_scope` criadas (dim=2560, COSINE)
- [ ] `qwen3-embedding:4b` puxado e dimensão confirmada
- [ ] Pipeline embed → insert → search validado ponta a ponta

## Decisões registradas nesta fase

- **Duas collections separadas** (`chat_scope` / `global_scope`) em vez de uma única com filtro de payload — isolamento mais simples, menos risco de vazamento entre escopos.
- **VECTOR_SIZE=2560** confirmado como correto para `qwen3-embedding:4b` (dimensão nativa, documentada no repositório oficial QwenLM/Qwen3-Embedding).
- **Modelo oficial do Ollama** (`qwen3-embedding:4b`, sem namespace de terceiros) — evita depender de builds de terceiros não auditados.

## Próximo passo (2.4) — CONCLUÍDO NESTA ENTREGA

Parser + chunking implementados:

- `src/ingestion/parser.py` — lê `.md`/`.txt` (PDF fica para depois, sem necessidade ainda)
- `src/ingestion/chunking.py` — chunking por palavras (250 palavras, overlap 40) com janela deslizante
- `scripts/ingest_document.py` — script real: lê arquivo → chunka → dedup por hash → embed em lote → insere no `global_scope`
- `tests/test_chunking.py` — valida a função de chunking sem depender de rede/Qdrant/Ollama

### Como testar

```bash
# 1. Teste isolado do chunking (rápido, sem rede)
python tests/test_chunking.py

# 2. Ingestão real: pegue qualquer .md do seu projeto como primeiro teste
cp /caminho/para/algum_arquivo.md knowledge/documents/
python scripts/ingest_document.py knowledge/documents/algum_arquivo.md

# 3. Rode de novo o MESMO comando — deve pular tudo por já estar indexado (dedup funcionando)
python scripts/ingest_document.py knowledge/documents/algum_arquivo.md
```

### Checklist de validação

- [ ] `test_chunking.py` passa todos os asserts
- [ ] Primeira ingestão mostra `N novos, 0 já existiam`
- [ ] Segunda ingestão do mesmo arquivo mostra `0 novos, N já existiam` (dedup funcionando)
- [ ] `global_scope` no dashboard do Qdrant (`http://localhost:6333/dashboard`) mostra os pontos inseridos, com payload `source`, `content_hash`, `text`, `chunk_index`, `ingested_at`

### Decisão registrada

- Chunking por **palavras**, não caracteres nem tokens — mais simples, evita cortar palavra no meio. Tamanho padrão 250 palavras / overlap 40, ajustável depois de observar qualidade real de retrieval (Fase de hybrid search).
- ID do ponto no Qdrant = **UUID determinístico derivado do content_hash** (via `uuid5`), não o hash bruto — Qdrant só aceita inteiro ou UUID como id. Isso também reforça o dedup: reingerir o mesmo texto gera o mesmo ID e apenas sobrescreve.

## Próximo passo (2.5)

Metadata mais rica + hybrid search: adicionar BM25/sparse ao lado do dense retrieval já funcionando, e começar o fusion + reranking.
