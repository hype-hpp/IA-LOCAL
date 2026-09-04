# IA Local — Fase 03 (Web Search + Browser, em andamento)

## Estrutura

```
IA-LOCAL/
├── docker-compose.yml        # sobe Qdrant + SearXNG
├── requirements.txt          # dependências Python
├── README.md
├── docs/
│   ├── STATUS.md             # progresso atual, checklist curto
│   └── TUTORIAL.md           # tutorial do ÚLTIMO passo entregue (substituído a cada passo)
├── scripts/                  # rodar manualmente, sob demanda
│   ├── setup_dirs.sh
│   ├── create_collections.py
│   ├── ingest_document.py
│   ├── search.py              # busca híbrida (RAG) no global_scope
│   └── search_web.py          # busca na web via SearXNG
├── src/
│   ├── ingestion/
│   │   ├── embedding_client.py
│   │   ├── parser.py
│   │   └── chunking.py
│   ├── retrieval/
│   │   ├── fusion.py           # Reciprocal Rank Fusion
│   │   ├── bm25_index.py       # índice sparse em memória
│   │   ├── hybrid_search.py    # orquestra dense + sparse
│   │   └── llm_reranker.py     # reranking via GPT-OSS
│   └── search/                 # NOVO (Fase 03)
│       └── searxng_client.py   # cliente de busca via SearXNG
├── tests/
│   ├── test_embedding_dim.py
│   ├── test_end_to_end.py
│   ├── test_chunking.py
│   ├── test_rrf.py
│   ├── test_llm_reranker_parsing.py
│   └── test_searxng_client.py  # NOVO (Fase 03)
├── chats/
├── knowledge/
│   └── documents/
├── searxng/                   # NOVO (Fase 03) — config gerada pelo container (settings.yml)
└── data/
    └── qdrant/
```

## Setup rápido (do zero)

```bash
cd ~/IA-LOCAL
./scripts/setup_dirs.sh
docker compose up -d
pip install -r requirements.txt
python scripts/create_collections.py
ollama pull qwen3-embedding:4b
```

### SearXNG (busca web) — configuração manual obrigatória na primeira vez

O SearXNG bloqueia respostas em JSON por padrão. Depois do `docker compose up -d`,
edite `searxng/settings.yml` (gerado automaticamente no primeiro boot):

```yaml
search:
  formats:
    - html
    - json
```

E troque `server.secret_key` pelo resultado de `openssl rand -hex 32`. Depois:
`docker compose restart searxng`.

## Ingerir um documento (RAG / knowledge)

```bash
cp algum_arquivo.md knowledge/documents/
python scripts/ingest_document.py knowledge/documents/algum_arquivo.md
```

Rodar de novo o mesmo comando não duplica nada (dedup por hash).

## Buscar no conhecimento local (hybrid search + rerank)

```bash
python scripts/search.py "sua pergunta aqui"
```

## Buscar na web (SearXNG)

```bash
python scripts/search_web.py "sua query aqui"
```

## Rodar os testes

```bash
# Rápidos, sem rede/serviço externo
python tests/test_chunking.py
python tests/test_rrf.py
python tests/test_llm_reranker_parsing.py

# Precisam de serviço no ar
python tests/test_embedding_dim.py     # Ollama
python tests/test_end_to_end.py        # Ollama + Qdrant
python tests/test_searxng_client.py    # SearXNG
```

## Progresso

Ver `docs/STATUS.md`.

## Como usar arquivos novos que eu te entregar

Toda entrega de novos arquivos vem com um `docs/TUTORIAL.md` explicando especificamente aqueles arquivos — o que fazem e como rodar. Esse tutorial é substituído a cada passo (não acumula histórico); a referência estável de longo prazo é este README.

Regra de onde colocar: o caminho do arquivo no card de download é o mesmo caminho dentro de `IA-LOCAL/` (ex: `src/search/searxng_client.py` vai em `src/search/searxng_client.py`). Se o arquivo já existe, apague o antigo antes de copiar o novo — evita ficar arquivo "fantasma" desatualizado.
