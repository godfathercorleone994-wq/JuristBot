import logging
import re
import httpx
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.core.registry import module_registry
from app.core.database import mongo_db
from app.core.config import Config
from app.modules.affiliate_system import affiliate_system

logger = logging.getLogger(__name__)

class ProcessConsultation:
    def __init__(self):
        # APIs de consulta de processos (exemplos)
        self.apis = {
            'tjsp': 'https://api.tjsp.jus.br/v1/processos',
            'tjmg': 'https://api.tjmg.jus.br/v1/processos',
            'tjrs': 'https://api.tjrs.jus.br/v1/processos'
        }
        
        # Padrões de números de processo
        self.process_patterns = {
            'cnj': r'^\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}$',
            'tjsp': r'^\d{7}-\d{2}\.\d{4}\.\d{1,2}\.\d{2}\.\d{4}$',
            'custom': r'^\d{4}\.\d{3}\.\d{6}-\d{1}$'
        }
    
    def validate_cpf(self, cpf: str) -> bool:
        """Validar CPF brasileiro"""
        # Remover caracteres não numéricos
        cpf = re.sub(r'\D', '', cpf)
        
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Validar primeiro dígito verificador
        sum = 0
        for i in range(9):
            sum += int(cpf[i]) * (10 - i)
        remainder = sum % 11
        digit1 = 0 if remainder < 2 else 11 - remainder
        
        if digit1 != int(cpf[9]):
            return False
        
        # Validar segundo dígito verificador
        sum = 0
        for i in range(10):
            sum += int(cpf[i]) * (11 - i)
        remainder = sum % 11
        digit2 = 0 if remainder < 2 else 11 - remainder
        
        return digit2 == int(cpf[10])
    
    def format_cpf(self, cpf: str) -> str:
        """Formatar CPF para exibição"""
        cpf = re.sub(r'\D', '', cpf)
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    def validate_process_number(self, process_number: str) -> Dict:
        """Validar e identificar tipo de número de processo"""
        process_number = process_number.strip().upper()
        
        for process_type, pattern in self.process_patterns.items():
            if re.match(pattern, process_number):
                return {
                    'valid': True,
                    'type': process_type,
                    'formatted': process_number
                }
        
        return {'valid': False, 'type': 'invalid', 'formatted': process_number}
    
    async def consult_by_cpf(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Consultar processos por CPF"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "🔍 **Consulta de Processos por CPF**\n\n"
                "💡 **Uso:** /consultarcpf <CPF>\n\n"
                "Exemplo:\n"
                "`/consultarcpf 123.456.789-00`\n"
                "`/consultarcpf 12345678900`\n\n"
                "⚠️ *A consulta segue a legislação de proteção de dados.*",
                parse_mode='Markdown'
            )
            return
        
        cpf_input = " ".join(context.args)
        
        if not self.validate_cpf(cpf_input):
            await update.message.reply_text(
                "❌ CPF inválido. Por favor, insira um CPF válido com 11 dígitos.\n\n"
                "Exemplos válidos:\n"
                "• 123.456.789-00\n"
                "• 12345678900"
            )
            return
        
        cpf_clean = re.sub(r'\D', '', cpf_input)
        cpf_formatted = self.format_cpf(cpf_clean)
        
        await update.message.reply_text(f"🔍 Consultando processos para CPF: `{cpf_formatted}`...", parse_mode='Markdown')
        
        # Simular consulta (substituir por API real)
        processes = await self.mock_consult_by_cpf(cpf_clean)
        
        if processes:
            response = f"📄 **Processos encontrados para CPF {cpf_formatted}:**\n\n"
            
            for i, process in enumerate(processes, 1):
                response += (
                    f"**Processo {i}:**\n"
                    f"• Número: `{process['numero']}`\n"
                    f"• Tribunal: {process['tribunal']}\n"
                    f"• Assunto: {process['assunto']}\n"
                    f"• Situação: {process['situacao']}\n"
                    f"• Última movimentação: {process['ultima_movimentacao']}\n"
                    f"• Valor da causa: {process.get('valor_causa', 'Não informado')}\n\n"
                )
            
            response += "💡 *Use /consultarprocesso <número> para detalhes completos.*"
            
            # Registrar conversão para afiliados
            await affiliate_system.record_conversion(user_id, 'process_consultation', 25.0)
            
        else:
            response = f"❌ Nenhum processo encontrado para o CPF `{cpf_formatted}`."
        
        # Log da consulta
        mongo_db.log_query(user_id, 'cpf_consultation', cpf_formatted, response[:200] + "..." if len(response) > 200 else response)
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def consult_by_process(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Consultar processo por número"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "⚖️ **Consulta de Processo**\n\n"
                "💡 **Uso:** /consultarprocesso <número do processo>\n\n"
                "Exemplos:\n"
                "`/consultarprocesso 0001234-56.2023.8.26.0100`\n"
                "`/consultarprocesso 1234567-89.2023.8.26.0100`\n\n"
                "📝 *Formatos aceitos: CNJ, TJSP, customizado*",
                parse_mode='Markdown'
            )
            return
        
        process_number = " ".join(context.args)
        validation = self.validate_process_number(process_number)
        
        if not validation['valid']:
            await update.message.reply_text(
                "❌ Número de processo inválido.\n\n"
                "💡 **Formatos válidos:**\n"
                "• CNJ: 0001234-56.2023.8.26.0100\n"
                "• TJSP: 1234567-89.2023.8.26.0100\n"
                "• Custom: 2023.001.123456-7"
            )
            return
        
        await update.message.reply_text(f"🔍 Consultando processo: `{validation['formatted']}`...", parse_mode='Markdown')
        
        # Simular consulta detalhada
        process_details = await self.mock_consult_process_details(validation['formatted'])
        
        if process_details:
            response = (
                f"⚖️ **Processo: {process_details['numero']}**\n\n"
                f"📋 **Detalhes:**\n"
                f"• Tribunal: {process_details['tribunal']}\n"
                f"• Classe: {process_details['classe']}\n"
                f"• Assunto: {process_details['assunto']}\n"
                f"• Situação: {process_details['situacao']}\n"
                f"• Distribuição: {process_details['distribuicao']}\n"
                f"• Valor: {process_details.get('valor_causa', 'Não informado')}\n\n"
                
                f"👥 **Partes:**\n"
            )
            
            for parte in process_details['partes'][:4]:  # Limitar a 4 partes
                response += f"• {parte['tipo']}: {parte['nome']}\n"
            
            if len(process_details['partes']) > 4:
                response += f"• ... e mais {len(process_details['partes']) - 4} partes\n"
            
            response += f"\n📅 **Últimas Movimentações:**\n"
            for mov in process_details['movimentacoes'][:3]:  # Últimas 3 movimentações
                response += f"• {mov['data']}: {mov['descricao']}\n"
            
            # Registrar conversão para afiliados
            await affiliate_system.record_conversion(user_id, 'process_consultation', 35.0)
            
        else:
            response = f"❌ Processo `{validation['formatted']}` não encontrado."
        
        # Log da consulta
        mongo_db.log_query(user_id, 'process_consultation', validation['formatted'], response[:200] + "..." if len(response) > 200 else response)
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def mock_consult_by_cpf(self, cpf: str) -> List[Dict]:
        """Simular consulta por CPF (substituir por API real)"""
        # Dados mock para demonstração
        mock_data = {
            "12345678900": [
                {
                    "numero": "0001234-56.2023.8.26.0100",
                    "tribunal": "TJSP - São Paulo",
                    "assunto": "Ação de Indenização por Danos Morais",
                    "situacao": "Em andamento",
                    "ultima_movimentacao": "15/10/2023 - Julgamento",
                    "valor_causa": "R$ 50.000,00"
                },
                {
                    "numero": "0005678-90.2022.8.26.0200", 
                    "tribunal": "TJSP - São Paulo",
                    "assunto": "Execução de Título Extrajudicial",
                    "situacao": "Concluído",
                    "ultima_movimentacao": "20/12/2022 - Arquivo",
                    "valor_causa": "R$ 25.000,00"
                }
            ],
            "98765432100": [
                {
                    "numero": "2023.001.123456-7",
                    "tribunal": "TJMG - Minas Gerais", 
                    "assunto": "Ação Trabalhista",
                    "situacao": "Em andamento",
                    "ultima_movimentacao": "10/11/2023 - Audiência",
                    "valor_causa": "R$ 30.000,00"
                }
            ]
        }
        
        return mock_data.get(cpf, [])
    
    async def mock_consult_process_details(self, process_number: str) -> Optional[Dict]:
        """Simular consulta detalhada de processo (substituir por API real)"""
        mock_details = {
            "0001234-56.2023.8.26.0100": {
                "numero": "0001234-56.2023.8.26.0100",
                "tribunal": "TJSP - São Paulo",
                "classe": "Ação de Indenização por Danos Morais",
                "assunto": "Indenização por Danos Morais",
                "situacao": "Em andamento",
                "distribuicao": "15/03/2023 - Distribuição por sorteio",
                "valor_causa": "R$ 50.000,00",
                "partes": [
                    {"tipo": "Autor", "nome": "João Silva"},
                    {"tipo": "Réu", "nome": "Empresa XYZ Ltda"},
                    {"tipo": "Advogado", "nome": "Dr. Carlos Santos"},
                    {"tipo": "Advogado", "nome": "Dra. Maria Oliveira"}
                ],
                "movimentacoes": [
                    {"data": "15/10/2023", "descricao": "Julgamento - Aguardando despacho"},
                    {"data": "10/09/2023", "descricao": "Audiência de Conciliação - Não houve acordo"},
                    {"data": "15/03/2023", "descricao": "Distribuição por sorteio"}
                ]
            }
        }
        
        return mock_details.get(process_number)

# Instância global do sistema de consulta
process_consultation = ProcessConsultation()

# Registrar comandos
module_registry.register_command("consultarcpf", process_consultation.consult_by_cpf, "Consultar processos por CPF")
module_registry.register_command("consultarprocesso", process_consultation.consult_by_process, "Consultar processo por número")

module_registry.register_module("process_consultation")
