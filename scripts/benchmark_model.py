"""
Benchmark de velocidade para candidatos a modelo orquestrador/especialista.

Mesmo formato usado nos benchmarks já registrados em 07_BENCHMARKS.md para
gpt-oss:20b, qwen3-coder:30b e qwen3.6:27b: tok/s em três tamanhos de
contexto (2K, 16K, 64K), mais o offload GPU/CPU reportado pelo próprio Ollama.

Uso:
    python scripts/benchmark_model.py qwen3.8:27b
    python scripts/benchmark_model.py qwen3.8:27b --contexts 2048 16384 65536

Pré-requisito: já ter rodado `ollama pull <modelo>`.

O que este script NÃO faz:
    Avaliação de qualidade. Isso continua sendo o processo manual já usado
    pro resto da tabela (notas 0-5 por categoria: instruções, raciocínio,
    coding, pesquisa factual, escrita, uso de ferramentas, análise multimodal).
"""

import os
import argparse
import subprocess

import requests

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_CONTEXTS = [2048, 16384, 65536]
GENERATION_TOKENS = 200  # fixo, pra comparação justa entre contextos


def build_padding_prompt(target_tokens: int) -> str:
    """
    Gera um prompt longo o bastante pra preencher ~target_tokens de entrada.
    Aproximação grosseira (a relação token/palavra varia por modelo e idioma),
    por isso superestimamos o corpo repetido — o valor real processado vem
    de volta em `prompt_eval_count` e é o que reportamos, não este alvo.
    """
    instrucao = (
        "Resuma o texto abaixo em português, focando nos pontos técnicos. "
    )
    trecho = (
        "O sistema de recuperação híbrida combina busca densa via embeddings "
        "com busca esparsa via BM25, fundindo os dois rankings com Reciprocal "
        "Rank Fusion antes de aplicar um reranker. "
    )
    corpo = trecho * (target_tokens // 25 + 1)
    return instrucao + corpo


def get_offload_info(model: str) -> str:
    """Lê `ollama ps` e retorna a linha correspondente ao modelo (mostra % CPU/GPU)."""
    try:
        result = subprocess.run(
            ["ollama", "ps"], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if model in line:
                return line.strip()
        return "(modelo não apareceu em 'ollama ps' — já descarregou da memória?)"
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return f"(não foi possível rodar 'ollama ps': {e})"


def run_single_test(model: str, context: int) -> dict:
    prompt = build_padding_prompt(context)

    resp = requests.post(
        f"{OLLAMA_HOST}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": context,
                "num_predict": GENERATION_TOKENS,
                "temperature": 0,
            },
        },
        timeout=600,
    )
    resp.raise_for_status()
    data = resp.json()

    eval_count = data.get("eval_count", 0)
    eval_duration_ns = data.get("eval_duration", 1)
    tok_s = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns else 0.0

    return {
        "context_requested": context,
        "prompt_tokens_real": data.get("prompt_eval_count", 0),
        "eval_count": eval_count,
        "tok_s": round(tok_s, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark de velocidade de um modelo Ollama")
    parser.add_argument("model", help="Tag do modelo no Ollama (ex: qwen3.8:27b)")
    parser.add_argument(
        "--contexts",
        type=int,
        nargs="+",
        default=DEFAULT_CONTEXTS,
        help=f"Tamanhos de contexto a testar (padrão: {DEFAULT_CONTEXTS})",
    )
    args = parser.parse_args()

    print(f"Benchmark de velocidade: {args.model}")
    print(f"Ollama host: {OLLAMA_HOST}")
    print(f"(pressupõe que 'ollama pull {args.model}' já foi rodado)\n")

    results = []
    for ctx in args.contexts:
        print(f"--- Contexto alvo: {ctx} ---")
        r = run_single_test(args.model, ctx)
        r["offload"] = get_offload_info(args.model)
        results.append(r)

        print(f"  Prompt real processado: ~{r['prompt_tokens_real']} tokens")
        print(f"  Tokens gerados:         {r['eval_count']}")
        print(f"  Velocidade:             {r['tok_s']} tok/s")
        print(f"  Offload (ollama ps):    {r['offload']}\n")

    print("=" * 60)
    print("Resumo pronto pra colar em 07_BENCHMARKS.md:\n")
    print(f"### {args.model}\n")
    print("| Contexto | tok/s |")
    print("|---:|---:|")
    for r in results:
        print(f"| {r['context_requested']} | {r['tok_s']} |")

    print("\nOffload observado por contexto:")
    for r in results:
        print(f"- {r['context_requested']}: {r['offload']}")

    print(
        "\nLembrete: isso cobre só velocidade. A avaliação de qualidade "
        "continua manual — mesmas categorias e escala 0-5 já usadas pro "
        "resto da tabela em 07_BENCHMARKS.md."
    )


if __name__ == "__main__":
    main()
