from telegram import Update
from telegram.ext import ContextTypes
from app.core.registry import module_registry
from app.core.database import mongo_db
from app.core.config import Config
from app.modules.affiliate_system import affiliate_system

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando start com suporte a links de afiliado"""
    user = update.effective_user
    user_id = user.id
    
    # Verificar se veio de um link de afiliado
    if context.args and len(context.args) > 0:
        affiliate_code = context.args[0]
        
        # Registrar o usuário como indicado
        users = mongo_db.get_collection('users')
        users.update_one(
            {'user_id': user_id},
            {'$set': {'referred_by': affiliate_code}},
            upsert=True
        )
        
        # Registrar a indicação no sistema de afiliados
        await affiliate_system.handle_referral(user_id, affiliate_code)
        
        welcome_affiliate = (
            f"👋 Olá {user.first_name}! Você foi indicado por um afiliado.\n\n"
            "🤖 Bem-vindo ao **JuristBot 2.0** - Seu assistente jurídico inteligente!\n\n"
            "💡 **Comece com:**\n"
            "/direito <pergunta> - Consulta jurídica\n"
            "/consultarcpf <CPF> - Consultar processos\n" 
            "/consultarprocesso <numero> - Detalhes de processo\n"
            "/analisar - Análise de documentos\n\n"
            "🎁 *Indicações especiais recebem benefícios!*"
        )
        await update.message.reply_text(welcome_affiliate, parse_mode='Markdown')
        
    else:
        # Comando start normal
        user_data = {
            'user_id': user_id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'language_code': user.language_code,
            'is_bot': user.is_bot,
            'referred_by': None
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
• Consulta de processos por CPF
• Detalhes de processos
• Sistema de afiliados
• Painel administrativo

📊 **Seu uso:** {stats['total_queries']} consultas
📅 **Hoje:** {stats['today_queries']} consultas

💡 **Comandos principais:**
/ajuda - Ver todos os comandos
/direito <pergunta> - Consulta jurídica
/consultarcpf <CPF> - Consultar processos
/consultarprocesso <numero> - Detalhes de processo
/afiliado - Tornar-se afiliado

⚡ **APIs de IA disponíveis:** {', '.join(Config.get_available_ia_apis()) or 'Nenhuma'}

💰 **Torne-se um afiliado e ganhe comissões!**
Use /afiliado para saber mais.
        """

        await update.message.reply_text(welcome_text)

# ... (outras funções do example.py permanecem iguais)
