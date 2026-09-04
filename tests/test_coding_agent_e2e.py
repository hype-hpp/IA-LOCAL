"""
Fase 04 - 4.4: Teste de integração end-to-end do Coding Agent completo.

Cobre o pipeline inteiro da fase, de ponta a ponta, com Ollama e Docker
reais — diferente do test_agent_loop.py (4.3), que testa só o CONTROLE do
loop com generate_code()/run_code() substituídos por fakes.

Pré-requisitos:
    - Docker rodando + imagem construída (./scripts/build_sandbox.sh)
    - Ollama rodando com qwen3-coder:30b puxado
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "coding"))
from agent_loop import solve_task


def main():
    print("1. Tarefa simples deve resolver rápido (idealmente na 1a tentativa)...")
    result = solve_task("calcular o fatorial de 6 e imprimir o resultado")
    assert result.success, (
        f"esperava sucesso, veio: success={result.success}, "
        f"tentativas={result.attempts_used}"
    )
    assert "720" in result.attempts[-1].result.stdout
    print(f"   [ok] Resolvido em {result.attempts_used} tentativa(s).")

    print("2. Tarefa que tende a exigir correção (arquivo inexistente)...")
    result = solve_task(
        "ler um arquivo chamado dados_inexistente_e2e.csv e imprimir a soma "
        "da coluna 'valor'",
        max_attempts=5,
    )
    # Não afirmamos que vai ter sucesso (depende de como o modelo contorna),
    # só que o loop roda de ponta a ponta sem travar e devolve um resultado
    # coerente. O comportamento de auto-correção real já foi confirmado
    # manualmente no passo 4.3 (3 tentativas até o modelo usar tempfile).
    assert result.attempts_used >= 1, "esperava pelo menos 1 tentativa registrada"
    print(
        f"   [ok] Loop rodou {result.attempts_used} tentativa(s), "
        f"success={result.success} (sem travar)."
    )

    print("3. Tarefa que exige rede (bloqueada pelo sandbox, --network none)...")
    result = solve_task(
        "sem usar bloco try/except, faça uma requisição HTTP real para "
        "https://example.com usando a biblioteca requests e imprima apenas "
        "o status code numérico da resposta (não invente nem hardcode o "
        "valor, deixe qualquer erro de conexão propagar normalmente)",
        max_attempts=2,
    )
    # Esta falha É determinística: o sandbox genuinamente não tem rede
    # (Decision 031). A primeira versão deste teste pedia só "imprimir o
    # status code", sem proibir try/except — e o Qwen3-Coder capturou a
    # exceção de conexão, imprimiu uma mensagem amigável e saiu com
    # exit_code=0, contando como "sucesso" mesmo sem cumprir a tarefa de
    # verdade (achado real, visto em teste no hardware). Proibir try/except
    # explicitamente fecha essa saída.
    assert not result.success, "esperava success=False: sandbox não tem rede (--network none)"
    assert result.attempts_used == 2, f"esperava esgotar as 2 tentativas, veio {result.attempts_used}"
    print("   [ok] Falhou como esperado (sem rede no sandbox), sem travar, sem exceção não tratada.")

    print("\nTeste end-to-end do Coding Agent (Fase 04) passou.")


if __name__ == "__main__":
    main()
