import os
import httpx
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from openai import OpenAI
from app.core.config import Config

logger = logging.getLogger(__name__)

class AIServiceManager:
    def __init__(self):
        self.setup_apis()
    
    def setup_apis(self):
        """Configurar todas as APIs de IA"""
        # Configurar Gemini
        if Config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.gemini_available = True
                logger.info("✅ Gemini API configurada")
            except Exception as e:
                logger.error(f"❌ Erro ao configurar Gemini: {e}")
                self.gemini_available = False
        else:
            self.gemini_available = False
            
        # Configurar OpenAI
        if Config.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
                self.openai_available = True
                logger.info("✅ OpenAI API configurada")
            except Exception as e:
                logger.error(f"❌ Erro ao configurar OpenAI: {e}")
                self.openai_available = False
        else:
            self.openai_available = False
            
        # DeepSeek
        self.deepseek_available = bool(Config.DEEPSEEK_API_KEY)
        if self.deepseek_available:
            logger.info("✅ DeepSeek API configurada")
    
    async def ask_gemini(self, prompt: str, context: str = "") -> Optional[str]:
        """Consultar Google Gemini API"""
        if not self.gemini_available:
            return None
            
        try:
            model = genai.GenerativeModel('gemini-pro')
            full_prompt = f"{context}\n\nPergunta: {prompt}" if context else prompt
            
            response = model.generate_content(full_prompt)
            return response.text if response else None
            
        except Exception as e:
            logger.error(f"Erro na API Gemini: {e}")
            return None
    
    async def ask_deepseek(self, prompt: str, context: str = "") -> Optional[str]:
        """Consultar DeepSeek API"""
        if not Config.DEEPSEEK_API_KEY:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {Config.DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": context or "Você é um assistente jurídico especializado."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result['choices'][0]['message']['content']
                else:
                    logger.error(f"Erro DeepSeek API: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erro na consulta DeepSeek: {e}")
            return None
    
    async def ask_openai(self, prompt: str, context: str = "") -> Optional[str]:
        """Consultar OpenAI API"""
        if not self.openai_available:
            return None
            
        try:
            messages = []
            if context:
                messages.append({"role": "system", "content": context})
            messages.append({"role": "user", "content": prompt})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro na API OpenAI: {e}")
            return None
    
    async def get_legal_advice(self, prompt: str, user_context: str = "") -> str:
        """Obter resposta jurídica usando a melhor API disponível"""
        context = """
        Você é um assistente jurídico especializado em direito brasileiro. 
        Forneça respostas precisas, citando legislação quando aplicável.
        Seja claro e objetivo. Se não souber algo, indique que é necessário 
        consultar um advogado para análise específica do caso.
        """
        
        # Tentar APIs em ordem de preferência
        responses = []
        
        # DeepSeek (prioridade por ser gratuito)
        response = await self.ask_deepseek(prompt, context + user_context)
        if response:
            responses.append(("DeepSeek", response))
        
        # Gemini
        if not responses:
            response = await self.ask_gemini(prompt, context + user_context)
            if response:
                responses.append(("Gemini", response))
        
        # OpenAI
        if not responses:
            response = await self.ask_openai(prompt, context + user_context)
            if response:
                responses.append(("OpenAI", response))
        
        if responses:
            source, answer = responses[0]
            return f"🔍 **Resposta ({source}):**\n\n{answer}\n\n*Fonte: {source} - Consulte um advogado para orientação específica.*"
        else:
            return "❌ Desculpe, não foi possível processar sua consulta no momento. Tente novamente mais tarde."

# Instância global do serviço de IA
ai_service = AIServiceManager()
