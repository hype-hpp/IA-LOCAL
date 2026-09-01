"""
Fase 02 - 2.3b: Client reutilizável de embedding.

Módulo simples de propósito único: transformar texto em vetor via Ollama.
Será importado pelo parser/chunking (próximo passo da Fase 02) e,
futuramente, pelo pipeline de retrieval.
"""

import os
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "qwen3-embedding:4b")
EMBEDDING_DIM = 2560


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Recebe uma lista de textos e retorna uma lista de vetores (float32),
    na mesma ordem. Levanta exceção se a API do Ollama falhar.
    """
    if not texts:
        return []

    resp = requests.post(
        f"{OLLAMA_HOST}/api/embed",
        json={"model": EMBEDDING_MODEL, "input": texts},
        timeout=120,
    )
    resp.raise_for_status()
    embeddings = resp.json()["embeddings"]

    for vec in embeddings:
        if len(vec) != EMBEDDING_DIM:
            raise ValueError(
                f"Dimensão inesperada: recebido {len(vec)}, esperado {EMBEDDING_DIM}. "
                "Verifique se o modelo mudou ou se há truncamento (MRL) ativo."
            )

    return embeddings


def embed_text(text: str) -> list[float]:
    """Atalho para embedar um único texto."""
    return embed_texts([text])[0]


if __name__ == "__main__":
    # smoke test manual
    vec = embed_text("teste rápido do client de embedding")
    print(f"Vetor gerado com {len(vec)} dimensões. Primeiros 5 valores: {vec[:5]}")
