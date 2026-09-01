"""
Fase 02 - 2.6: Reranker via GPT-OSS (já residente na VRAM, sem modelo extra).

Decisão (substitui a ideia original de um Qwen3-Reranker dedicado):
não existe tag oficial de reranker no Ollama, e o jeito correto de usar um
cross-encoder como o Qwen3-Reranker é via prompt + logit de "yes/no", frágil
de implementar de forma confiável pela API do Ollama. Em vez disso, usamos o
orquestrador (GPT-OSS 20B) para pontuar relevância via prompt estruturado.

Trade-off: adiciona latência de uma chamada de LLM por busca. Se isso pesar
demais na prática, é uma decisão reversível (regra 5 do projeto: medir antes
de trocar).

A lógica de parsing é isolada em parse_rerank_response() para ser testável
sem precisar de rede (ver tests/test_llm_reranker_parsing.py).
"""

import os
import json
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
RERANK_MODEL = os.environ.get("RERANK_MODEL", "gpt-oss:20b")
MAX_CHARS_PER_CANDIDATE = 400
DEBUG = os.environ.get("RERANK_DEBUG", "0") == "1"

# Schema JSON real, não só a string "json" — força a estrutura exata via
# grammar-constrained decoding do Ollama, em vez de confiar que o modelo
# vai seguir o formato descrito em texto no prompt.
RERANK_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "index": {"type": "integer"},
            "score": {"type": "number"},
        },
        "required": ["index", "score"],
    },
}


def build_prompt(query: str, candidates: list[dict]) -> str:
    """Monta o prompt de avaliação de relevância com os candidatos numerados."""
    lines = [
        "Você é um avaliador de relevância para um sistema de busca.",
        f'Pergunta do usuário: "{query}"',
        "",
        "Trechos candidatos (numerados):",
    ]
    for i, cand in enumerate(candidates):
        text = (cand.get("text") or "")[:MAX_CHARS_PER_CANDIDATE].replace("\n", " ")
        lines.append(f"[{i}] {text}")

    lines += [
        "",
        "Para cada trecho, dê uma nota de 0 a 10 indicando o quão relevante ele é "
        "para responder à pergunta. Responda APENAS com um JSON no formato exato "
        '(sem texto antes ou depois):',
        '[{"index": 0, "score": 7}, {"index": 1, "score": 2}, ...]',
        f"Inclua uma entrada para cada um dos {len(candidates)} trechos, de [0] a [{len(candidates)-1}].",
    ]
    return "\n".join(lines)


def parse_rerank_response(raw_text: str, num_candidates: int) -> dict[int, float]:
    """
    Extrai {index: score} da resposta do LLM. Tolerante a formatos levemente
    fora do esperado; ignora entradas inválidas em vez de quebrar tudo.
    Retorna dict vazio se não conseguir parsear nada (chamador deve ter fallback).
    """
    cleaned = raw_text.strip()
    # Remove cercas de código markdown, caso o modelo insista em usá-las
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return {}

    if not isinstance(data, list):
        return {}

    scores: dict[int, float] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        idx = item.get("index")
        score = item.get("score")
        if not isinstance(idx, int) or not isinstance(score, (int, float)):
            continue
        if 0 <= idx < num_candidates:
            scores[idx] = float(score)

    return scores


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Reordena candidates por relevância segundo o GPT-OSS.
    Em caso de falha total do LLM (rede, parsing), retorna os top_k
    originais na ordem que chegaram (fallback = ordem do RRF).
    """
    if not candidates:
        return []

    fallback = candidates[:top_k]

    try:
        prompt = build_prompt(query, candidates)
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": RERANK_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": RERANK_SCHEMA,
                "options": {"temperature": 0},
            },
            timeout=120,
        )
        resp.raise_for_status()
        raw_content = resp.json()["message"]["content"]
    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"[aviso] Reranker falhou ({e}), usando ordem original (RRF).")
        return fallback

    if DEBUG:
        print(f"[debug] Resposta crua do LLM: {raw_content[:500]}")

    llm_scores = parse_rerank_response(raw_content, len(candidates))

    if not llm_scores:
        print("[aviso] Reranker não retornou scores válidos, usando ordem original (RRF).")
        if not DEBUG:
            print("        (rode com RERANK_DEBUG=1 para ver a resposta crua do modelo)")
        return fallback

    # Candidatos sem score do LLM ficam no fim, mantendo ordem relativa original
    scored = [
        (i, llm_scores.get(i, -1.0), cand)
        for i, cand in enumerate(candidates)
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [cand for _, _, cand in scored[:top_k]]
