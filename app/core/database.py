import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connect()

    def connect(self):
        """Conectar ao MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # Testar conexão
            self.client.admin.command('ismaster')
            db_name = os.getenv('MONGODB_DB_NAME', 'juristbot')
            self.db = self.client[db_name]
            
            logger.info("✅ Conectado ao MongoDB com sucesso!")
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Erro ao conectar com MongoDB: {e}")
            self.client = None
            self.db = None

    def _create_indexes(self):
        """Criar índices para otimização"""
        try:
            # Índices para usuários
            self.db.users.create_index("user_id", unique=True)
            self.db.users.create_index("created_at")
            
            # Índices para afiliados
            self.db.affiliates.create_index("affiliate_code", unique=True)
            self.db.affiliates.create_index("user_id", unique=True)
            
            # Índices para processos
            self.db.processes.create_index("process_number", unique=True)
            self.db.processes.create_index("user_id")
            self.db.processes.create_index("cpf")
            
            # Índices para consultas
            self.db.queries.create_index([("created_at", -1)])
            self.db.queries.create_index("user_id")
            
            logger.info("✅ Índices do MongoDB criados!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar índices: {e}")

    def get_collection(self, collection_name):
        """Obter uma coleção do MongoDB"""
        if self.db is None:
            self.connect()
        return self.db[collection_name] if self.db else None

    def insert_user(self, user_data):
        """Inserir ou atualizar usuário"""
        try:
            users = self.get_collection('users')
            if users:
                users.update_one(
                    {'user_id': user_data['user_id']},
                    {'$set': {**user_data, 'updated_at': datetime.utcnow()}},
                    upsert=True
                )
                return True
        except Exception as e:
            logger.error(f"Erro ao inserir usuário: {e}")
        return False

    def get_user(self, user_id):
        """Obter usuário por ID"""
        try:
            users = self.get_collection('users')
            return users.find_one({'user_id': user_id}) if users else None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return None

    def log_query(self, user_id, query_type, query_data, response):
        """Log de consultas para analytics"""
        try:
            queries = self.get_collection('queries')
            if queries:
                queries.insert_one({
                    'user_id': user_id,
                    'query_type': query_type,
                    'query_data': query_data,
                    'response': response,
                    'created_at': datetime.utcnow()
                })
                return True
        except Exception as e:
            logger.error(f"Erro ao logar consulta: {e}")
        return False

    def close_connection(self):
        """Fechar conexão"""
        if self.client:
            self.client.close()
            logger.info("Conexão com MongoDB fechada.")

# Instância global do MongoDB
mongo_db = MongoDBManager()
