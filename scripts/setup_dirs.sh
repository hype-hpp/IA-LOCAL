#!/usr/bin/env bash
# Fase 02 - 2.1: Fundação de armazenamento (Decision 018)
# Cria a separação física entre escopo do chat (temporário) e escopo global (persistente)

set -euo pipefail

# Raiz do projeto = uma pasta acima de scripts/, independente de onde o script é chamado
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

echo "Criando estrutura em: $BASE_DIR"

# Escopo do Chat (temporário, apagado junto com o chat)
mkdir -p "$BASE_DIR/chats"

# Escopo Global (persistente, alimentado via /save ou UI)
mkdir -p "$BASE_DIR/knowledge/documents"
mkdir -p "$BASE_DIR/knowledge/cache"

# Dados do Qdrant (volume do docker-compose)
mkdir -p "$BASE_DIR/data/qdrant"

# Arquivo de exemplo para deixar claro o padrão de um chat_id
mkdir -p "$BASE_DIR/chats/.exemplo_chat_id"
touch "$BASE_DIR/chats/.exemplo_chat_id/.gitkeep"

# .gitignore básico para não versionar dados grandes
cat > "$BASE_DIR/.gitignore" <<'EOF'
data/
chats/*
!chats/.gitkeep
knowledge/cache/
*.pyc
__pycache__/
.env
EOF
touch "$BASE_DIR/chats/.gitkeep"

echo "Estrutura criada:"
tree -L 3 "$BASE_DIR/chats" "$BASE_DIR/knowledge" "$BASE_DIR/data" 2>/dev/null || \
  find "$BASE_DIR/chats" "$BASE_DIR/knowledge" "$BASE_DIR/data" -maxdepth 3
