"""
Управление конфигурацией БД
Поддержка Qdrant (векторная БД) и Neo4j (графовая БД)
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

# Load environment variables early so DB configs pick them up
load_dotenv()


class QdrantConfig(BaseModel):
    """Конфигурация векторной БД Qdrant"""
    
    # Параметры подключения
    url: Optional[str] = Field(
        default=None,
        description="URL сервиса Qdrant (облако или свой URL)"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API-ключ Qdrant (нужен для облака)"
    )
    
    # Параметры коллекции
    collection_name: str = Field(
        default="hello_agents_vectors",
        description="Имя векторной коллекции"
    )
    vector_size: int = Field(
        default=384,
        description="Размерность векторов"
    )
    distance: str = Field(
        default="cosine",
        description="Метрика расстояния (cosine, dot, euclidean)"
    )
    
    # Параметры подключения
    timeout: int = Field(
        default=30,
        description="Таймаут подключения (с)"
    )
    
    @classmethod
    def from_env(cls) -> "QdrantConfig":
        """Создаёт конфигурацию из переменных окружения"""
        return cls(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION", "hello_agents_vectors"),
            vector_size=int(os.getenv("QDRANT_VECTOR_SIZE", "384")),
            distance=os.getenv("QDRANT_DISTANCE", "cosine"),
            timeout=int(os.getenv("QDRANT_TIMEOUT", "30"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь"""
        return self.model_dump(exclude_none=True)


class Neo4jConfig(BaseModel):
    """Конфигурация графовой БД Neo4j"""
    
    # Параметры подключения
    uri: str = Field(
        default="bolt://localhost:7687",
        description="URI подключения Neo4j"
    )
    username: str = Field(
        default="neo4j",
        description="Имя пользователя"
    )
    password: str = Field(
        default="hello-agents-password",
        description="Пароль"
    )
    database: str = Field(
        default="neo4j",
        description="Имя базы данных"
    )
    
    # Параметры пула подключений
    max_connection_lifetime: int = Field(
        default=3600,
        description="Максимальное время жизни соединения (с)"
    )
    max_connection_pool_size: int = Field(
        default=50,
        description="Максимальный размер пула"
    )
    connection_acquisition_timeout: int = Field(
        default=60,
        description="Таймаут получения соединения (с)"
    )
    
    @classmethod
    def from_env(cls) -> "Neo4jConfig":
        """Создаёт конфигурацию из переменных окружения"""
        return cls(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "hello-agents-password"),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            max_connection_lifetime=int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")),
            max_connection_pool_size=int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")),
            connection_acquisition_timeout=int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "60"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь"""
        return self.model_dump()


class DatabaseConfig(BaseModel):
    """Менеджер конфигурации БД"""
    
    qdrant: QdrantConfig = Field(
        default_factory=QdrantConfig,
        description="Конфигурация векторной БД Qdrant"
    )
    neo4j: Neo4jConfig = Field(
        default_factory=Neo4jConfig,
        description="Конфигурация графовой БД Neo4j"
    )
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Создаёт конфигурацию из переменных окружения"""
        return cls(
            qdrant=QdrantConfig.from_env(),
            neo4j=Neo4jConfig.from_env()
        )
    
    def get_qdrant_config(self) -> Dict[str, Any]:
        """Возвращает словарь конфигурации Qdrant"""
        return self.qdrant.to_dict()
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Возвращает словарь конфигурации Neo4j"""
        return self.neo4j.to_dict()
    
    def validate_connections(self) -> Dict[str, bool]:
        """Проверяет конфигурацию подключений к БД"""
        results = {}
        
        # Проверка конфигурации Qdrant
        try:
            from ..memory.storage.qdrant_store import QdrantVectorStore
            qdrant_store = QdrantVectorStore(**self.get_qdrant_config())
            results["qdrant"] = qdrant_store.health_check()
            logger.info(f"✅ Проверка Qdrant: {'успех' if results['qdrant'] else 'ошибка'}")
        except Exception as e:
            results["qdrant"] = False
            logger.error(f"❌ Проверка Qdrant не удалась: {e}")
        
        # Проверка конфигурации Neo4j
        try:
            from ..memory.storage.neo4j_store import Neo4jGraphStore
            neo4j_store = Neo4jGraphStore(**self.get_neo4j_config())
            results["neo4j"] = neo4j_store.health_check()
            logger.info(f"✅ Проверка Neo4j: {'успех' if results['neo4j'] else 'ошибка'}")
        except Exception as e:
            results["neo4j"] = False
            logger.error(f"❌ Проверка Neo4j не удалась: {e}")
        
        return results


# Глобальный экземпляр конфигурации
db_config = DatabaseConfig.from_env()


def get_database_config() -> DatabaseConfig:
    """Возвращает конфигурацию БД"""
    return db_config


def update_database_config(**kwargs) -> None:
    """Обновляет конфигурацию БД"""
    global db_config
    
    if "qdrant" in kwargs:
        db_config.qdrant = QdrantConfig(**kwargs["qdrant"])
    
    if "neo4j" in kwargs:
        db_config.neo4j = Neo4jConfig(**kwargs["neo4j"])
    
    logger.info("✅ Конфигурация БД обновлена")
