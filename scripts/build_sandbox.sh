#!/usr/bin/env bash
# Fase 04 - 4.1: Builda a imagem Docker do sandbox de execução de código.
#
# Uso:
#   ./scripts/build_sandbox.sh
#
# Rodar de novo depois de qualquer mudança em sandbox/Dockerfile.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

IMAGE_NAME="ia-local-sandbox:latest"

echo "Buildando imagem do sandbox: $IMAGE_NAME"
docker build -t "$IMAGE_NAME" -f "$BASE_DIR/sandbox/Dockerfile" "$BASE_DIR/sandbox"

echo "[ok] Imagem '$IMAGE_NAME' construída."
echo ""
echo "Teste rápido manual:"
echo "  docker run --rm --network none $IMAGE_NAME python -c \"import numpy; print(numpy.__version__)\""
