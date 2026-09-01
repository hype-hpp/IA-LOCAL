"""
Fase 02 - 2.4b: Chunking de texto.

Estratégia: janela deslizante por PALAVRAS (não caracteres), para nunca
cortar uma palavra no meio. Overlap garante que contexto na borda de um
chunk não se perca completamente no chunk seguinte.

Valores padrão são um ponto de partida razoável, não uma verdade absoluta —
ajustar depois de observar qualidade de retrieval na Fase de hybrid search.
"""

DEFAULT_CHUNK_SIZE_WORDS = 250
DEFAULT_OVERLAP_WORDS = 40


def chunk_text(
    text: str,
    chunk_size_words: int = DEFAULT_CHUNK_SIZE_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
) -> list[str]:
    """Divide o texto em chunks de ~chunk_size_words palavras, com overlap_words de sobreposição."""
    if overlap_words >= chunk_size_words:
        raise ValueError("overlap_words deve ser menor que chunk_size_words")

    words = text.split()
    if not words:
        return []

    chunks = []
    step = chunk_size_words - overlap_words
    start = 0

    while start < len(words):
        end = start + chunk_size_words
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += step

    return chunks


if __name__ == "__main__":
    sample = " ".join(f"palavra{i}" for i in range(600))
    result = chunk_text(sample)
    print(f"Texto de 600 palavras gerou {len(result)} chunks.")
    for i, c in enumerate(result):
        print(f"  chunk {i}: {len(c.split())} palavras")
