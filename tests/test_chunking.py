"""
Fase 02 - 2.4d: Teste isolado do chunking. Sem rede, sem Qdrant, sem Ollama.
Roda rápido e não deveria quebrar nunca sozinho.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "ingestion"))
from chunking import chunk_text


def main():
    # Caso 1: texto menor que um chunk -> 1 chunk só
    small_text = "uma frase pequena de teste"
    result = chunk_text(small_text, chunk_size_words=250, overlap_words=40)
    assert len(result) == 1, f"esperado 1 chunk, veio {len(result)}"
    print("[ok] Texto pequeno gera 1 chunk.")

    # Caso 2: texto maior que um chunk -> múltiplos chunks com overlap
    words = [f"w{i}" for i in range(600)]
    big_text = " ".join(words)
    result = chunk_text(big_text, chunk_size_words=250, overlap_words=40)
    assert len(result) > 1, "texto grande deveria gerar múltiplos chunks"
    print(f"[ok] Texto de 600 palavras gerou {len(result)} chunks.")

    # Verifica que o overlap realmente existe (última palavra do chunk N
    # deve aparecer perto do início do chunk N+1)
    first_chunk_words = result[0].split()
    second_chunk_words = result[1].split()
    overlap_found = any(w in second_chunk_words[:50] for w in first_chunk_words[-40:])
    assert overlap_found, "overlap entre chunks não encontrado"
    print("[ok] Overlap entre chunks confirmado.")

    # Caso 3: texto vazio -> lista vazia, sem erro
    result = chunk_text("", chunk_size_words=250, overlap_words=40)
    assert result == [], "texto vazio deveria retornar lista vazia"
    print("[ok] Texto vazio tratado corretamente.")

    print("\nTodos os testes de chunking passaram.")


if __name__ == "__main__":
    main()
