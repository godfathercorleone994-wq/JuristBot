#!/bin/bash
set -o errexit

echo "🚀 Iniciando build do JuristBot 2.0..."

# Instalar dependências
echo "📦 Instalando dependências Python..."
pip install -r requirements.txt

# Criar diretórios necessários
echo "📁 Criando estrutura de diretórios..."
mkdir -p app/data app/logs

# Verificar Python
echo "🐍 Versão do Python:"
python --version

echo "✅ Build concluído com sucesso!"
