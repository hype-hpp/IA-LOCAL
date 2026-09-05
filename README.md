<div align="center">

# 🧠 IA Local

**Um assistente de IA agentic, local-first e multimodal, rodando 100% no seu hardware.**

Sem nuvem, sem mensalidade, sem enviar seus dados pra fora — modelos locais via [Ollama](https://ollama.com), retrieval próprio, pesquisa web própria e um coding agent isolado em sandbox.

</div>

---

## 📌 Visão geral

O objetivo não é competir com um modelo de fronteira hospedado — é **maximizar a capacidade prática do sistema inteiro**, combinando modelos locais, ferramentas, memória, retrieval, sandbox e verificação.

| Peça | Papel |
|---|---|
| **GPT-OSS 20B** | Orquestrador — decide, planeja, formata a resposta final |
| **Qwen3-Coder 30B** | Tool de código — gera/corrige código sob demanda |
| **Qwen3-Embedding 4B** | Embeddings para RAG (dim=2560) |
| **Qdrant** | Banco vetorial (`chat_scope` temporário / `global_scope` persistente) |
| **SearXNG + Crawl4AI** | Pesquisa e extração de conteúdo da web |
| **Docker Sandbox** | Execução isolada de código gerado |

Hardware de referência: Ryzen 7 5800X3D · RTX 4070 Ti SUPER 16GB · 32GB RAM · Arch Linux.

## 🚧 Progresso

| Fase | Descrição | Status |
|---|---|:---:|
| 01 | Fundação + Benchmark | ✅ |
| 02 | RAG / Knowledge (Qdrant, embeddings, hybrid search, rerank) | ✅ |
| 03 | Web Search + Browser (SearXNG, Crawl4AI, multi-query) | ✅ |
| 04 | Coding Agent + Sandbox (Qwen3-Coder, Docker, auto-correção) | ✅ |
| 05 | Memory (promoção `/save`, memória episódica/semântica) | ⏳ próxima |
| 06–10 | Adaptive Crawler, Agent Core, UI, Benchmarks, Otimização | ⏳ |

Progresso detalhado por passo: [`docs/STATUS.md`](docs/STATUS.md).

## 📂 Estrutura

```
IA-LOCAL/
├── docker-compose.yml        # sobe Qdrant + SearXNG
├── requirements.txt
├── sandbox/
│   └── Dockerfile             # imagem do sandbox de execução (python:3.11-slim + libs)
├── docs/
│   ├── STATUS.md              # progresso por passo/fase
│   └── TUTORIAL.md            # tutorial do ÚLTIMO passo entregue (substituído a cada passo)
├── scripts/                   # rodar manualmente, sob demanda
│   ├── setup_dirs.sh
│   ├── create_collections.py
│   ├── ingest_document.py
│   ├── search.py               # hybrid search + rerank no global_scope
│   ├── search_web.py           # busca via SearXNG
│   ├── fetch_page.py           # fetch + extração via Crawl4AI
│   ├── web_research.py         # pipeline completo de pesquisa web
│   ├── build_sandbox.sh        # builda a imagem do sandbox
│   ├── generate_code.py        # gera código via Qwen3-Coder
│   └── solve_task.py           # loop completo: gera → executa → corrige
├── src/
│   ├── ingestion/               # parser, chunking, embeddings
│   ├── retrieval/                # RRF, BM25, hybrid search, reranker
│   ├── search/                   # SearXNG, Crawl4AI, multi-query
│   ├── sandbox/                  # executor Docker isolado
│   └── coding/                   # Qwen3-Coder client + loop de iteração
├── tests/                     # um teste por unidade de lógica
├── chats/                     # escopo TEMPORÁRIO — apagado junto com a conversa
├── knowledge/                 # escopo GLOBAL / PERSISTENTE
└── data/qdrant/                # storage do Qdrant
```

## 🚀 Setup rápido (do zero)

```bash
cd ~/IA-LOCAL
./scripts/setup_dirs.sh
docker compose up -d
pip install -r requirements.txt
python scripts/create_collections.py
ollama pull qwen3-embedding:4b
ollama pull qwen3-coder:30b
./scripts/build_sandbox.sh
```

<details>
<summary><strong>SearXNG (busca web) — configuração manual obrigatória na primeira vez</strong></summary>

<br>

O SearXNG bloqueia respostas em JSON por padrão. Depois do `docker compose up -d`, edite `searxng/settings.yml` (gerado automaticamente no primeiro boot):

```yaml
search:
  formats:
    - html
    - json
```

Troque `server.secret_key` pelo resultado de `openssl rand -hex 32`. Depois:

```bash
docker compose restart searxng
```

</details>

## 🧭 Como usar

**RAG — ingerir e buscar conhecimento local**

```bash
cp algum_arquivo.md knowledge/documents/
python scripts/ingest_document.py knowledge/documents/algum_arquivo.md
python scripts/search.py "sua pergunta aqui"
```

**Pesquisa web**

```bash
python scripts/web_research.py "sua query aqui"
```

**Coding Agent — gera código e executa em sandbox isolado**

```bash
python scripts/solve_task.py "somar os 10 primeiros números pares"
```

## ✅ Rodando os testes

```bash
# Rápidos, sem rede/serviço externo
python tests/test_chunking.py
python tests/test_rrf.py
python tests/test_llm_reranker_parsing.py
python tests/test_coder_client_parsing.py
python tests/test_agent_loop.py

# Precisam de serviço no ar
python tests/test_embedding_dim.py       # Ollama
python tests/test_end_to_end.py          # Ollama + Qdrant
python tests/test_searxng_client.py      # SearXNG
python tests/test_sandbox_executor.py    # Docker
python tests/test_coding_agent_e2e.py    # Ollama + Docker
```

## 📖 Documentação

- [`docs/STATUS.md`](docs/STATUS.md) — progresso detalhado por passo/fase
- [`docs/TUTORIAL.md`](docs/TUTORIAL.md) — tutorial do último passo entregue (não acumula histórico)

## Como usar arquivos novos que eu te entregar
> Toda entrega de arquivos novos vem com um `docs/TUTORIAL.md` explicando especificamente aqueles arquivos. O caminho do arquivo no card de download é o mesmo caminho dentro de `IA-LOCAL/` — se o arquivo já existe, apague o antigo antes de copiar o novo.

## ⚙️ Princípios do projeto

- **Local-first**: cloud é fallback opcional, nunca requisito.
- **Nada sem necessidade real**: nenhum componente entra "porque parece legal".
- **Sandbox sempre**: código gerado nunca roda direto na sua máquina.
- **Testado no hardware real**: nenhuma fase avança sem validação de verdade.

---

</div>
