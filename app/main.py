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
        self.admin_id = int(os.getenv('ADMIN_TELEGRAM_ID', 0))
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN não configurado!")
        
        # Inicializar MongoDB
        from app.core.database import mongo_db
        self.db = mongo_db
        
        # Inicializar serviços de IA
        from app.modules.ia_services import ai_service
        self.ai_service = ai_service
        
        self.application = Application.builder().token(self.token).build()
        
    def load_modules(self):
        """Carregar módulos dinamicamente"""
        try:
            # Importar módulos (serão carregados automaticamente via registry)
            from app.core.registry import module_registry
            
            # Importar todos os módulos
            from app.modules import example, legal_assistant, affiliate_system, process_consultation, admin
            
            # Registrar handlers dos módulos
            for handler_type, handler_config in module_registry.get_handlers():
                if handler_type == 'command':
                    self.application.add_handler(CommandHandler(*handler_config))
                elif handler_type == 'message':
                    self.application.add_handler(MessageHandler(*handler_config))
                elif handler_type == 'callback':
                    self.application.add_handler(CallbackQueryHandler(*handler_config))
            
            # Registrar comandos do bot
            commands_list = module_registry.get_commands()
            if commands_list:
                from telegram import BotCommand
                bot_commands = [BotCommand(cmd, desc) for cmd, desc in commands_list]
                self.application.bot.set_my_commands(bot_commands)
            
            logger.info(f"✅ Módulos carregados: {len(module_registry.get_loaded_modules())}")
            logger.info(f"✅ Handlers registrados: {len(module_registry.get_handlers())}")
            logger.info(f"✅ Comandos configurados: {len(commands_list)}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar módulos: {e}")
            raise
    
    def setup_webhook(self):
        """Configurar webhook para Render"""
        webhook_url = os.getenv('RENDER_WEBHOOK_URL')
        if webhook_url:
            # Modo produção com webhook
            self.application.run_webhook(
                listen="0.0.0.0",
                port=int(os.getenv('PORT', 8443)),
                url_path=self.token,
                webhook_url=f"{webhook_url}/{self.token}",
                secret_token=os.getenv('WEBHOOK_SECRET', 'juristbot_secret')
            )
            logger.info("🌐 Webhook configurado para Render")
        else:
            # Modo desenvolvimento com polling
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            logger.info("🔄 Modo polling ativado (desenvolvimento)")
    
    def run(self):
        """Iniciar o bot"""
        try:
            # Validar configurações
            from app.core.config import Config
            Config.validate()
            
            # Carregar módulos
            self.load_modules()
            
            # Handler de erro global
            self.application.add_error_handler(self.error_handler)
            
            # Handler para mensagens não tratadas
            self.application.add_handler(MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.handle_unknown_message
            ))
            
            logger.info("🚀 JuristBot 2.0 iniciado com sucesso!")
            logger.info(f"👤 Admin ID: {self.admin_id}")
            logger.info(f"🗄️ MongoDB: {'Conectado' if self.db.db else 'Desconectado'}")
            logger.info(f"🤖 IA Services: DeepSeek={self.ai_service.deepseek_available}, Gemini={self.ai_service.gemini_available}, OpenAI={self.ai_service.openai_available}")
            
            self.setup_webhook()
            
        except Exception as e:
            logger.error(f"❌ Erro crítico ao iniciar bot: {e}")
            raise

    async def error_handler(self, update: Update, context):
        """Handler global de erros"""
        logger.error(f"Erro durante a atualização {update}: {context.error}")
        
        # Notificar admin sobre erros críticos
        try:
            if self.admin_id:
                error_msg = f"❌ Erro no bot: {context.error}"
                await context.bot.send_message(chat_id=self.admin_id, text=error_msg)
        except Exception as e:
            logger.error(f"Erro ao notificar admin: {e}")

    async def handle_unknown_message(self, update: Update, context):
        """Handler para mensagens não reconhecidas"""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        logger.info(f"Mensagem não tratada de {user_id}: {user_message}")
        
        response = (
            "🤖 Olá! Sou o JuristBot, seu assistente jurídico inteligente.\n\n"
            "💡 **Comandos disponíveis:**\n"
            "/start - Iniciar conversa\n"
            "/ajuda - Ver todos os comandos\n"
            "/direito <pergunta> - Consulta jurídica\n"
            "/consultarcpf <CPF> - Consultar processos por CPF\n"
            "/consultarprocesso <numero> - Consultar processo\n"
            "/afiliado - Tornar-se afiliado\n\n"
            "Escolha um comando para continuar!"
        )
        
        await update.message.reply_text(response)

def main():
    """Função principal"""
    try:
        bot = JuristBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrompido pelo usuário")
    except Exception as e:
        logger.critical(f"Falha crítica: {e}")
        # Tentar notificar admin se possível
        import os
        admin_id = os.getenv('ADMIN_TELEGRAM_ID')
        if admin_id:
            # Aqui poderia tentar enviar uma mensagem direta se o bot estiver configurado
            pass

if __name__ == '__main__':
    main()
