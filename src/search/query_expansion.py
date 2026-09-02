"""
Fase 03 - 3.4: Geração de variações de query via GPT-OSS.

Mesmo princípio já usado no reranker (Decision 025, Fase 02): reaproveitar
o orquestrador (GPT-OSS 20B, já residente na VRAM) como "worker" para uma
tarefa auxiliar via prompt + JSON Schema forçado (grammar-constrained
decoding do Ollama), em vez de subir lógica ou modelo dedicado.

Objetivo: cobertura melhor de busca. Uma query literal do usuário pode não
bater com os termos exatos usados nas páginas relevantes — variações
(sinônimos, termos técnicos, reformulações) aumentam a chance de achar
material bom que a query original sozinha não acharia.

Fallback: se o LLM falhar ou não retornar nada parseável, generate_query_variations
retorna lista vazia — quem chama (multi_query.py) simplesmente segue só com
a query original, sem quebrar o fluxo.
"""

import os
import json
import requests
from typing import List

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
QUERY_EXPANSION_MODEL = os.environ.get("QUERY_EXPANSION_MODEL", "gpt-oss:20b")

VARIATIONS_SCHEMA = {
    "type": "array",
    "items": {"type": "string"},
}


def build_prompt(query: str, n: int) -> str:
    return (
        "Você ajuda a melhorar buscas na web. Dada a pergunta de um usuário, "
        f"gere {n} reformulações alternativas dessa busca — sinônimos, termos "
        "técnicos relacionados, ou ângulos diferentes do mesmo tema — que "
        "ajudariam a encontrar mais páginas relevantes sobre o assunto.\n\n"
        f'Pergunta original: "{query}"\n\n'
        "Responda APENAS com um JSON no formato exato (sem texto antes ou "
        "depois, sem markdown):\n"
        '["reformulação 1", "reformulação 2", ...]\n\n'
        "Regras: mantenha o mesmo idioma da pergunta original. Não repita a "
        "pergunta original literalmente. Cada reformulação deve ser uma "
        "query de busca curta, não uma frase completa explicando o que "
        "você fez."
    )


def parse_variations_response(raw_text: str, num_variations: int) -> List[str]:
    """
    Extrai a lista de variações da resposta do LLM. Tolerante a formatos
    levemente fora do esperado; ignora entradas inválidas em vez de quebrar
    tudo. Retorna lista vazia se não conseguir parsear nada.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned

    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return []

    if not isinstance(data, list):
        return []

    variations = [item.strip() for item in data if isinstance(item, str) and item.strip()]
    return variations[:num_variations]


def generate_query_variations(query: str, n: int = 3) -> List[str]:
    """
    Gera até n variações da query via GPT-OSS. Em caso de falha (rede,
    parsing), retorna lista vazia — não é erro fatal, só significa que a
    busca vai seguir só com a query original.
    """
    try:
        prompt = build_prompt(query, n)
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": QUERY_EXPANSION_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": VARIATIONS_SCHEMA,
                "options": {"temperature": 0.7},
            },
            timeout=60,
        )
        resp.raise_for_status()
        raw_content = resp.json()["message"]["content"]
    except (requests.RequestException, KeyError, ValueError) as e:
        print(f"[aviso] Geração de variações de query falhou ({e}), seguindo só com a query original.")
        return []

    variations = parse_variations_response(raw_content, n)
    if not variations:
        print("[aviso] GPT-OSS não retornou variações válidas, seguindo só com a query original.")
    return variations
