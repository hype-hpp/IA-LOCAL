# IA Local — Fase 02 (RAG / Knowledge)

## Estrutura

```
IA-LOCAL/
├── docker-compose.yml
├── requirements.txt
├── README.md
├── docs/
│   └── STATUS.md            # progresso atual, checklist curto
├── scripts/                  # rodar manualmente, sob demanda
│   ├── setup_dirs.sh
│   ├── create_collections.py
│   └── ingest_document.py
├── src/
│   ├── ingestion/
│   │   ├── embedding_client.py
│   │   ├── parser.py
│   │   └── chunking.py
│   └── retrieval/
│       ├── fusion.py           # Reciprocal Rank Fusion
│       ├── bm25_index.py       # índice sparse em memória
│       └── hybrid_search.py    # orquestra dense + sparse
├── tests/
│   ├── test_embedding_dim.py
│   ├── test_end_to_end.py
│   ├── test_chunking.py
│   └── test_rrf.py
├── chats/
├── knowledge/
│   └── documents/
└── data/
    └── qdrant/
```

## Setup rápido

```bash
cd ~/IA-LOCAL
./scripts/setup_dirs.sh
docker compose up -d
pip install -r requirements.txt
python scripts/create_collections.py
ollama pull qwen3-embedding:4b
```

## Ingerir um documento

```bash
cp algum_arquivo.md knowledge/documents/
python scripts/ingest_document.py knowledge/documents/algum_arquivo.md
```

Rodar de novo o mesmo comando não duplica nada (dedup por hash).

## Buscar (hybrid search)

```bash
python scripts/search.py "sua pergunta aqui"
```

## Rodar os testes

```bash
python tests/test_chunking.py       # rápido, sem rede
python tests/test_rrf.py            # rápido, sem rede
python tests/test_embedding_dim.py  # precisa do Ollama rodando
python tests/test_end_to_end.py     # precisa do Ollama + Qdrant rodando
```

## Progresso

Ver `docs/STATUS.md`.

## Como usar arquivos novos que eu (Claude) te entregar

Toda entrega de novos arquivos vem com um `docs/TUTORIAL.md` explicando especificamente aqueles arquivos — o que fazem e como rodar. Esse tutorial é substituído a cada passo (não acumula histórico); a referência estável de longo prazo é este README.

Regra de onde colocar: o caminho do arquivo no card de download é o mesmo caminho dentro de `IA-LOCAL/` (ex: `src/retrieval/fusion.py` vai em `src/retrieval/fusion.py`). Se o arquivo já existe, apague o antigo antes de copiar o novo — evita ficar arquivo "fantasma" desatualizado.
