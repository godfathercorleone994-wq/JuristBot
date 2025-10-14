from telegram import Update
from telegram.ext import ContextTypes
from app.core.registry import module_registry
from app.core.database import mongo_db
from app.core.config import Config

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando start com informações do sistema"""
    user = update.effective_user
    user_id = user.id
    
    # Registrar usuário
    user_data = {
        'user_id': user_id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'language_code': user.language_code,
        'is_bot': user.is_bot
    }
    mongo_db.insert_user(user_data)
    
    # Obter estatísticas do usuário
    stats = mongo_db.get_user_stats(user_id)
    
    welcome_text = f"""
👨‍⚖️ **Bem-vindo ao {Config.BOT_NAME}, {user.first_name}!**

Sou seu assistente jurídico inteligente com integração de IA.

🤖 **Funcionalidades:**
• Consultas jurídicas com IA
• Análise de documentos
• Consulta de processos
• Sistema de afiliados
• Painel administrativo

📊 **Seu uso:** {stats['total_queries']} consultas
📅 **Hoje:** {stats['today_queries']} consultas

💡 **Comandos principais:**
/ajuda - Ver todos os comandos
/direito <pergunta> - Consulta jurídica
/analisar - Analisar documento
/consultar - Consultar processo
/status - Ver status do sistema

⚡ **APIs de IA disponíveis:** {', '.join(Config.get_available_ia_apis()) or 'Nenhuma'}
    """
    
    await update.message.reply_text(welcome_text)

async def ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando ajuda com lista dinâmica de comandos"""
    commands = module_registry.get_commands()
    
    if not commands:
        text = "❌ Nenhum comando registrado no momento."
    else:
        text = "📋 **Comandos disponíveis:**\n\n" + "\n".join(
            f"• `/{cmd}` - {desc}" for cmd, desc in commands
        )
    
    text += "\n\n💡 *Use os comandos com os parâmetros indicados.*"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status do sistema"""
    from app.modules.ia_services import ai_service
    
    status_info = f"""
🔄 **Status do Sistema**

🤖 **Bot:** {Config.BOT_NAME}
🗄️ **MongoDB:** {'✅ Conectado' if mongo_db.is_connected else '❌ Desconectado'}
👤 **Usuário:** {update.effective_user.first_name}

🤖 **APIs de IA:**
• DeepSeek: {'✅' if ai_service.deepseek_available else '❌'}
• Gemini: {'✅' if ai_service.gemini_available else '❌'} 
• OpenAI: {'✅' if ai_service.openai_available else '❌'}

📊 **Módulos carregados:** {len(module_registry.get_loaded_modules())}
🛠️ **Handlers ativos:** {len(module_registry.get_handlers())}
    """
    
    await update.message.reply_text(status_info)

# Registrar comandos base
module_registry.register_command("start", start, "Iniciar o bot e ver informações")
module_registry.register_command("ajuda", ajuda, "Ver todos os comandos disponíveis")
module_registry.register_command("status", status, "Ver status do sistema")

# Registrar que este módulo foi carregado
module_registry.register_module("example")
