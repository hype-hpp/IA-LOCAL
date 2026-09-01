"""
Fase 02 - 2.3a: Teste mais simples possível.
Chama o Ollama diretamente e confirma a dimensão real do embedding.

Pré-requisito: ollama pull qwen3-embedding:4b
"""

import os
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = "qwen3-embedding:4b"
EXPECTED_DIM = 2560  # confirmado via docs oficiais do Qwen3-Embedding


def main():
    print(f"Chamando {OLLAMA_HOST}/api/embed com modelo '{MODEL}' ...")
    resp = requests.post(
        f"{OLLAMA_HOST}/api/embed",
        json={"model": MODEL, "input": "teste de dimensão de embedding"},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()

    embedding = data["embeddings"][0]
    real_dim = len(embedding)

    print(f"Dimensão retornada: {real_dim}")
    print(f"Dimensão esperada (Qdrant): {EXPECTED_DIM}")

    if real_dim == EXPECTED_DIM:
        print("[ok] Dimensão bate com as collections já criadas. Nada a ajustar.")
    else:
        print("[ATENÇÃO] Dimensão diferente! As collections do Qdrant precisam "
              "ser recriadas com VECTOR_SIZE correto antes de indexar qualquer dado.")


if __name__ == "__main__":
    main()
