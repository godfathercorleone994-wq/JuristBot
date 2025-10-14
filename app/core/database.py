import os
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.is_connected = False
        self.connect()

    def connect(self):
        """Conectar ao MongoDB"""
        try:
            mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
            db_name = os.getenv('MONGODB_DB_NAME', 'juristbot')
            
            self.client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=10000,
                retryWrites=True
            )
            
            # Testar conexão
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            self.is_connected = True
            
            logger.info("✅ Conectado ao MongoDB com sucesso!")
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ Erro ao conectar com MongoDB: {e}")
            self.client = None
            self.db = None
            self.is_connected = False

    def _create_indexes(self):
        """Criar índices para otimização"""
        try:
            # Índices para usuários
            self.db.users.create_index("user_id", unique=True)
            self.db.users.create_index("created_at")
            self.db.users.create_index("is_active")
            
            # Índices para afiliados
            self.db.affiliates.create_index("affiliate_code", unique=True)
            self.db.affiliates.create_index("user_id", unique=True)
            self.db.affiliates.create_index("status")
            
            # Índices para processos
            self.db.processes.create_index("process_number", unique=True)
            self.db.processes.create_index("user_id")
            self.db.processes.create_index("cpf")
            self.db.processes.create_index("created_at")
            
            # Índices para consultas
            self.db.queries.create_index([("created_at", -1)])
            self.db.queries.create_index("user_id")
            self.db.queries.create_index("query_type")
            
            logger.info("✅ Índices do MongoDB criados/verificados!")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar índices: {e}")

    def get_collection(self, collection_name: str):
        """Obter uma coleção do MongoDB"""
        if not self.is_connected:
            self.connect()
        return self.db[collection_name] if self.db else None

    def insert_user(self, user_data: Dict) -> bool:
        """Inserir ou atualizar usuário"""
        try:
            users = self.get_collection('users')
            if users:
                users.update_one(
                    {'user_id': user_data['user_id']},
                    {
                        '$set': {
                            **user_data, 
                            'updated_at': datetime.utcnow(),
                            'last_activity': datetime.utcnow()
                        },
                        '$setOnInsert': {
                            'created_at': datetime.utcnow(),
                            'is_active': True
                        }
                    },
                    upsert=True
                )
                return True
        except Exception as e:
            logger.error(f"Erro ao inserir usuário: {e}")
        return False

    def get_user(self, user_id: int) -> Optional[Dict]:
        """Obter usuário por ID"""
        try:
            users = self.get_collection('users')
            return users.find_one({'user_id': user_id}) if users else None
        except Exception as e:
            logger.error(f"Erro ao buscar usuário: {e}")
            return None

    def log_query(self, user_id: int, query_type: str, query_data: str, response: str) -> bool:
        """Log de consultas para analytics"""
        try:
            queries = self.get_collection('queries')
            if queries:
                queries.insert_one({
                    'user_id': user_id,
                    'query_type': query_type,
                    'query_data': query_data,
                    'response_preview': response[:500],  # Salvar apenas preview
                    'response_length': len(response),
                    'created_at': datetime.utcnow(),
                    'timestamp': datetime.utcnow().timestamp()
                })
                return True
        except Exception as e:
            logger.error(f"Erro ao logar consulta: {e}")
        return False

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obter estatísticas do usuário"""
        try:
            queries = self.get_collection('queries')
            if queries:
                total_queries = queries.count_documents({'user_id': user_id})
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                today_queries = queries.count_documents({
                    'user_id': user_id,
                    'created_at': {'$gte': today}
                })
                
                return {
                    'total_queries': total_queries,
                    'today_queries': today_queries,
                    'first_query': queries.find_one(
                        {'user_id': user_id}, 
                        sort=[('created_at', 1)]
                    )
                }
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas: {e}")
        
        return {'total_queries': 0, 'today_queries': 0, 'first_query': None}

    def close_connection(self):
        """Fechar conexão"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("Conexão com MongoDB fechada.")

# Instância global do MongoDB
mongo_db = MongoDBManager()
