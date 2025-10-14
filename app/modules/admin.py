import logging
import csv
import io
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.core.registry import module_registry
from app.core.database import mongo_db
from app.core.config import Config

logger = logging.getLogger(__name__)

class AdminPanel:
    def __init__(self):
        self.admin_id = Config.ADMIN_TELEGRAM_ID
    
    def is_admin(self, user_id: int) -> bool:
        """Verificar se o usuário é admin"""
        return user_id == self.admin_id
    
    async def admin_access_required(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Middleware para verificar acesso admin"""
        user_id = update.effective_user.id
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Acesso restrito. Apenas administradores podem usar este comando.")
            return False
        return True
    
    async def admin_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Painel principal do administrador"""
        if not await self.admin_access_required(update, context):
            return
        
        # Buscar estatísticas gerais
        stats = await self.get_system_stats()
        
        dashboard_text = (
            "👑 **Painel Administrativo - JuristBot**\n\n"
            f"📊 **Estatísticas do Sistema:**\n"
            f"• 👥 Usuários totais: {stats['total_users']}\n"
            f"• 📈 Usuários ativos (30d): {stats['active_users_30d']}\n"
            f"• 🤖 Afiliados: {stats['total_affiliates']}\n"
            f"• 🔍 Consultas totais: {stats['total_queries']}\n"
            f"• 💰 Comissões totais: R$ {stats['total_commissions']:.2f}\n\n"
            
            f"📈 **Hoje:**\n"
            f"• ➕ Novos usuários: {stats['new_users_today']}\n"
            f"• 🔍 Consultas: {stats['queries_today']}\n"
            f"• 💸 Comissões: R$ {stats['commissions_today']:.2f}\n\n"
            
            f"⚙️ **Status do Sistema:**\n"
            f"• 🗄️ MongoDB: {'✅' if mongo_db.is_connected else '❌'}\n"
            f"• 🤖 APIs IA: {stats['available_ia_apis']}\n"
            f"• 🕒 Uptime: {stats['system_uptime']}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Estatísticas Detalhadas", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Gerenciar Usuários", callback_data="admin_users")],
            [InlineKeyboardButton("🤖 Gerenciar Afiliados", callback_data="admin_affiliates")],
            [InlineKeyboardButton("🔍 Consultas Recentes", callback_data="admin_queries")],
            [InlineKeyboardButton("💰 Relatório Financeiro", callback_data="admin_finance")],
            [InlineKeyboardButton("⚙️ Configurações", callback_data="admin_settings")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(dashboard_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def get_system_stats(self) -> Dict:
        """Obter estatísticas do sistema"""
        try:
            # Usuários
            users = mongo_db.get_collection('users')
            total_users = users.count_documents({}) if users else 0
            
            # Usuários ativos (últimos 30 dias)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            active_users_30d = users.count_documents({
                'last_activity': {'$gte': thirty_days_ago}
            }) if users else 0
            
            # Afiliados
            affiliates = mongo_db.get_collection('affiliates')
            total_affiliates = affiliates.count_documents({}) if affiliates else 0
            
            # Consultas
            queries = mongo_db.get_collection('queries')
            total_queries = queries.count_documents({}) if queries else 0
            
            # Consultas de hoje
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            queries_today = queries.count_documents({
                'created_at': {'$gte': today_start}
            }) if queries else 0
            
            # Comissões
            total_commissions = 0
            commissions_today = 0
            if affiliates:
                affiliate_stats = affiliates.aggregate([
                    {
                        '$group': {
                            '_id': None,
                            'total_commission': {'$sum': '$total_commission'},
                            'today_commission': {
                                '$sum': {
                                    '$cond': [
                                        {'$gte': ['$last_commission_date', today_start]},
                                        '$pending_commission',
                                        0
                                    ]
                                }
                            }
                        }
                    }
                ])
                result = list(affiliate_stats)
                if result:
                    total_commissions = result[0].get('total_commission', 0)
                    commissions_today = result[0].get('today_commission', 0)
            
            # Novos usuários hoje
            new_users_today = users.count_documents({
                'created_at': {'$gte': today_start}
            }) if users else 0
            
            # APIs de IA disponíveis
            from app.core.config import Config
            available_apis = Config.get_available_ia_apis()
            
            # Uptime do sistema (simulado)
            system_uptime = "24h 15m"
            
            return {
                'total_users': total_users,
                'active_users_30d': active_users_30d,
                'total_affiliates': total_affiliates,
                'total_queries': total_queries,
                'queries_today': queries_today,
                'total_commissions': total_commissions,
                'commissions_today': commissions_today,
                'new_users_today': new_users_today,
                'available_ia_apis': len(available_apis),
                'system_uptime': system_uptime
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
            return {}
    
    async def admin_stats_detailed(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Estatísticas detalhadas do sistema"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        # Estatísticas por tipo de consulta
        queries = mongo_db.get_collection('queries')
        if queries:
            pipeline = [
                {
                    '$group': {
                        '_id': '$query_type',
                        'count': {'$sum': 1},
                        'last_24h': {
                            '$sum': {
                                '$cond': [
                                    {'$gte': ['$created_at', datetime.utcnow() - timedelta(hours=24)]},
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                },
                {'$sort': {'count': -1}}
            ]
            query_stats = list(queries.aggregate(pipeline))
        else:
            query_stats = []
        
        stats_text = "📈 **Estatísticas Detalhadas**\n\n"
        
        if query_stats:
            stats_text += "🔍 **Consultas por Tipo:**\n"
            for stat in query_stats[:10]:  # Top 10 tipos
                stats_text += f"• {stat['_id']}: {stat['count']} total, {stat['last_24h']} últimas 24h\n"
            stats_text += "\n"
        
        # Usuários por período
        users = mongo_db.get_collection('users')
        if users:
            user_stats = {
                'last_24h': users.count_documents({
                    'created_at': {'$gte': datetime.utcnow() - timedelta(hours=24)}
                }),
                'last_7d': users.count_documents({
                    'created_at': {'$gte': datetime.utcnow() - timedelta(days=7)}
                }),
                'last_30d': users.count_documents({
                    'created_at': {'$gte': datetime.utcnow() - timedelta(days=30)}
                })
            }
            
            stats_text += (
                f"👥 **Crescimento de Usuários:**\n"
                f"• Últimas 24h: {user_stats['last_24h']}\n"
                f"• Últimos 7 dias: {user_stats['last_7d']}\n"
                f"• Últimos 30 dias: {user_stats['last_30d']}\n"
            )
        
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_manage_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gerenciamento de usuários"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        users = mongo_db.get_collection('users')
        if not users:
            await query.edit_message_text("❌ Erro ao acessar banco de dados.")
            return
        
        # Usuários mais ativos
        pipeline = [
            {
                '$lookup': {
                    'from': 'queries',
                    'localField': 'user_id',
                    'foreignField': 'user_id',
                    'as': 'user_queries'
                }
            },
            {
                '$addFields': {
                    'query_count': {'$size': '$user_queries'},
                    'last_active': {'$max': '$user_queries.created_at'}
                }
            },
            {'$sort': {'query_count': -1}},
            {'$limit': 10}
        ]
        
        top_users = list(users.aggregate(pipeline))
        
        users_text = "👥 **Top 10 Usuários Mais Ativos**\n\n"
        
        for i, user in enumerate(top_users, 1):
            username = user.get('username', 'Sem username')
            first_name = user.get('first_name', 'N/A')
            query_count = user.get('query_count', 0)
            
            users_text += f"{i}. {first_name} (@{username}): {query_count} consultas\n"
        
        users_text += "\n💡 *Use /exportusers para exportar lista completa*"
        
        keyboard = [
            [InlineKeyboardButton("📤 Exportar Usuários", callback_data="admin_export_users")],
            [InlineKeyboardButton("🔄 Atualizar", callback_data="admin_users")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(users_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_export_users(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Exportar lista de usuários para CSV"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        users = mongo_db.get_collection('users')
        if not users:
            await query.edit_message_text("❌ Erro ao acessar banco de dados.")
            return
        
        # Buscar todos os usuários
        all_users = list(users.find({}, {
            'user_id': 1, 
            'username': 1, 
            'first_name': 1, 
            'last_name': 1, 
            'created_at': 1,
            'last_activity': 1,
            'is_affiliate': 1
        }).sort('created_at', -1))
        
        # Criar CSV em memória
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escrever cabeçalho
        writer.writerow([
            'ID', 'Username', 'Primeiro Nome', 'Último Nome', 
            'Data de Criação', 'Última Atividade', 'É Afiliado'
        ])
        
        # Escrever dados
        for user in all_users:
            writer.writerow([
                user.get('user_id', ''),
                user.get('username', ''),
                user.get('first_name', ''),
                user.get('last_name', ''),
                user.get('created_at', '').strftime('%Y-%m-%d %H:%M:%S') if user.get('created_at') else '',
                user.get('last_activity', '').strftime('%Y-%m-%d %H:%M:%S') if user.get('last_activity') else '',
                'Sim' if user.get('is_affiliate') else 'Não'
            ])
        
        # Preparar arquivo para envio
        csv_data = output.getvalue().encode('utf-8')
        csv_file = io.BytesIO(csv_data)
        csv_file.name = f'usuarios_juristbot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        await context.bot.send_document(
            chat_id=query.from_user.id,
            document=csv_file,
            filename=csv_file.name,
            caption=f"📊 Exportação de Usuários - {len(all_users)} usuários"
        )
        
        # Atualizar mensagem original
        await query.edit_message_text(
            f"✅ Arquivo CSV exportado com sucesso!\n\n"
            f"📁 {len(all_users)} usuários exportados.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Voltar", callback_data="admin_users")
            ]])
        )
    
    async def admin_manage_affiliates(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gerenciamento de afiliados"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        affiliates = mongo_db.get_collection('affiliates')
        if not affiliates:
            await query.edit_message_text("❌ Nenhum afiliado encontrado.")
            return
        
        # Top afiliados por comissão
        top_affiliates = list(affiliates.find().sort('total_commission', -1).limit(10))
        
        affiliates_text = "🤖 **Top 10 Afiliados por Comissão**\n\n"
        
        for i, affiliate in enumerate(top_affiliates, 1):
            username = affiliate.get('username', 'Sem username')
            first_name = affiliate.get('first_name', 'N/A')
            total_commission = affiliate.get('total_commission', 0)
            referral_count = affiliate.get('referral_count', 0)
            
            affiliates_text += (
                f"{i}. {first_name} (@{username})\n"
                f"   💰 R$ {total_commission:.2f} | 👥 {referral_count} indicações\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("📤 Exportar Afiliados", callback_data="admin_export_affiliates")],
            [InlineKeyboardButton("🔄 Atualizar", callback_data="admin_affiliates")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(affiliates_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_recent_queries(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Consultas recentes do sistema"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        queries = mongo_db.get_collection('queries')
        if not queries:
            await query.edit_message_text("❌ Nenhuma consulta encontrada.")
            return
        
        # Últimas 10 consultas
        recent_queries = list(queries.find().sort('created_at', -1).limit(10))
        
        queries_text = "🔍 **Últimas 10 Consultas**\n\n"
        
        for i, q in enumerate(recent_queries, 1):
            user_id = q.get('user_id', 'N/A')
            query_type = q.get('query_type', 'N/A')
            query_data = q.get('query_data', '')[:50] + "..." if len(q.get('query_data', '')) > 50 else q.get('query_data', '')
            created_at = q.get('created_at', '').strftime('%H:%M') if q.get('created_at') else 'N/A'
            
            queries_text += f"{i}. 🕒 {created_at} | 👤 {user_id}\n"
            queries_text += f"   📝 {query_type}: {query_data}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("📤 Exportar Consultas", callback_data="admin_export_queries")],
            [InlineKeyboardButton("🔄 Atualizar", callback_data="admin_queries")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(queries_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_financial_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Relatório financeiro"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        affiliates = mongo_db.get_collection('affiliates')
        if not affiliates:
            await query.edit_message_text("❌ Dados financeiros não disponíveis.")
            return
        
        # Estatísticas financeiras
        pipeline = [
            {
                '$group': {
                    '_id': None,
                    'total_commission': {'$sum': '$total_commission'},
                    'pending_commission': {'$sum': '$pending_commission'},
                    'paid_commission': {'$sum': '$paid_commission'},
                    'active_affiliates': {'$sum': 1}
                }
            }
        ]
        
        result = list(affiliates.aggregate(pipeline))
        if not result:
            finance_data = {'total_commission': 0, 'pending_commission': 0, 'paid_commission': 0, 'active_affiliates': 0}
        else:
            finance_data = result[0]
        
        finance_text = (
            "💰 **Relatório Financeiro**\n\n"
            f"• 💵 Comissões Totais: R$ {finance_data.get('total_commission', 0):.2f}\n"
            f"• ⏳ Comissões Pendentes: R$ {finance_data.get('pending_commission', 0):.2f}\n"
            f"• ✅ Comissões Pagas: R$ {finance_data.get('paid_commission', 0):.2f}\n"
            f"• 🤖 Afiliados Ativos: {finance_data.get('active_affiliates', 0)}\n\n"
            
            "💡 *Valores baseados no sistema de comissões de 10-20%*"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Estatísticas Detalhadas", callback_data="admin_stats")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(finance_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Configurações do sistema"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        from app.core.config import Config
        
        settings_text = (
            "⚙️ **Configurações do Sistema**\n\n"
            f"• 🤖 Nome do Bot: {Config.BOT_NAME}\n"
            f"• 👤 Admin ID: {Config.ADMIN_TELEGRAM_ID}\n"
            f"• 🗄️ MongoDB: {'✅ Conectado' if mongo_db.is_connected else '❌ Desconectado'}\n\n"
            
            "🔧 **APIs Configuradas:**\n"
        )
        
        # Status das APIs de IA
        from app.modules.ia_services import ai_service
        apis_status = [
            f"• DeepSeek: {'✅' if ai_service.deepseek_available else '❌'}",
            f"• Gemini: {'✅' if ai_service.gemini_available else '❌'}",
            f"• OpenAI: {'✅' if ai_service.openai_available else '❌'}"
        ]
        
        settings_text += "\n".join(apis_status)
        
        keyboard = [
            [InlineKeyboardButton("🔄 Verificar Conexões", callback_data="admin_check_connections")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="admin_back")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(settings_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_check_connections(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verificar status das conexões"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        # Testar conexão com MongoDB
        mongo_status = "✅ Conectado" if mongo_db.is_connected else "❌ Desconectado"
        
        # Testar APIs de IA
        from app.modules.ia_services import ai_service
        
        connection_text = (
            "🔌 **Verificação de Conexões**\n\n"
            f"• 🗄️ MongoDB: {mongo_status}\n"
            "• 🤖 APIs de IA:\n"
        )
        
        # Testar cada API
        test_results = []
        
        # DeepSeek
        try:
            deepseek_test = await ai_service.ask_deepseek("Teste de conexão")
            deepseek_status = "✅ OK" if deepseek_test else "❌ Falha"
        except:
            deepseek_status = "❌ Erro"
        test_results.append(f"  - DeepSeek: {deepseek_status}")
        
        # Gemini
        try:
            gemini_test = await ai_service.ask_gemini("Teste de conexão")
            gemini_status = "✅ OK" if gemini_test else "❌ Falha"
        except:
            gemini_status = "❌ Erro"
        test_results.append(f"  - Gemini: {gemini_status}")
        
        # OpenAI
        try:
            openai_test = await ai_service.ask_openai("Teste de conexão")
            openai_status = "✅ OK" if openai_test else "❌ Falha"
        except:
            openai_status = "❌ Erro"
        test_results.append(f"  - OpenAI: {openai_status}")
        
        connection_text += "\n".join(test_results)
        
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="admin_settings")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(connection_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def admin_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manipular callbacks do painel administrativo"""
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        
        if callback_data == "admin_stats":
            await self.admin_stats_detailed(update, context)
        elif callback_data == "admin_users":
            await self.admin_manage_users(update, context)
        elif callback_data == "admin_affiliates":
            await self.admin_manage_affiliates(update, context)
        elif callback_data == "admin_queries":
            await self.admin_recent_queries(update, context)
        elif callback_data == "admin_finance":
            await self.admin_financial_report(update, context)
        elif callback_data == "admin_settings":
            await self.admin_settings(update, context)
        elif callback_data == "admin_export_users":
            await self.admin_export_users(update, context)
        elif callback_data == "admin_check_connections":
            await self.admin_check_connections(update, context)
        elif callback_data == "admin_back":
            await self.admin_dashboard_callback(update, context)
    
    async def admin_dashboard_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Voltar ao dashboard principal (versão callback)"""
        query = update.callback_query
        await query.answer()
        
        if not self.is_admin(query.from_user.id):
            await query.edit_message_text("❌ Acesso negado.")
            return
        
        # Reutilizar a lógica do dashboard principal
        stats = await self.get_system_stats()
        
        dashboard_text = (
            "👑 **Painel Administrativo - JuristBot**\n\n"
            f"📊 **Estatísticas do Sistema:**\n"
            f"• 👥 Usuários totais: {stats['total_users']}\n"
            f"• 📈 Usuários ativos (30d): {stats['active_users_30d']}\n"
            f"• 🤖 Afiliados: {stats['total_affiliates']}\n"
            f"• 🔍 Consultas totais: {stats['total_queries']}\n"
            f"• 💰 Comissões totais: R$ {stats['total_commissions']:.2f}\n\n"
            
            f"📈 **Hoje:**\n"
            f"• ➕ Novos usuários: {stats['new_users_today']}\n"
            f"• 🔍 Consultas: {stats['queries_today']}\n"
            f"• 💸 Comissões: R$ {stats['commissions_today']:.2f}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("📊 Estatísticas Detalhadas", callback_data="admin_stats")],
            [InlineKeyboardButton("👥 Gerenciar Usuários", callback_data="admin_users")],
            [InlineKeyboardButton("🤖 Gerenciar Afiliados", callback_data="admin_affiliates")],
            [InlineKeyboardButton("🔍 Consultas Recentes", callback_data="admin_queries")],
            [InlineKeyboardButton("💰 Relatório Financeiro", callback_data="admin_finance")],
            [InlineKeyboardButton("⚙️ Configurações", callback_data="admin_settings")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(dashboard_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enviar mensagem broadcast para todos os usuários"""
        if not await self.admin_access_required(update, context):
            return
        
        if not context.args:
            await update.message.reply_text(
                "📢 **Envio de Broadcast**\n\n"
                "💡 **Uso:** /broadcast <mensagem>\n\n"
                "Exemplo:\n"
                "`/broadcast Nova atualização disponível! Confira as novidades.`\n\n"
                "⚠️ *Esta mensagem será enviada para todos os usuários.*",
                parse_mode='Markdown'
            )
            return
        
        message = " ".join(context.args)
        users = mongo_db.get_collection('users')
        
        if not users:
            await update.message.reply_text("❌ Erro ao acessar banco de dados.")
            return
        
        # Buscar todos os usuários
        all_users = users.find({}, {'user_id': 1})
        user_count = 0
        error_count = 0
        
        await update.message.reply_text(f"📤 Iniciando broadcast para {users.count_documents({})} usuários...")
        
        # Enviar mensagem para cada usuário
        for user in all_users:
            try:
                user_id = user['user_id']
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 **Mensagem do JuristBot:**\n\n{message}"
                )
                user_count += 1
                
                # Pequena pausa para evitar rate limiting
                import asyncio
                await asyncio.sleep(0.1)
                
            except Exception as e:
                error_count += 1
                logger.error(f"Erro ao enviar broadcast para {user_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Broadcast concluído!\n\n"
            f"• ✅ Enviadas: {user_count}\n"
            f"• ❌ Erros: {error_count}\n"
            f"• 📊 Total: {user_count + error_count}"
        )

# Instância global do painel administrativo
admin_panel = AdminPanel()

# Registrar comandos administrativos
module_registry.register_command("admin", admin_panel.admin_dashboard, "Painel administrativo (apenas admin)")
module_registry.register_command("broadcast", admin_panel.broadcast_message, "Enviar mensagem para todos os usuários (apenas admin)")

# Registrar handlers de callback
module_registry.register_callback("admin_.*", admin_panel.admin_callback_handler)

module_registry.register_module("admin")
