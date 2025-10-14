#!/bin/bash
set -o errexit

echo "🚀 Iniciando build do JuristBot 2.0..."

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r app/requirements.txt

# Criar diretórios necessários
echo "📁 Criando estrutura de diretórios..."
mkdir -p app/data app/logs

# Verificar se as variáveis de ambiente necessárias estão definidas
echo "🔧 Verificando configurações..."

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "⚠️  AVISO: TELEGRAM_BOT_TOKEN não definido!"
    echo "💡 Lembre-se de configurar no painel do Render"
fi

if [ -z "$MONGODB_URI" ]; then
    echo "⚠️  AVISO: MONGODB_URI não definido!"
    echo "💡 Configure um MongoDB Atlas ou serviço similar"
fi

if [ -z "$ADMIN_TELEGRAM_ID" ]; then
    echo "⚠️  AVISO: ADMIN_TELEGRAM_ID não definido!"
    echo "💡 Recursos administrativos estarão desativados"
fi

# Verificar APIs de IA
if [ -z "$DEEPSEEK_API_KEY" ] && [ -z "$GEMINI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  AVISO: Nenhuma API de IA configurada!"
    echo "💡 Configure pelo menos uma API de IA"
fi

echo "✅ Build concluído com sucesso!"
echo "📊 Resumo da configuração:"
echo "   • Python: $(python --version)"
echo "   • MongoDB: $([ -z "$MONGODB_URI" ] && echo "Não configurado" || echo "Configurado")"
echo "   • Telegram Bot: $([ -z "$TELEGRAM_BOT_TOKEN" ] && echo "Não configurado" || echo "Configurado")"
echo "   • APIs IA: $(if [ -n "$DEEPSEEK_API_KEY" ] || [ -n "$GEMINI_API_KEY" ] || [ -n "$OPENAI_API_KEY" ]; then echo "Configuradas"; else echo "Não configuradas"; fi)"
