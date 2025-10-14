import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.core.registry import module_registry
from app.core.database import mongo_db
from app.core.config import Config

logger = logging.getLogger(__name__)

class AffiliateSystem:
    def __init__(self):
        self.commission_rates = {
            'legal_consultation': 0.10,  # 10% para consultas jurídicas
            'process_consultation': 0.15,  # 15% para consultas de processos
            'document_analysis': 0.20,  # 20% para análise de documentos
        }
    
    def generate_affiliate_code(self, user_id: int) -> str:
        """Gerar código de afiliado único"""
        base_code = f"JURIST{user_id:06d}"
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"{base_code}{random_suffix}"
    
    async def register_affiliate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Registrar usuário como afiliado"""
        user_id = update.effective_user.id
        user = update.effective_user
        
        # Verificar se já é afiliado
        affiliates = mongo_db.get_collection('affiliates')
        existing_affiliate = affiliates.find_one({'user_id': user_id})
        
        if existing_affiliate:
            await update.message.reply_text(
                "✅ Você já é um afiliado!\n\n"
                f"🔗 Seu código: `{existing_affiliate['affiliate_code']}`\n"
                f"💰 Comissão total: R$ {existing_affiliate.get('total_commission', 0):.2f}\n\n"
                "Use /meuafiliado para ver seu dashboard."
            )
            return
        
        # Criar novo afiliado
        affiliate_code = self.generate_affiliate_code(user_id)
        affiliate_data = {
            'user_id': user_id,
            'username': user.username,
            'first_name': user.first_name,
            'affiliate_code': affiliate_code,
            'joined_at': datetime.utcnow(),
            'status': 'active',
            'total_commission': 0,
            'pending_commission': 0,
            'paid_commission': 0,
            'referral_count': 0,
            'conversion_rate': 0,
            'last_commission_date': None
        }
        
        affiliates.insert_one(affiliate_data)
        
        # Atualizar usuário como afiliado
        users = mongo_db.get_collection('users')
        users.update_one(
            {'user_id': user_id},
            {'$set': {'is_affiliate': True, 'affiliate_code': affiliate_code}}
        )
        
        welcome_message = (
            "🎉 **Parabéns! Você agora é um afiliado do JuristBot!**\n\n"
            f"🔗 **Seu código único:** `{affiliate_code}`\n\n"
            "💸 **Sistema de Comissões:**\n"
            "• Consultas jurídicas: 10%\n"
            "• Consultas de processos: 15%\n"
            "• Análise de documentos: 20%\n\n"
            "📤 **Como divulgar:**\n"
            f"`https://t.me/{context.bot.username}?start={affiliate_code}`\n\n"
            "📊 **Comandos disponíveis:**\n"
            "/meuafiliado - Ver seu dashboard\n"
            "/linkafiliado - Gerar link personalizado\n"
            "/comissoes - Ver suas comissões\n"
            "/saque - Solicitar saque\n\n"
            "💡 *Compartilhe seu link e comece a ganhar!*"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def affiliate_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dashboard do afiliado"""
        user_id = update.effective_user.id
        
        affiliates = mongo_db.get_collection('affiliates')
        affiliate = affiliates.find_one({'user_id': user_id})
        
        if not affiliate:
            await update.message.reply_text(
                "❌ Você ainda não é um afiliado.\n\n"
                "Use /afiliado para se registrar e começar a ganhar comissões!"
            )
            return
        
        # Buscar estatísticas recentes
        referrals = mongo_db.get_collection('referrals')
        recent_referrals = list(referrals.find({
            'affiliate_code': affiliate['affiliate_code'],
            'created_at': {'$gte': datetime.utcnow() - timedelta(days=30)}
        }))
        
        # Calcular métricas
        active_referrals = [r for r in recent_referrals if r.get('has_converted', False)]
        conversion_rate = len(active_referrals) / len(recent_referrals) * 100 if recent_referrals else 0
        
        dashboard_text = (
            "📊 **Dashboard do Afiliado**\n\n"
            f"🔗 Código: `{affiliate['affiliate_code']}`\n"
            f"👥 Indicações totais: {affiliate.get('referral_count', 0)}\n"
            f"🎯 Taxa de conversão: {conversion_rate:.1f}%\n\n"
            f"💰 **Comissões:**\n"
            f"• Total acumulado: R$ {affiliate.get('total_commission', 0):.2f}\n"
            f"• Pendente: R$ {affiliate.get('pending_commission', 0):.2f}\n"
            f"• Sacado: R$ {affiliate.get('paid_commission', 0):.2f}\n\n"
            f"📈 **Últimos 30 dias:**\n"
            f"• Novas indicações: {len(recent_referrals)}\n"
            f"• Conversões: {len(active_referrals)}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔗 Gerar Link", callback_data="generate_link")],
            [InlineKeyboardButton("💰 Comissões", callback_data="view_commissions")],
            [InlineKeyboardButton("📤 Compartilhar", callback_data="share_affiliate")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(dashboard_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def generate_affiliate_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gerar link de afiliado personalizado"""
        user_id = update.effective_user.id
        
        affiliates = mongo_db.get_collection('affiliates')
        affiliate = affiliates.find_one({'user_id': user_id})
        
        if not affiliate:
            await update.message.reply_text("❌ Você precisa ser um afiliado para gerar links.")
            return
        
        bot_username = context.bot.username
        affiliate_code = affiliate['affiliate_code']
        affiliate_link = f"https://t.me/{bot_username}?start={affiliate_code}"
        
        message_text = (
            "🔗 **Seu Link de Afiliado:**\n\n"
            f"`{affiliate_link}`\n\n"
            "💡 **Dicas para divulgar:**\n"
            "• Compartilhe em grupos jurídicos\n"
            "• Indique para colegas advogados\n"
            "• Use em suas redes sociais\n"
            "• Adicione na sua assinatura de email\n\n"
            "📊 Cada conversão gera comissão!"
        )
        
        await update.message.reply_text(message_text, parse_mode='Markdown')
    
    async def handle_referral(self, user_id: int, affiliate_code: str) -> bool:
        """Registrar uma indicação"""
        try:
            affiliates = mongo_db.get_collection('affiliates')
            affiliate = affiliates.find_one({'affiliate_code': affiliate_code})
            
            if not affiliate:
                return False
            
            # Registrar a indicação
            referrals = mongo_db.get_collection('referrals')
            referral_data = {
                'affiliate_code': affiliate_code,
                'referred_user_id': user_id,
                'created_at': datetime.utcnow(),
                'has_converted': False,
                'conversion_date': None,
                'conversion_type': None,
                'commission_amount': 0
            }
            
            referrals.insert_one(referral_data)
            
            # Atualizar contador do afiliado
            affiliates.update_one(
                {'affiliate_code': affiliate_code},
                {'$inc': {'referral_count': 1}}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar indicação: {e}")
            return False
    
    async def record_conversion(self, user_id: int, service_type: str, amount: float) -> bool:
        """Registrar conversão e calcular comissão"""
        try:
            # Buscar usuário para verificar se veio de indicação
            users = mongo_db.get_collection('users')
            user = users.find_one({'user_id': user_id})
            
            if not user or not user.get('referred_by'):
                return False
            
            affiliate_code = user['referred_by']
            commission_rate = self.commission_rates.get(service_type, 0.10)
            commission = amount * commission_rate
            
            # Atualizar referência
            referrals = mongo_db.get_collection('referrals')
            referrals.update_one(
                {
                    'affiliate_code': affiliate_code,
                    'referred_user_id': user_id
                },
                {
                    '$set': {
                        'has_converted': True,
                        'conversion_date': datetime.utcnow(),
                        'conversion_type': service_type,
                        'commission_amount': commission
                    }
                }
            )
            
            # Atualizar comissões do afiliado
            affiliates = mongo_db.get_collection('affiliates')
            affiliates.update_one(
                {'affiliate_code': affiliate_code},
                {
                    '$inc': {
                        'total_commission': commission,
                        'pending_commission': commission
                    },
                    '$set': {'last_commission_date': datetime.utcnow()}
                }
            )
            
            logger.info(f"Comissão de R$ {commission:.2f} registrada para afiliado {affiliate_code}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar conversão: {e}")
            return False
    
    async def affiliate_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipular callbacks do sistema de afiliados"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        data = query.data
        
        if data == "generate_link":
            await self.generate_affiliate_link(update, context)
        elif data == "view_commissions":
            await self.view_commissions(update, context)
        elif data == "share_affiliate":
            await self.share_affiliate_link(update, context)
    
    async def view_commissions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Visualizar detalhes das comissões"""
        user_id = update.effective_user.id
        
        affiliates = mongo_db.get_collection('affiliates')
        affiliate = affiliates.find_one({'user_id': user_id})
        
        if not affiliate:
            await update.message.reply_text("❌ Você não é um afiliado.")
            return
        
        # Buscar comissões recentes
        referrals = mongo_db.get_collection('referrals')
        recent_commissions = list(referrals.find({
            'affiliate_code': affiliate['affiliate_code'],
            'has_converted': True
        }).sort('conversion_date', -1).limit(10))
        
        if not recent_commissions:
            message = "💰 **Suas Comissões**\n\nAinda não há comissões registradas."
        else:
            message = "💰 **Últimas Comissões**\n\n"
            for commission in recent_commissions:
                date = commission['conversion_date'].strftime("%d/%m/%Y")
                amount = commission['commission_amount']
                service = commission.get('conversion_type', 'serviço')
                message += f"• {date}: R$ {amount:.2f} ({service})\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def share_affiliate_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Compartilhar link de afiliado"""
        user_id = update.effective_user.id
        
        affiliates = mongo_db.get_collection('affiliates')
        affiliate = affiliates.find_one({'user_id': user_id})
        
        if not affiliate:
            await update.message.reply_text("❌ Você não é um afiliado.")
            return
        
        share_text = (
            "👨‍⚖️ *Recomendo o JuristBot - Assistente Jurídico com IA!*\n\n"
            "🤖 Um bot completo para:\n"
            "• Consultas jurídicas inteligentes\n"
            "• Análise de processos\n"
            "• Pesquisa jurídica\n"
            "• Documentos automatizados\n\n"
            f"🔗 Acesse: https://t.me/{context.bot.username}?start={affiliate['affiliate_code']}\n\n"
            "#JuristBot #Direito #IA #Advocacia"
        )
        
        await update.message.reply_text(
            share_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 Compartilhar", 
                    url=f"https://t.me/share/url?url=https://t.me/{context.bot.username}?start={affiliate['affiliate_code']}&text={share_text}")
            ]])
        )

# Instância global do sistema de afiliados
affiliate_system = AffiliateSystem()

# Registrar comandos e handlers
module_registry.register_command("afiliado", affiliate_system.register_affiliate, "Tornar-se um afiliado")
module_registry.register_command("meuafiliado", affiliate_system.affiliate_dashboard, "Ver dashboard de afiliado")
module_registry.register_command("linkafiliado", affiliate_system.generate_affiliate_link, "Gerar link de afiliado")
module_registry.register_command("comissoes", affiliate_system.view_commissions, "Ver minhas comissões")
module_registry.register_callback("generate_link", affiliate_system.affiliate_callback_handler)
module_registry.register_callback("view_commissions", affiliate_system.affiliate_callback_handler)
module_registry.register_callback("share_affiliate", affiliate_system.affiliate_callback_handler)

module_registry.register_module("affiliate_system")
