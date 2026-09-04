# Tutorial — Fase 04, Passo 4.2 (Tool Qwen3-Coder)

Cobre apenas os arquivos deste passo. Histórico completo fica no `README.md`
e no `docs/STATUS.md`.

## O que foi entregue

| Arquivo | Onde colocar |
|---|---|
| `src/coding/__init__.py` | `IA-LOCAL/src/coding/__init__.py` |
| `src/coding/coder_client.py` | `IA-LOCAL/src/coding/coder_client.py` |
| `tests/test_coder_client_parsing.py` | `IA-LOCAL/tests/test_coder_client_parsing.py` |
| `scripts/generate_code.py` | `IA-LOCAL/scripts/generate_code.py` |

Nada do passo 4.1 foi modificado.

## O que cada coisa faz

- **`src/coding/coder_client.py`**: função `generate_code(task, previous_code=None, error=None)`
  que chama o Qwen3-Coder via Ollama e devolve código Python pronto (string).
  Mesma função cobre os dois casos de uso, via prompt diferente conforme os
  parâmetros:
  - Só `task` → gera código novo.
  - `task` + `previous_code` + `error` → pede correção do código anterior
    (é isso que o passo 4.3, o loop de iteração, vai chamar a cada retry).

  Decisão tomada neste passo: ao contrário do reranker (Decision 025) e do
  query expansion (Decision 028), aqui **não** se usa grammar-constrained
  JSON Schema — pede-se um bloco de código cercado por ```` ```python ```` e
  extrai-se via regex (`extract_code()`). Forçar código inteiro dentro de uma
  string JSON só adicionaria complexidade de escaping sem benefício real.

  Erros de infraestrutura (rede, resposta sem código extraível) levantam
  `CoderError` — diferente do `executor.py` da 4.1, aqui faz sentido
  interromper com exceção, já que não tem o que rodar no sandbox se a
  geração falhou.

  **Atenção**: a tag do modelo está como `qwen3-coder:30b` (mesmo padrão de
  nomenclatura do `qwen3-embedding:4b`), mas isso ainda não foi confirmado
  no seu Ollama — rode `ollama list` (ou `ollama pull qwen3-coder:30b` se
  ainda não tiver puxado) e ajuste a env var `CODER_MODEL` se a tag real for
  diferente.

- **`tests/test_coder_client_parsing.py`**: testa `extract_code()` e
  `build_prompt()` sem precisar de rede nem do Ollama — cobre bloco cercado
  com/sem tag de linguagem, resposta sem cerca nenhuma (fallback), múltiplos
  blocos (extrai só o primeiro), resposta vazia, e os dois modos do prompt
  (geração nova vs. correção).

- **`scripts/generate_code.py`**: CLI manual para testar de ponta a ponta
  contra o Ollama real. Com `--run`, já executa o código gerado no sandbox
  da 4.1 e mostra o resultado — bom teste de fumaça do encadeamento
  Qwen3-Coder → executor, antes de montar o loop de iteração automática.

## Como testar

```bash
# 1. Colocar os arquivos nos caminhos da tabela acima

# 2. Teste de parsing (rápido, sem rede)
python tests/test_coder_client_parsing.py

# 3. Confirmar a tag do modelo no Ollama
ollama list | grep -i coder
# se a tag real não for qwen3-coder:30b, exporte:
# export CODER_MODEL="tag-real-aqui"

# 4. Teste real de geração (precisa do Ollama rodando com o modelo puxado)
python scripts/generate_code.py "somar os 10 primeiros números pares"

# 5. Teste real de geração + execução no sandbox
python scripts/generate_code.py "somar os 10 primeiros números pares" --run
```

## Checklist de validação

- [ ] `python tests/test_coder_client_parsing.py` termina com "Todos os testes de parsing do coder_client passaram."
- [ ] Tag do modelo confirmada via `ollama list` (ajustada via `CODER_MODEL` se necessário)
- [ ] `python scripts/generate_code.py "..."` devolve um bloco de código Python coerente com a tarefa
- [ ] `python scripts/generate_code.py "..." --run` executa o código gerado no sandbox e mostra `success=True` (para uma tarefa simples o suficiente)

## Próximo passo (4.3)

Loop de iteração: executa o código gerado → se `success=False`, manda
`code` + `result.stderr` de volta pro `generate_code()` (modo correção) →
executa de novo → repete até sucesso ou até um número máximo de tentativas.
