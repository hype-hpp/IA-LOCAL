# Tutorial — Passo 2.5 (Hybrid Search: dense + BM25 + RRF)

Este arquivo explica só os arquivos entregues nesta etapa. Para setup geral do zero, veja o `README.md`.

## O que foi entregue

| Arquivo | Onde colocar | O que faz |
|---|---|---|
| `fusion.py` | `src/retrieval/fusion.py` | Combina duas listas rankeadas (dense + sparse) em uma só, via Reciprocal Rank Fusion |
| `bm25_index.py` | `src/retrieval/bm25_index.py` | Monta um índice de busca por palavra-chave (BM25) em memória, a partir do `global_scope` |
| `hybrid_search.py` | `src/retrieval/hybrid_search.py` | Orquestra tudo: busca por significado (dense) + busca por palavra-chave (BM25) + fusão |
| `search.py` | `scripts/search.py` | Script que você roda no terminal para fazer uma busca de verdade |
| `test_rrf.py` | `tests/test_rrf.py` | Testa a lógica de fusão isoladamente, sem precisar de Qdrant nem Ollama |

## Como rodar

```bash
cd ~/IA-LOCAL

# 1. Nova dependência: instale antes de tudo
pip install -r requirements.txt

# 2. Teste rápido, sem rede — confirma que a lógica de fusão está correta
python tests/test_rrf.py

# 3. Se ainda não ingeriu nenhum documento, faça isso primeiro (senão a busca vem vazia)
python scripts/ingest_document.py knowledge/documents/algum_arquivo.md

# 4. Busca de verdade
python scripts/search.py "sua pergunta aqui"
```

## O que esperar no terminal

`test_rrf.py` deve imprimir 4 linhas de `[ok]` e terminar com "Todos os testes de RRF passaram."

`search.py` deve imprimir algo assim:

```
1. [score=0.0328] fonte=algum_arquivo.md
   Aqui vem um trecho do texto encontrado...

2. [score=0.0301] fonte=outro_arquivo.md
   ...
```

O `score` é só um número relativo pra ordenar — não é "porcentagem de certeza".

## Checklist de validação

- [ ] `test_rrf.py` passa todos os asserts
- [ ] `search.py` com uma pergunta relacionada a um documento já ingerido retorna esse documento entre os resultados
- [ ] Rodar a mesma busca duas vezes dá resultado consistente (BM25 é determinístico, dense também)

## Decisões desta etapa

- BM25 em memória (`rank_bm25`), reconstruído a cada busca — não sparse vectors nativos do Qdrant. Simplicidade > otimização prematura, dado o tamanho do seu acervo pessoal.
- Fusão via RRF (k=60), não normalização de score entre dense e sparse.

## Próximo passo

2.6 — Reranker (ainda escolhendo o modelo, será validado antes de entregar código).
