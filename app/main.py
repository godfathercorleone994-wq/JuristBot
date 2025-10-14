import os
import sys
import logging

# ✅ CORREÇÃO CRÍTICA: Adicionar caminho absoluto
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, 'app')
sys.path.insert(0, current_dir)
sys.path.insert(0, app_dir)

# Agora importar dotenv
from dotenv import load_dotenv

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
        logger.info("🚀 Iniciando JuristBot 2.0...")
        
        # ✅ VERIFICAR IMPORTAÇÕES PRIMEIRO
        logger.info("📦 Verificando importações...")
        
        from app.core.config import Config
        logger.info("✅ app.core.config importado")
        
        from app.core.database import mongo_db
        logger.info("✅ app.core.database importado")
        
        from app.modules.ia_services import ai_service
        logger.info("✅ app.modules.ia_services importado")
        
        logger.info("✅ Importações básicas OK")
        
        # Validar configurações
        Config.validate()
        logger.info("✅ Configurações validadas")
        
        # Inicializar bot Telegram
        from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler
        from app.core.registry import module_registry
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN não configurado!")
            
        application = Application.builder().token(token).build()
        logger.info("✅ Bot Telegram inicializado")
        
        # ✅ CARREGAR MÓDULOS
        logger.info("🔧 Carregando módulos...")
        
        # Importar módulos (isso registra automaticamente os handlers)
        try:
            from app.modules import example
            logger.info("✅ Módulo example carregado")
        except Exception as e:
            logger.error(f"❌ Erro carregando example: {e}")
            
        try:
            from app.modules import legal_assistant
            logger.info("✅ Módulo legal_assistant carregado")
        except Exception as e:
            logger.error(f"❌ Erro carregando legal_assistant: {e}")
            
        try:
            from app.modules import affiliate_system
            logger.info("✅ Módulo affiliate_system carregado")
        except Exception as e:
            logger.error(f"❌ Erro carregando affiliate_system: {e}")
            
        try:
            from app.modules import process_consultation
            logger.info("✅ Módulo process_consultation carregado")
        except Exception as e:
            logger.error(f"❌ Erro carregando process_consultation: {e}")
            
        try:
            from app.modules import admin
            logger.info("✅ Módulo admin carregado")
        except Exception as e:
            logger.error(f"❌ Erro carregando admin: {e}")
            
        try:
            from app.modules import juristcoach
            logger.info("✅ Módulo juristcoach carregado")
        except Exception as e:
            logger.error(f"❌ Erro carregando juristcoach: {e}")
        
        logger.info("✅ Módulos importados")
        
        # Registrar handlers dos módulos
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
        
        # Configurar comandos do bot
        commands_list = module_registry.get_commands()
        if commands_list:
            from telegram import BotCommand
            bot_commands = [BotCommand(cmd, desc) for cmd, desc in commands_list]
            application.bot.set_my_commands(bot_commands)
        
        logger.info(f"✅ {len(commands_list)} comandos registrados")
        logger.info(f"✅ {len(module_registry.get_loaded_modules())} módulos carregados")
        
        # Configurar webhook para Render
        webhook_url = os.getenv('RENDER_WEBHOOK_URL')
        if webhook_url:
            logger.info(f"🌐 Configurando webhook: {webhook_url}")
            application.run_webhook(
                listen="0.0.0.0",
                port=int(os.getenv('PORT', 8443)),
                url_path=token,
                webhook_url=f"{webhook_url}/{token}",
                secret_token=os.getenv('WEBHOOK_SECRET', 'juristbot_secret')
            )
        else:
            logger.info("🔄 Modo polling ativado")
            application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
            
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
        # Log detalhado para debugging
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise

if __name__ == '__main__':
    main()
