import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from app.core.registry import module_registry
from app.core.database import mongo_db
from app.core.config import Config
from app.modules.ia_services import ai_service
from app.modules.affiliate_system import affiliate_system

logger = logging.getLogger(__name__)

# Estados da conversa para o JuristCoach
CHOOSING, ANALYZING_CAREER, SETTING_GOALS, RECEIVING_ADVICE, TRACKING_PROGRESS = range(5)

class JuristCoach:
    def __init__(self):
        self.career_paths = {
            'advocacia_privada': '🏛️ Advocacia Privada',
            'advocacia_publica': '⚖️ Advocacia Pública', 
            'magistratura': '👨‍⚖️ Magistratura',
            'ministerio_publico': '🔍 Ministério Público',
            'delegacia': '🕵️‍♂️ Carreira Policial',
            'empresarial': '💼 Direito Empresarial',
            'academico': '🎓 Carreira Acadêmica',
            'outro': '🔮 Outra Carreira'
        }
        
        self.skill_categories = {
            'argumentacao': '🎯 Argumentação Jurídica',
            'redacao': '📝 Redação Jurídica', 
            'oratoria': '🎤 Oratória',
            'negociacao': '🤝 Negociação',
            'pesquisa': '🔎 Pesquisa Jurídica',
            'tecnologia': '💻 Tecnologia Jurídica',
            'gestao': '📊 Gestão de Escritório',
            'ingles': '🌎 Inglês Jurídico'
        }

    def start_juristcoach(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar o JuristCoach - Assistente de Carreira Jurídica"""
        user = update.effective_user
        
        welcome_text = (
            "🎯 **BEM-VINDO AO JURISTCOACH!**\n\n"
            "Seu *assistente pessoal de carreira jurídica* com IA!\n\n"
            "✨ **O que posso fazer por você:**\n"
            "• 🎯 Análise de perfil profissional\n"  
            "• 🚀 Planejamento de carreira personalizado\n"
            "• 📚 Recomendações de estudo estratégicas\n"
            "• 💼 Simulações de entrevistas e provas\n"
            "• 📈 Acompanhamento de evolução\n"
            "• 🔮 Previsões de mercado jurídico\n\n"
            "Vamos transformar sua carreira jurídica! 💫"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎯 Análise de Perfil", callback_data="coach_analysis")],
            [InlineKeyboardButton("🚀 Planejamento de Carreira", callback_data="coach_planning")],
            [InlineKeyboardButton("📚 Roteiro de Estudos", callback_data="coach_studyplan")],
            [InlineKeyboardButton("💼 Simulador de Entrevista", callback_data="coach_interview")],
            [InlineKeyboardButton("📈 Meu Progresso", callback_data="coach_progress")],
            [InlineKeyboardButton("🔮 Tendências do Mercado", callback_data="coach_trends")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 'update' pode ser de uma mensagem ou de um callback de botão
        message = update.message if update.message else update.callback_query.message
        message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        
        mongo_db.log_query(user.id, 'juristcoach_start', 'Iniciou JuristCoach', 'Análise de carreira iniciada')
        
        return CHOOSING

    def career_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Análise completa de perfil profissional"""
        query = update.callback_query
        query.answer()
        
        analysis_text = (
            "🎯 **ANÁLISE DE PERFIL PROFISSIONAL**\n\n"
            "Vou analisar seu perfil para criar um plano *personalizado*!\n\n"
            "Por favor, me conte:\n"
            "1. Sua formação acadêmica\n"
            "2. Experiências profissionais\n" 
            "3. Áreas de interesse no Direito\n"
            "4. Seus principais objetivos\n"
            "5. Habilidades que deseja desenvolver\n\n"
            "💡 *Escreva tudo em uma única mensagem*"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="coach_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(analysis_text, reply_markup=reply_markup, parse_mode='Markdown')
        return ANALYZING_CAREER

    def analyze_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processar análise de perfil com IA"""
        user_profile = update.message.text
        user_id = update.effective_user.id
        
        update.message.reply_text("🔮 **Analisando seu perfil com IA...**")
        
        analysis_prompt = f"""
        ANALISE ESTE PERFIL JURÍDICO E FORNEÇA:
        PERFIL DO USUÁRIO: {user_profile}
        FORNEÇA UMA ANÁLISE ESTRUTURADA COM:
        1. ANÁLISE SWOT PERSONALIZADA (Pontos Fortes, Fracos, Oportunidades, Ameaças)
        2. CARREIRAS RECOMENDADAS (Top 3 com justificativa)
        3. PLANO DE DESENVOLVIMENTO (Habilidades, cursos, experiências)
        4. PREVISÃO DE MERCADO (Tendências, salários)
        Formate a resposta de forma clara e motivadora!
        """

        analysis = asyncio.run(ai_service.get_legal_advice(analysis_prompt, "Você é um coach de carreira jurídica especializado."))
        
        coach_data = {'user_id': user_id, 'profile_analysis': user_profile, 'ia_analysis': analysis, 'analysis_date': datetime.utcnow(), 'coach_stage': 'profile_analyzed'}
        coach_collection = mongo_db.get_collection('juristcoach')
        coach_collection.update_one({'user_id': user_id}, {'$set': coach_data}, upsert=True)
        
        response_text = f"🎉 **ANÁLISE COMPLETA DO SEU PERFIL!**\n\n{analysis}\n\n💫 *Use essas insights para impulsionar sua carreira!*"
        
        if len(response_text) > 4096:
            parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for part in parts:
                update.message.reply_text(part, parse_mode='Markdown')
        else:
            update.message.reply_text(response_text, parse_mode='Markdown')
        
        asyncio.run(affiliate_system.record_conversion(user_id, 'career_coaching', 50.0))
        
        keyboard = [[InlineKeyboardButton("🚀 Criar Plano de Ação", callback_data="coach_action_plan")], [InlineKeyboardButton("📚 Ver Roteiro de Estudos", callback_data="coach_studyplan")], [InlineKeyboardButton("🔙 Menu Principal", callback_data="coach_back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text("🎯 **Qual o próximo passo?**", reply_markup=reply_markup)
        return RECEIVING_ADVICE

    def create_study_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Criar roteiro de estudos personalizado"""
        query = update.callback_query
        query.answer()
        user_id = query.from_user.id
        
        coach_collection = mongo_db.get_collection('juristcoach')
        user_data = coach_collection.find_one({'user_id': user_id})
        
        if not user_data or 'ia_analysis' not in user_data:
            query.edit_message_text("❌ Primeiro preciso analisar seu perfil!\n\nUse a opção 'Análise de Perfil' para começar.")
            return CHOOSING
        
        query.edit_message_text("📚 **Criando seu roteiro de estudos personalizado...**")
        
        study_prompt = f"""
        BASEADO NA ANÁLISE ANTERIOR, CRIE UM ROTEIRO DE ESTUDOS DETALHADO COM:
        ANÁLISE DO USUÁRIO: {user_data.get('ia_analysis', '')}
        1. CRONOGRAMA SEMANAL (distribuição, revisões, pausas)
        2. MATERIAIS RECOMENDADOS (livros, cursos, sites)
        3. METODOLOGIA DE ESTUDO (técnicas, mapas mentais, exercícios)
        4. ACOMPANHAMENTO DE PROGRESSO (métricas, verificações)
        Formate como um plano executável de 3-6 meses!
        """

        study_plan = asyncio.run(ai_service.get_legal_advice(study_prompt, "Você é um especialista em métodos de estudo jurídico."))
        
        coach_collection.update_one({'user_id': user_id}, {'$set': {'study_plan': study_plan, 'study_plan_date': datetime.utcnow()}})
        
        response_text = f"📚 **SEU ROTEIRO DE ESTUDOS PERSONALIZADO!**\n\n{study_plan}\n\n🎯 *Siga este plano para maximizar seus resultados!*"
        
        if len(response_text) > 4096:
            parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for part in parts:
                query.message.reply_text(part, parse_mode='Markdown')
        else:
            query.message.reply_text(response_text, parse_mode='Markdown')
        
        keyboard = [[InlineKeyboardButton("💼 Simulador de Entrevista", callback_data="coach_interview")], [InlineKeyboardButton("📈 Acompanhar Progresso", callback_data="coach_progress")], [InlineKeyboardButton("🔙 Menu Principal", callback_data="coach_back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.message.reply_text("🎓 **Preparado para os próximos passos?**", reply_markup=reply_markup)
        return RECEIVING_ADVICE

    def interview_simulator(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Simulador de entrevistas e provas"""
        query = update.callback_query
        query.answer()
        
        simulator_text = "💼 **SIMULADOR DE ENTREVISTAS E PROVAS**\n\nEscolha o tipo de simulação:\n\n• 🏛️ **Entrevista Advocacia Privada**\n• ⚖️ **Entrevista Setor Público**\n• 👨‍⚖️ **Simulado para Magistratura**\n• 🔍 **Simulado para MP**\n• 🕵️‍♂️ **Simulado para Polícia**\n• 💼 **Case Empresarial**\n"
        
        keyboard = [[InlineKeyboardButton("🏛️ Advocacia Privada", callback_data="sim_private")], [InlineKeyboardButton("⚖️ Setor Público", callback_data="sim_public")], [InlineKeyboardButton("👨‍⚖️ Magistratura", callback_data="sim_judge")], [InlineKeyboardButton("🔍 Ministério Público", callback_data="sim_mp")], [InlineKeyboardButton("🕵️‍♂️ Polícia", callback_data="sim_police")], [InlineKeyboardButton("💼 Case Empresarial", callback_data="sim_business")], [InlineKeyboardButton("🔙 Voltar", callback_data="coach_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(simulator_text, reply_markup=reply_markup, parse_mode='Markdown')
        return CHOOSING

    def start_interview_simulation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar simulação específica"""
        query = update.callback_query
        query.answer()
        
        simulation_type = query.data.replace('sim_', '')
        user_id = query.from_user.id
        
        simulation_types = {'private': 'advocacia privada', 'public': 'setor público', 'judge': 'magistratura', 'mp': 'ministério público', 'police': 'carreira policial', 'business': 'direito empresarial'}
        sim_type = simulation_types.get(simulation_type, 'entrevista')
        
        query.edit_message_text(f"🎭 **Preparando simulação para {sim_type}...**")
        
        simulation_prompt = f"""
        CRIE UMA SIMULAÇÃO DE ENTREVISTA/PROVA PARA: CARREIRA: {sim_type.upper()}
        FORNEÇA:
        1. 3 PERGUNTAS TÉCNICAS específicas da área
        2. 2 PERGUNTAS COMPORTAMENTAIS típicas
        3. 1 CASE PRÁTICO para resolução
        4. RESPOSTAS IDEIAS para cada item
        5. DICAS DE APRESENTAÇÃO específicos
        Formate como um simulado interativo e realista!
        """

        simulation = asyncio.run(ai_service.get_legal_advice(simulation_prompt, "Você é um especialista em recrutamento jurídico."))
        
        coach_collection = mongo_db.get_collection('juristcoach')
        coach_collection.update_one({'user_id': user_id}, {'$push': {'simulations': {'type': sim_type, 'content': simulation, 'date': datetime.utcnow()}}})
        
        response_text = f"💼 **SIMULAÇÃO - {sim_type.upper()}**\n\n{simulation}\n\n🎯 *Treine suas respostas e melhore seu desempenho!*"
        
        if len(response_text) > 4096:
            parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for part in parts:
                query.message.reply_text(part, parse_mode='Markdown')
        else:
            query.message.reply_text(response_text, parse_mode='Markdown')
        
        keyboard = [[InlineKeyboardButton("🔄 Nova Simulação", callback_data="coach_interview")], [InlineKeyboardButton("📈 Meu Progresso", callback_data="coach_progress")], [InlineKeyboardButton("🔙 Menu Principal", callback_data="coach_back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.message.reply_text("🎭 **Como foi sua performance?**", reply_markup=reply_markup)
        return RECEIVING_ADVICE

    def career_trends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tendências do mercado jurídico"""
        query = update.callback_query
        query.answer()
        
        query.edit_message_text("🔮 **Analisando tendências do mercado jurídico...**")
        
        trends_prompt = """
        ANALISE AS PRINCIPAIS TENDÊNCIAS DO MERCADO JURÍDICO BRASILEIRO PARA OS PRÓXIMOS 2 ANOS, INCLUINDO:
        1. ÁREAS EM ALTA (setores, nichos)
        2. HABILIDADES MAIS VALORIZADAS (técnicas, comportamentais, tech)
        3. IMPACTOS DA TECNOLOGIA (Lawtechs, IA)
        4. MUDANÇAS NO RECRUTAMENTO (processos, perfis)
        5. RECOMENDAÇÕES ESTRATÉGICAS (como se preparar)
        Baseie-se em dados reais e projeções de mercado!
        """

        trends = asyncio.run(ai_service.get_legal_advice(trends_prompt, "Você é um analista de mercado jurídico especializado."))
        
        response_text = f"🔮 **TENDÊNCIAS DO MERCADO JURÍDICO**\n\n{trends}\n\n💫 *Prepare-se para o futuro do Direito!*"
        
        if len(response_text) > 4096:
            parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for part in parts:
                query.message.reply_text(part, parse_mode='Markdown')
        else:
            query.message.reply_text(response_text, parse_mode='Markdown')
        
        keyboard = [[InlineKeyboardButton("🎯 Análise de Perfil", callback_data="coach_analysis")], [InlineKeyboardButton("🚀 Planejamento", callback_data="coach_planning")], [InlineKeyboardButton("🔙 Menu Principal", callback_data="coach_back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.message.reply_text("🎯 **Como você vai se preparar?**", reply_markup=reply_markup)
        return RECEIVING_ADVICE

    def progress_tracker(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Acompanhamento de progresso"""
        query = update.callback_query
        query.answer()
        
        user_id = query.from_user.id
        coach_collection = mongo_db.get_collection('juristcoach')
        user_data = coach_collection.find_one({'user_id': user_id})
        
        if not user_data:
            progress_text = "📈 **ACOMPANHAMENTO DE PROGRESSO**\n\nVocê ainda não começou sua jornada no JuristCoach!\n\n🎯 Use a *Análise de Perfil* para dar o primeiro passo."
        else:
            analysis_date = user_data.get('analysis_date')
            days_since_analysis = (datetime.utcnow() - analysis_date).days if analysis_date else 0
            simulations_count = len(user_data.get('simulations', []))
            has_study_plan = 'study_plan' in user_data
            progress_text = f"📈 **SEU PROGRESSO NO JURISTCOACH**\n\n📅 **Tempo na jornada:** {days_since_analysis} dias\n🎭 **Simulações realizadas:** {simulations_count}\n📚 **Plano de estudos:** {'✅ Ativo' if has_study_plan else '⏳ Pendente'}\n🔮 **Análise de perfil:** ✅ Concluída\n\n"
            if days_since_analysis > 30: progress_text += "🌟 **Excelente consistência!** Continue evoluindo.\n"
            elif days_since_analysis > 7: progress_text += "💫 **Bom começo!** Mantenha o ritmo.\n"
            else: progress_text += "🎯 **Início promissor!** Foco nos próximos passos.\n"
            if simulations_count == 0: progress_text += "\n💡 **Dica:** Experimente o simulador de entrevistas!\n"
            elif not has_study_plan: progress_text += "\n💡 **Dica:** Crie seu roteiro de estudos personalizado!\n"
        
        keyboard = [[InlineKeyboardButton("🔄 Atualizar Progresso", callback_data="coach_progress")], [InlineKeyboardButton("🎯 Nova Análise", callback_data="coach_analysis")], [InlineKeyboardButton("🔙 Menu Principal", callback_data="coach_back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(progress_text, reply_markup=reply_markup, parse_mode='Markdown')
        return CHOOSING

    def career_planning(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Planejamento estratégico de carreira"""
        query = update.callback_query
        query.answer()
        
        planning_text = "🚀 **PLANEJAMENTO ESTRATÉGICO DE CARREIRA**\n\nVou criar um *plano personalizado* para sua trajetória!\n\nEscolha o horizonte temporal:\n\n• 🎯 **Curto Prazo** (6-12 meses)\n• 🚀 **Médio Prazo** (1-3 anos)\n• 🌟 **Longo Prazo** (3-5 anos)\n"
        
        keyboard = [[InlineKeyboardButton("🎯 Curto Prazo (6-12 meses)", callback_data="plan_short")], [InlineKeyboardButton("🚀 Médio Prazo (1-3 anos)", callback_data="plan_medium")], [InlineKeyboardButton("🌟 Longo Prazo (3-5 anos)", callback_data="plan_long")], [InlineKeyboardButton("🔙 Voltar", callback_data="coach_back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(planning_text, reply_markup=reply_markup, parse_mode='Markdown')
        return CHOOSING

    def generate_career_plan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gerar plano de carreira com IA"""
        query = update.callback_query
        query.answer()
        
        plan_type = query.data.replace('plan_', '')
        user_id = query.from_user.id
        periods = {'short': '6 a 12 meses', 'medium': '1 a 3 anos', 'long': '3 a 5 anos'}
        period = periods.get(plan_type, 'curto prazo')
        
        query.edit_message_text(f"🚀 **Criando seu plano para {period}...**")
        
        coach_collection = mongo_db.get_collection('juristcoach')
        user_data = coach_collection.find_one({'user_id': user_id})
        user_context = user_data.get('ia_analysis', '') if user_data else "Perfil jurídico em desenvolvimento"
        
        plan_prompt = f"""
        CRIE UM PLANO ESTRATÉGICO DE CARREIRA JURÍDICA PARA:
        CONTEXTO DO USUÁRIO: {user_context}
        PERÍODO: {period.upper()}
        ESTRUTURE O PLANO COM:
        1. OBJETIVOS PRINCIPAIS (metas, marcos)
        2. ROTEIRO DE AÇÕES (passos, cursos)
        3. RECURSOS NECESSÁRIOS (materiais, networking)
        4. POTENCIAIS OBSTÁCULOS (desafios, estratégias)
        5. ACOMPANHAMENTO (métricas, revisões)
        Torne o plano prático, realista e motivador!
        """

        career_plan = asyncio.run(ai_service.get_legal_advice(plan_prompt, "Você é um estrategista de carreira jurídica especializado."))
        
        coach_collection.update_one({'user_id': user_id}, {'$set': {f'career_plan_{plan_type}': career_plan, f'plan_{plan_type}_date': datetime.utcnow()}})
        
        response_text = f"🚀 **SEU PLANO DE CARREIRA - {period.upper()}**\n\n{career_plan}\n\n💫 *Execute este plano e transforme sua carreira!*"
        
        if len(response_text) > 4096:
            parts = [response_text[i:i+4096] for i in range(0, len(response_text), 4096)]
            for part in parts:
                query.message.reply_text(part, parse_mode='Markdown')
        else:
            query.message.reply_text(response_text, parse_mode='Markdown')
        
        keyboard = [[InlineKeyboardButton("📚 Roteiro de Estudos", callback_data="coach_studyplan")], [InlineKeyboardButton("💼 Simulador", callback_data="coach_interview")], [InlineKeyboardButton("🔙 Menu Principal", callback_data="coach_back_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.message.reply_text("🎯 **Pronto para colocar em prática?**", reply_markup=reply_markup)
        return RECEIVING_ADVICE

    def back_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Voltar ao menu principal"""
        query = update.callback_query
        query.answer()
        return self.start_juristcoach(update, context)

    def back_to_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Voltar ao menu do JuristCoach"""
        query = update.callback_query
        query.answer()
        
        welcome_text = (
            "🎯 **JURISTCOACH - MENU PRINCIPAL**\n\n"
            "Escolha uma opção para continuar:\n\n"
            "✨ **O que posso fazer por você:**\n"
            "• 🎯 Análise de perfil profissional\n"  
            "• 🚀 Planejamento de carreira personalizado\n"
            "• 📚 Recomendações de estudo estratégicas\n"
            "• 💼 Simulações de entrevistas e provas\n"
            "• 📈 Acompanhamento de evolução\n"
            "• 🔮 Previsões de mercado jurídico\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🎯 Análise de Perfil", callback_data="coach_analysis")],
            [InlineKeyboardButton("🚀 Planejamento de Carreira", callback_data="coach_planning")],
            [InlineKeyboardButton("📚 Roteiro de Estudos", callback_data="coach_studyplan")],
            [InlineKeyboardButton("💼 Simulador de Entrevista", callback_data="coach_interview")],
            [InlineKeyboardButton("📈 Meu Progresso", callback_data="coach_progress")],
            [InlineKeyboardButton("🔮 Tendências do Mercado", callback_data="coach_trends")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')
        return CHOOSING

    def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancelar conversação"""
        update.message.reply_text(
            "👋 Até logo! Lembre-se: *sua carreira jurídica é uma jornada* 🚀\n\n"
            "Volte ao JuristCoach quando quiser continuar sua evolução!",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

# Instância global do JuristCoach
jurist_coach = JuristCoach()

# Configurar Conversation Handler
# Note que a entry_point do CallbackQueryHandler foi ajustada para chamar a função diretamente
coach_conversation = ConversationHandler(
    entry_points=[
        CommandHandler('juristcoach', jurist_coach.start_juristcoach),
        CallbackQueryHandler(jurist_coach.start_juristcoach, pattern='^juristcoach_start$')
    ],
    states={
        CHOOSING: [
            CallbackQueryHandler(jurist_coach.career_analysis, pattern='^coach_analysis$'),
            CallbackQueryHandler(jurist_coach.career_planning, pattern='^coach_planning$'),
            CallbackQueryHandler(jurist_coach.create_study_plan, pattern='^coach_studyplan$'),
            CallbackQueryHandler(jurist_coach.interview_simulator, pattern='^coach_interview$'),
            CallbackQueryHandler(jurist_coach.progress_tracker, pattern='^coach_progress$'),
            CallbackQueryHandler(jurist_coach.career_trends, pattern='^coach_trends$'),
            CallbackQueryHandler(jurist_coach.start_interview_simulation, pattern='^sim_'),
            CallbackQueryHandler(jurist_coach.generate_career_plan, pattern='^plan_'),
            CallbackQueryHandler(jurist_coach.back_to_menu, pattern='^coach_back$'),
            CallbackQueryHandler(jurist_coach.back_to_main, pattern='^coach_back_main$'),
        ],
        ANALYZING_CAREER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, jurist_coach.analyze_profile),
            CallbackQueryHandler(jurist_coach.back_to_menu, pattern='^coach_back$'),
        ],
        RECEIVING_ADVICE: [
            CallbackQueryHandler(jurist_coach.back_to_main, pattern='^coach_back_main$'),
            CallbackQueryHandler(jurist_coach.back_to_menu, pattern='^coach_back$'),
        ]
    },
    fallbacks=[
        CommandHandler('cancel', jurist_coach.cancel),
        CallbackQueryHandler(jurist_coach.cancel, pattern='^cancel$')
    ]
)

# Registrar handlers
module_registry.register_conversation_handler(coach_conversation)
module_registry.register_command("juristcoach", jurist_coach.start_juristcoach, "Assistente de carreira jurídica com IA")
module_registry.register_command("coach", jurist_coach.start_juristcoach, "JuristCoach - Mentoria de carreira")

module_registry.register_module("juristcoach")
