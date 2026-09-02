"""
Модуль конфигурации ядра InnoCore AI
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

class LLMProvider(Enum):
"""Перечисление поставщиков LLM"""
    OPENAI = "openai"
    CLAUDE = "claude"
MODELSCOPE = "modelscope" # Облако Alibaba ModelScope
OLLAMA = "ollama" # Локальное развертывание
DASHSCOPE = "dashscope" # Alibaba Cloud Lingji (рекомендуется для серии Qwen)

class VectorDBType(Enum):
"""Перечисление типов векторной базы данных"""
    QDRANT = "qdrant"
    CHROMA = "chroma"
    PINECONE = "pinecone"

@dataclass
class LLMConfig:
"""Конфигурация LLM"""
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-3.5-turbo"  # OpenAI: gpt-4, gpt-3.5-turbo, gpt-4-turbo-preview
                                        # DashScope: qwen-turbo, qwen-plus, qwen-max
                                        # ModelScope: qwen/Qwen2.5-7B-Instruct
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 60

@dataclass
class VectorDBConfig:
"""Конфигурация векторной базы данных"""
    db_type: VectorDBType = VectorDBType.QDRANT
    host: str = "localhost"
    port: int = 6333
    api_key: Optional[str] = None
    collection_name_prefix: str = "innocore"
    embedding_model: str = "text-embedding-3-small"

@dataclass
class DatabaseConfig:
"""Конфигурация реляционной базы данных"""
    host: str = "localhost"
    port: int = 5432
    database: str = "innocore_ai"
    username: str = "postgres"
    password: str = "password"
    pool_size: int = 10

@dataclass
class RedisConfig:
"""Конфигурация Redis"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 20

@dataclass
class ExternalAPIConfig:
"""Внешняя конфигурация API"""
    crossref_api_key: Optional[str] = None
    google_scholar_api_key: Optional[str] = None
    serpapi_key: Optional[str] = None
    arxiv_base_url: str = "http://export.arxiv.org/api/query"
    ieee_base_url: str = "https://ieeexploreapi.ieee.org/api/v1"

@dataclass
class InnoCoreConfig:
"""Основной класс конфигурации InnoCore AI"""
    
#Базовая конфигурация
    app_name: str = "InnoCore AI"
    debug: bool = False
    log_level: str = "INFO"
    
# Конфигурация LLM
    llm: LLMConfig = field(default_factory=LLMConfig)
    
# Конфигурация векторной базы данных
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)
    
# Конфигурация реляционной базы данных
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    
# Конфигурация Redis
    redis: RedisConfig = field(default_factory=RedisConfig)
    
# Конфигурация внешнего API
    external_apis: ExternalAPIConfig = field(default_factory=ExternalAPIConfig)
    
#Конфигурация агента
    agent_max_steps: int = 5
    agent_timeout: int = 300
    concurrent_agents: int = 4
    
# Конфигурация RAG
    retrieval_top_k: int = 5
    similarity_threshold: float = 0.7
    hybrid_search_weights: Dict[str, float] = field(default_factory=lambda: {
        "vector": 0.7,
        "keyword": 0.3
    })
    
#Конфигурация производительности
cache_ttl: int = 3600 # Срок действия кэша (секунды)
    batch_size: int = 10
    max_concurrent_requests: int = 50
    
    def __post_init__(self):
"""Обработка после инициализации"""
# Загрузить конфигурацию из переменных среды
        self.llm.api_key = self.llm.api_key or os.getenv("OPENAI_API_KEY")
        self.llm.base_url = self.llm.base_url or os.getenv("OPENAI_BASE_URL")
        
# Загрузить имя модели из переменной среды (если установлено)
        env_model = os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL")
        if env_model:
            self.llm.model_name = env_model
        
        self.database.password = self.database.password or os.getenv("DATABASE_PASSWORD")
        self.redis.password = self.redis.password or os.getenv("REDIS_PASSWORD")
        
        self.external_apis.crossref_api_key = self.external_apis.crossref_api_key or os.getenv("CROSSREF_API_KEY")
        self.external_apis.google_scholar_api_key = self.external_apis.google_scholar_api_key or os.getenv("GOOGLE_SCHOLAR_API_KEY")
        self.external_apis.serpapi_key = self.external_apis.serpapi_key or os.getenv("SERPAPI_KEY")
        
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

# Пример глобальной конфигурации
config = InnoCoreConfig()

def get_config() -> InnoCoreConfig:
"""Получить экземпляр глобальной конфигурации"""
    return config

def update_config(**kwargs) -> None:
"""Обновить конфигурацию"""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)