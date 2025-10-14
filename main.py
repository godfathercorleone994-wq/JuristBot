import os
import sys
import logging
from dotenv import load_dotenv

# ✅ ADICIONAR CAMINHO para importar módulos do app
sys.path.append(os.path.dirname(__file__))

# Carregar configurações
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Função principal"""
    try:
        # ✅ VERIFICAR IMPORTAÇÕES
        from app.core.config import Config
        from app.core.database import mongo_db
        from app.modules.ia_services import ai_service
        
        # Validar configurações
        Config.validate()
        
        logger.info("✅ Todas as importações funcionaram!")
        logger.info(f"🗄️ MongoDB: {'Conectado' if mongo_db.is_connected else 'Desconectado'}")
        logger.info(f"🤖 IA Services: DeepSeek={ai_service.deepseek_available}")
        
        # Iniciar bot Telegram
        from telegram.ext import Application
        from app.core.registry import module_registry
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        application = Application.builder().token(token).build()
        
        # Carregar módulos
        from app.modules import example, legal_assistant, affiliate_system, process_consultation, admin, juristcoach
        
        # Registrar handlers
        for handler_type, handler_config in module_registry.get_handlers():
            if handler_type == 'command':
                application.add_handler(CommandHandler(*handler_config))
            elif handler_type == 'message':
                application.add_handler(MessageHandler(*handler_config))
            elif handler_type == 'callback':
                application.add_handler(CallbackQueryHandler(*handler_config))
        
        # Registrar Conversation Handlers
        for conversation_handler in module_registry.get_conversation_handlers():
            application.add_handler(conversation_handler)
        
        # Configurar webhook
        webhook_url = os.getenv('RENDER_WEBHOOK_URL')
        if webhook_url:
            logger.info(f"🌐 Configurando webhook: {webhook_url}")
            application.run_webhook(
                listen="0.0.0.0",
                port=int(os.getenv('PORT', 8443)),
                url_path=token,
                webhook_url=f"{webhook_url}/{token}"
            )
        else:
            logger.info("🔄 Usando polling...")
            application.run_polling()
            
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {e}")
        raise

if __name__ == '__main__':
    main()
