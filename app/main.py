import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from dotenv import load_dotenv

# Carregar configurações
load_dotenv()

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class JuristBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.admin_id = int(os.getenv('ADMIN_TELEGRAM_ID'))
        
        if not self.token:
            raise ValueError("Token do bot não configurado!")
            
        self.application = Application.builder().token(self.token).build()
        
    def load_modules(self):
        """Carregar módulos dinamicamente"""
        try:
            # Importar módulos
            from app.modules import example, legal_assistant, admin
            from app.core.registry import module_registry
            
            # Registrar handlers dos módulos
            for handler_type, handler_config in module_registry.get_handlers():
                if handler_type == 'command':
                    self.application.add_handler(CommandHandler(*handler_config))
                elif handler_type == 'message':
                    self.application.add_handler(MessageHandler(*handler_config))
                elif handler_type == 'callback':
                    self.application.add_handler(CallbackQueryHandler(*handler_config))
            
            logger.info(f"✅ Módulos carregados: {len(module_registry.get_handlers())} handlers")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar módulos: {e}")
    
    def setup_webhook(self):
        """Configurar webhook para Render"""
        webhook_url = os.getenv('RENDER_WEBHOOK_URL')
        if webhook_url:
            self.application.run_webhook(
                listen="0.0.0.0",
                port=int(os.getenv('PORT', 8443)),
                url_path=self.token,
                webhook_url=f"{webhook_url}/{self.token}"
            )
            logger.info("🌐 Webhook configurado para Render")
        else:
            self.application.run_polling()
            logger.info("🔄 Modo polling ativado")
    
    def run(self):
        """Iniciar o bot"""
        try:
            # Validar configurações
            from app.core.config import Config
            Config.validate()
            
            # Carregar módulos
            self.load_modules()
            
            # Handler de erro
            self.application.add_error_handler(self.error_handler)
            
            logger.info("🚀 JuristBot iniciado com sucesso!")
            self.setup_webhook()
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar bot: {e}")
            raise

    async def error_handler(self, update: Update, context):
        logger.error(f"Erro no bot: {context.error}")

def main():
    bot = JuristBot()
    bot.run()

if __name__ == '__main__':
    main()
