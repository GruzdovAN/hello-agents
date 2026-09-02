"""
Управление конфигурацией базы данных
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """Класс конфигурации Oracle-базы данных"""
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        service_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "1521"))
        self.service_name = service_name or os.getenv("DB_SERVICE_NAME", "ORCL")
        self.username = username or os.getenv("DB_USERNAME", "system")
        self.password = password or os.getenv("DB_PASSWORD", "")
        
    def get_connection_string(self) -> str:
        """Получить строку подключения Oracle"""
        return f"{self.username}/{self.password}@{self.host}:{self.port}/{self.service_name}"
    
    def validate(self) -> bool:
        """Проверить, что конфигурация полная"""
        return all([self.host, self.port, self.service_name, self.username, self.password])
