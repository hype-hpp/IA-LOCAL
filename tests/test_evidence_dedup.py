"""
Fase 03 - 3.3: Teste da lógica pura de montagem de evidências.
Sem rede, sem Qdrant, sem Ollama. Roda rápido e não deveria quebrar nunca sozinho.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from evidence import build_evidence_chunks, content_hash


def main():
    # Caso 1: páginas com falha no fetch são ignoradas
    fetch_results = [
        {"url": "https://a.com", "success": False, "title": None, "markdown": None, "error": "timeout"},
        {"url": "https://b.com", "success": True, "title": "B", "markdown": "conteúdo válido " * 50},
    ]
    chunks = build_evidence_chunks(fetch_results, query="teste")
    assert len(chunks) >= 1, "página válida deveria gerar ao menos 1 chunk"
    assert all(c["source_url"] == "https://b.com" for c in chunks), "página com falha não deveria gerar chunk"
    print("[ok] Páginas com falha no fetch são ignoradas.")

    # Caso 2: markdown vazio/só espaço é ignorado
    fetch_results = [{"url": "https://c.com", "success": True, "title": "C", "markdown": "   \n  "}]
    chunks = build_evidence_chunks(fetch_results, query="teste")
    assert chunks == [], "markdown vazio não deveria gerar chunk"
    print("[ok] Markdown vazio é ignorado.")

    # Caso 3: content_hash é determinístico e sensível ao conteúdo
    h1 = content_hash("mesmo texto")
    h2 = content_hash("mesmo texto")
    assert h1 == h2, "hash do mesmo texto deveria ser igual"
    h3 = content_hash("texto diferente")
    assert h1 != h3, "hash de textos diferentes deveria ser diferente"
    print("[ok] content_hash é determinístico e sensível ao conteúdo.")

    # Caso 4: metadata correta propagada + reaproveita chunking.py para textos grandes
    fetch_results = [{"url": "https://d.com", "success": True, "title": "D Title", "markdown": "texto " * 300}]
    chunks = build_evidence_chunks(fetch_results, query="minha query")
    assert len(chunks) > 1, "texto grande deveria gerar múltiplos chunks (reaproveitando chunking.py)"
    assert all(c["query"] == "minha query" and c["title"] == "D Title" for c in chunks)
    print(f"[ok] Metadata propagada corretamente ({len(chunks)} chunks de um texto grande).")

    # Caso 5: lista de fetch vazia não quebra
    chunks = build_evidence_chunks([], query="teste")
    assert chunks == [], "lista vazia deveria retornar lista vazia"
    print("[ok] Lista de fetch vazia tratada corretamente.")

    print("\nTodos os testes de evidência (lógica pura) passaram.")


if __name__ == "__main__":
    main()
