import logging
from typing import List, Tuple, Callable, Any

logger = logging.getLogger(__name__)

class ModuleRegistry:
    def __init__(self):
        self.handlers = []
        self.commands = []
        self.loaded_modules = set()
        self.conversation_handlers = []  # ✅ NOVO: Suporte a Conversation Handlers
    
    def register_command(self, command: str, callback: Callable, description: str = None):
        """Registrar comando do bot"""
        self.handlers.append(('command', [command, callback]))
        
        # Adicionar descrição padrão se não fornecida
        if description is None:
            description = f"Comando {command}"
            
        self.commands.append((command, description))
        logger.debug(f"Comando registrado: /{command} - {description}")
    
    def register_message(self, filters_obj: Any, callback: Callable):
        """Registrar handler de mensagens"""
        self.handlers.append(('message', [filters_obj, callback]))
        logger.debug(f"Handler de mensagem registrado: {filters_obj}")
    
    def register_callback(self, pattern: str, callback: Callable):
        """Registrar callback queries"""
        self.handlers.append(('callback', [pattern, callback]))
        logger.debug(f"Callback registrado: {pattern}")
    
    def register_module(self, module_name: str):
        """Registrar módulo carregado"""
        self.loaded_modules.add(module_name)
        logger.info(f"Módulo carregado: {module_name}")
    
    def register_conversation_handler(self, conversation_handler):
        """✅ NOVO: Registrar Conversation Handler"""
        self.conversation_handlers.append(conversation_handler)
        logger.debug(f"Conversation Handler registrado: {conversation_handler}")
    
    def get_handlers(self) -> List[Tuple]:
        return self.handlers
    
    def get_commands(self) -> List[Tuple]:
        return self.commands
    
    def get_loaded_modules(self) -> set:
        return self.loaded_modules
    
    def get_conversation_handlers(self):
        """✅ NOVO: Obter todos os Conversation Handlers"""
        return self.conversation_handlers
    
    def clear_registry(self):
        """Limpar registro (para testes)"""
        self.handlers.clear()
        self.commands.clear()
        self.loaded_modules.clear()
        self.conversation_handlers.clear()

# Instância global do registro
module_registry = ModuleRegistry()
