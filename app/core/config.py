import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ADMIN_TELEGRAM_ID = int(os.getenv('ADMIN_TELEGRAM_ID', 0))
    
    # APIs de IA
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'juristbot')
    
    # Render
    RENDER_WEBHOOK_URL = os.getenv('RENDER_WEBHOOK_URL')
    PORT = int(os.getenv('PORT', 8443))
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'juristbot_secret')
    
    # Configurações do Bot
    BOT_NAME = os.getenv('BOT_NAME', 'JuristBot 2.0')
    BOT_USERNAME = os.getenv('BOT_USERNAME', '')
    
    @classmethod
    def validate(cls):
        """Validar configurações obrigatórias"""
        required = ['TELEGRAM_BOT_TOKEN']
        missing = [var for var in required if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Variáveis de ambiente obrigatórias não configuradas: {', '.join(missing)}")
        
        if not cls.ADMIN_TELEGRAM_ID:
            print("⚠️  AVISO: ADMIN_TELEGRAM_ID não configurado - recursos administrativos desativados")
        
        # Verificar APIs de IA disponíveis
        ia_apis = []
        if cls.DEEPSEEK_API_KEY: ia_apis.append("DeepSeek")
        if cls.GEMINI_API_KEY: ia_apis.append("Gemini")
        if cls.OPENAI_API_KEY: ia_apis.append("OpenAI")
        
        if ia_apis:
            print(f"✅ APIs de IA configuradas: {', '.join(ia_apis)}")
        else:
            print("⚠️  AVISO: Nenhuma API de IA configurada - funcionalidades de IA desativadas")
    
    @classmethod
    def get_available_ia_apis(cls):
        """Retornar lista de APIs de IA disponíveis"""
        apis = []
        if cls.DEEPSEEK_API_KEY: apis.append("DeepSeek")
        if cls.GEMINI_API_KEY: apis.append("Gemini")
        if cls.OPENAI_API_KEY: apis.append("OpenAI")
        return apis
