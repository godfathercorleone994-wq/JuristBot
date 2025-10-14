from telegram import Update
from telegram.ext import ContextTypes
from app.core.registry import module_registry
from app.core.database import mongo_db
from app.modules.ia_services import ai_service  # ✅ AGORA ESTE IMPORT FUNCIONA

async def legal_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fornecer orientação jurídica"""
    if not context.args:
        await update.message.reply_text(
            "💡 **Uso:** /direito <sua pergunta jurídica>\n\n"
            "Exemplo: /direito Qual o prazo para abrir uma ação trabalhista?"
        )
        return
    
    user_id = update.effective_user.id
    question = " ".join(context.args)
    
    # Salvar usuário
    user_data = {
        'user_id': user_id,
        'username': update.effective_user.username,
        'first_name': update.effective_user.first_name,
        'last_name': update.effective_user.last_name
    }
    mongo_db.insert_user(user_data)
    
    await update.message.reply_text("⚖️ Analisando sua consulta jurídica...")
    
    # Obter resposta da IA
    response = await ai_service.get_legal_advice(question)
    
    # Log da consulta
    mongo_db.log_query(user_id, 'legal_advice', question, response[:200] + "..." if len(response) > 200 else response)
    
    await update.message.reply_text(response)

async def document_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analisar documento jurídico"""
    await update.message.reply_text(
        "📄 **Análise de Documentos**\n\n"
        "Envie o documento ou texto que deseja analisar.\n"
        "Em breve: integração com PDF e documentos jurídicos."
    )

# Registrar comandos jurídicos
module_registry.register_command("direito", legal_advice, "Consultar sobre questões jurídicas")
module_registry.register_command("analisar", document_analysis, "Analisar documento jurídico")

module_registry.register_module("legal_assistant")
