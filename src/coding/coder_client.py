"""
Fase 04 - 4.2: Client do Qwen3-Coder (gera/corrige código via Ollama).

Decision 016 do projeto: Qwen3-Coder é tratado como Tool acionada pelo
orquestrador (GPT-OSS) — recebe uma tarefa técnica, gera código, devolve
pronto para o GPT-OSS formatar a resposta final (ou, nesta fase, pronto
para ser executado pelo src/sandbox/executor.py).

Decisão de formato de saída (Fase 04, passo 4.2):
diferente do reranker (Decision 025) e do query_expansion (Decision 028),
aqui NÃO se usa grammar-constrained JSON Schema. Forçar código Python
inteiro dentro de uma string JSON exigiria escapar quebras de linha, aspas
etc., e não traz benefício real sobre simplesmente pedir um bloco de código
cercado por ```python e extrair via regex — abordagem padrão para geração
de código com LLMs e mais simples de depurar quando o modelo foge do
formato (regra 1 do projeto: não adicionar complexidade sem necessidade).

Uma única função `generate_code()` cobre os dois casos de uso:
- Gerar código novo a partir de uma tarefa em linguagem natural.
- Corrigir código anterior, dado o código + a saída de erro da execução
  (usado pelo loop de iteração do passo 4.3 — mesma função, prompt
  diferente conforme os parâmetros recebidos).
"""

import os
import re
import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
# TODO: confirmar a tag exata com `ollama list` / `ollama pull qwen3-coder:30b`
# no hardware real, mesmo processo já feito para qwen3-embedding:4b (Fase 02).
CODER_MODEL = os.environ.get("CODER_MODEL", "qwen3-coder:30b")

ALLOWED_LIBRARIES = (
    "biblioteca padrão do Python, numpy, pandas, requests, beautifulsoup4, "
    "matplotlib, scipy (as únicas pré-instaladas no sandbox de execução)"
)

CODE_FENCE_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


class CoderError(Exception):
    """
    Erro de infraestrutura (rede, parsing) ao chamar o Qwen3-Coder.
    Diferente do executor.py (Fase 04.1), aqui um erro DEVE interromper o
    chamador via exceção — não faz sentido tentar rodar uma string vazia
    no sandbox.
    """


def build_prompt(task: str, previous_code: str | None = None, error: str | None = None) -> str:
    """Monta o prompt de geração (ou correção, se previous_code/error vierem preenchidos)."""
    if previous_code is not None and error is not None:
        return (
            "Você é um assistente de programação Python. O código abaixo foi "
            "gerado para a tarefa indicada, mas falhou na execução. Corrija o "
            "código.\n\n"
            f'Tarefa original: "{task}"\n\n'
            "Código anterior:\n"
            "```python\n"
            f"{previous_code}\n"
            "```\n\n"
            "Erro/saída da execução:\n"
            "```\n"
            f"{error}\n"
            "```\n\n"
            "Regras:\n"
            "- Responda APENAS com um bloco de código Python corrigido, cercado "
            "por ```python e ```, sem nenhum texto antes ou depois.\n"
            "- O código deve poder ser executado sozinho como um script "
            "(use print() para mostrar resultados).\n"
            f"- Não use bibliotecas além de: {ALLOWED_LIBRARIES}."
        )

    return (
        "Você é um assistente de programação Python. Gere código Python que "
        "resolva a tarefa abaixo.\n\n"
        f'Tarefa: "{task}"\n\n'
        "Regras:\n"
        "- Responda APENAS com um bloco de código Python, cercado por "
        "```python e ```, sem nenhum texto antes ou depois.\n"
        "- O código deve poder ser executado sozinho como um script "
        "(use print() para mostrar resultados, não apenas retornar valores).\n"
        f"- Não use bibliotecas além de: {ALLOWED_LIBRARIES}."
    )


def extract_code(raw_text: str) -> str:
    """
    Extrai o bloco de código de dentro de cercas markdown (```python ... ```
    ou ``` ... ```). Tolerante: se o modelo não usar cercas (foge do prompt),
    assume que a resposta inteira já é código, em vez de falhar. Se houver
    mais de um bloco cercado, extrai só o primeiro.
    """
    match = CODE_FENCE_RE.search(raw_text)
    if match:
        return match.group(1).strip()
    return raw_text.strip()


def generate_code(
    task: str,
    previous_code: str | None = None,
    error: str | None = None,
    timeout: int = 120,
) -> str:
    """
    Chama o Qwen3-Coder via Ollama para gerar (task apenas) ou corrigir
    (task + previous_code + error) código Python. Levanta CoderError em
    caso de falha de rede/parsing ou resposta sem código extraível.
    """
    prompt = build_prompt(task, previous_code, error)

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": CODER_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        raw_content = resp.json()["message"]["content"]
    except (requests.RequestException, KeyError, ValueError) as e:
        raise CoderError(f"Falha ao chamar Qwen3-Coder via Ollama: {e}") from e

    code = extract_code(raw_content)
    if not code:
        raise CoderError("Qwen3-Coder retornou uma resposta vazia ou sem código extraível.")

    return code


if __name__ == "__main__":
    # smoke test manual
    generated = generate_code("Imprimir os 10 primeiros números de Fibonacci")
    print(generated)
