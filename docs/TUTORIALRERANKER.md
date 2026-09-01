# Tutorial — Passo 2.6 (Reranker via GPT-OSS)

Este arquivo explica só os arquivos entregues nesta etapa. Para setup geral do zero, veja o `README.md`.

## Contexto da decisão

Não existe reranker oficial no Ollama (só builds de terceiros), e o jeito correto de usar um cross-encoder como o Qwen3-Reranker é frágil via API do Ollama. Em vez disso, usamos o **GPT-OSS 20B** (já residente na VRAM) para pontuar relevância via prompt, sem adicionar nenhum modelo novo.

## O que foi entregue

| Arquivo | Onde colocar | O que faz |
|---|---|---|
| `llm_reranker.py` | `src/retrieval/llm_reranker.py` | Monta o prompt, chama o GPT-OSS via Ollama, parseia a resposta, reordena os candidatos |
| `search.py` | `scripts/search.py` (substitui o anterior) | CLI de busca, agora com rerank ligado por padrão |
| `test_llm_reranker_parsing.py` | `tests/test_llm_reranker_parsing.py` | Testa só a lógica de parsing da resposta do LLM, sem rede |

## Como rodar

```bash
cd ~/IA-LOCAL

# 1. Teste rápido, sem rede — confirma que o parsing está correto
python tests/test_llm_reranker_parsing.py

# 2. Busca COM rerank (padrão agora)
python scripts/search.py "sua pergunta aqui"

# 3. Busca SEM rerank, pra comparar (mostra ordem crua do RRF)
python scripts/search.py "sua pergunta aqui" --no-rerank
```

## O que esperar no terminal

Com rerank, você vai ver uma linha extra antes dos resultados:

```
(15 candidatos encontrados, reordenando com GPT-OSS...)

1. [score=...] fonte=arquivo.md
   ...
```

Se o GPT-OSS falhar ou responder algo que não dá pra parsear, aparece um aviso `[aviso] Reranker falhou/não retornou scores válidos, usando ordem original (RRF).` — isso não é erro fatal, é o fallback funcionando como esperado.

## Checklist de validação

- [ ] `test_llm_reranker_parsing.py` passa todos os asserts
- [ ] `search.py` (com rerank) roda sem travar e retorna resultados
- [ ] Compare visualmente: `search.py "pergunta"` vs `search.py "pergunta" --no-rerank` — a ordem deveria mudar pelo menos um pouco se o rerank estiver fazendo algo
- [ ] Observar quanto tempo a busca com rerank demora a mais que sem rerank (latência é o trade-off desta decisão — vale a pena registrar esse número)

## Próximo passo

Com isso, a Fase 02 (RAG/Knowledge) está com todos os componentes do roadmap implementados e testados. Falta decidir: seguir pra Fase 03 (Web Search + Browser) ou revisar/otimizar algo da Fase 02 primeiro com base no que você observar no uso real.
