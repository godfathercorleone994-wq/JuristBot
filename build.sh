#!/bin/bash
set -o errexit

echo "🚀 Iniciando build do JuristBot..."

# Instalar dependências
pip install -r app/requirements.txt

# Criar diretórios necessários
mkdir -p app/data app/logs

# Verificar se as variáveis de ambiente necessárias estão definidas
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ ERRO: TELEGRAM_BOT_TOKEN não definido!"
    exit 1
fi

if [ -z "$MONGODB_URI" ]; then
    echo "⚠️  AVISO: MONGODB_URI não definido, usando MongoDB local"
fi

echo "✅ Build concluído com sucesso!"
echo "📁 Estrutura do projeto:"
find app/ -type f -name "*.py" | head -10
