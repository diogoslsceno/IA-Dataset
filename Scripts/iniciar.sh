#!/usr/bin/env bash
# ==============================================================================
# Script de Inicialização da Aplicação WordGen / NEES (IA - Dataset)
# Compatível com Linux e macOS
# ==============================================================================

echo "=================================================================="
echo "    INICIALIZANDO PLATAFORMA WORDGEN · IA - DATASET              "
echo "=================================================================="

# 1. Determina diretório base
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/../dashboard" ]; then
    BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -d "$SCRIPT_DIR/dashboard" ]; then
    BASE_DIR="$SCRIPT_DIR"
elif [ -d "$SCRIPT_DIR/IA - Dataset/dashboard" ]; then
    BASE_DIR="$SCRIPT_DIR/IA - Dataset"
else
    BASE_DIR="$SCRIPT_DIR"
fi

# 2. Localiza o Python
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "ERRO: Python não encontrado no sistema. Por favor instale o Python 3.9+."
    exit 1
fi

echo "[1/3] Python detectado: $($PY_CMD --version)"

# 3. Verifica status do Ollama (opcional)
if curl -s http://127.0.0.1:11434/api/tags &>/dev/null; then
    echo "[2/3] Serviço Ollama (Llama 3.2): ONLINE (Aceleração Neural Ativa)"
else
    echo "[2/3] Serviço Ollama não detectado: MODO ANALÍTICO LOCAL ATIVO"
    echo "      (Dica: Para habilitar o Llama 3.2 3B neural, execute 'ollama serve' em outro terminal)"
fi

# 4. Inicia Servidor Integrado
echo "[3/3] Iniciando Servidor HTTP e Chatbot na porta 8765..."
echo "------------------------------------------------------------------"
echo "Acesse no navegador: http://localhost:8765/dist/"
echo "Pressione CTRL+C para encerrar o servidor a qualquer momento."
echo "------------------------------------------------------------------"

# Tenta abrir o navegador automaticamente em background
if command -v xdg-open &>/dev/null; then
    (sleep 1 && xdg-open "http://localhost:8765/dist/" &>/dev/null) &
elif command -v open &>/dev/null; then
    (sleep 1 && open "http://localhost:8765/dist/" &>/dev/null) &
fi

exec "$PY_CMD" "$BASE_DIR/dashboard/server_com_chat.py"
