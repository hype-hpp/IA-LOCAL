"""
Fase 02 - 2.4a: Parser de documentos.

Escopo atual: .md e .txt apenas (texto puro, sem parsing estrutural).
PDF fica para um incremento futuro, quando houver necessidade real
(regra 1 do projeto: não criar componente sem necessidade).
"""

from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".txt"}


def read_text_file(path: str) -> str:
    """Lê um arquivo de texto/markdown e retorna o conteúdo bruto."""
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Extensão '{file_path.suffix}' não suportada ainda. "
            f"Suportadas: {SUPPORTED_EXTENSIONS}"
        )

    return file_path.read_text(encoding="utf-8")
