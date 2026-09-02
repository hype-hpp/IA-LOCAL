"""
Fase 03 - 3.2: Teste de integração do page_fetcher (Crawl4AI).

Requer rede e o Chromium do Crawl4AI instalado (`crawl4ai-setup` já rodado).
Usa https://example.com por ser uma página simples, estável e feita
justamente para esse tipo de teste.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "search"))
from page_fetcher import fetch_page, fetch_pages


def test_fetch_single_page():
    result = fetch_page("https://example.com")
    assert result["success"], f"esperado sucesso, veio erro: {result['error']}"
    assert result["markdown"], "markdown vazio para uma página simples é suspeito"
    assert "example" in result["markdown"].lower()
    print(f"   [ok] fetch_page: {len(result['markdown'])} caracteres extraídos.")


def test_fetch_multiple_pages():
    urls = ["https://example.com", "https://www.iana.org/help/example-domains"]
    results = fetch_pages(urls)
    assert len(results) == 2, f"esperado 2 resultados, veio {len(results)}"
    assert all("url" in r and "success" in r for r in results)
    print(f"   [ok] fetch_pages: {len(results)} resultados retornados.")


def test_fetch_invalid_url_does_not_crash():
    result = fetch_page("https://dominio-que-nao-existe-com-certeza-123456789.invalid")
    assert result["success"] is False, "URL inválida deveria falhar, não ter sucesso"
    assert result["error"] is not None
    print("   [ok] URL inválida falha graciosamente, sem quebrar o processo.")


if __name__ == "__main__":
    print("1. Testando fetch de uma única página...")
    test_fetch_single_page()
    print("2. Testando fetch de múltiplas páginas em paralelo...")
    test_fetch_multiple_pages()
    print("3. Testando URL inválida...")
    test_fetch_invalid_url_does_not_crash()
    print("\nTodos os testes do page_fetcher passaram.")
