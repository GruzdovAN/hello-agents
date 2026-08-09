"""Модуль управления конфигурацией"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Загрузить переменные среды
# Сначала попробуйте загрузить .env текущего каталога.
load_dotenv()

# Затем попробуйте загрузить .env HelloAgents, если он существует.
helloagents_env = Path(__file__).parent.parent.parent.parent / "HelloAgents" / ".env"
if helloagents_env.exists():
    load_dotenv(helloagents_env, override=False)  # Не перезаписывайте существующие переменные среды


class Settings(BaseSettings):
    """Конфигурация приложения"""

    # Применить базовую конфигурацию
    app_name: str = "Умный помощник в путешествиях HelloAgents"
    app_version: str = "1.0.0"
    debug: bool = False

    # Конфигурация сервера
    host: str = "0.0.0.0"
    port: int = 8000

    # Конфигурация CORS – использование строк, разделенных на код
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,http://127.0.0.1:3000"

    # Конфигурация API Amap
    amap_api_key: str = ""

    # Конфигурация API Unsplash
    unsplash_access_key: str = ""
    unsplash_secret_key: str = ""

    # Конфигурация LLM (читается из переменных среды, управляемых HelloAgents)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # Конфигурация журнала
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Игнорировать дополнительные переменные среды

    def get_cors_origins_list(self) -> List[str]:
        """Получить список источников CORS"""
        return [origin.strip() for origin in self.cors_origins.split(',')]


# Создайте экземпляр глобальной конфигурации
settings = Settings()


def get_settings() -> Settings:
    """Получить экземпляр конфигурации"""
    return settings


# Проверьте необходимую конфигурацию
def validate_config():
    """Убедитесь, что настройка завершена"""
    errors = []
    warnings = []

    if not settings.amap_api_key:
        errors.append("AMAP_API_KEY не настроен.")

    # HelloAgentsLLM автоматически считывает данные из LLM_API_KEY и не требует OPENAI_API_KEY.
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not llm_api_key:
        warnings.append("LLM_API_KEY или OPENAI_API_KEY не настроены, и функция LLM может быть недоступна.")

    if errors:
        error_msg = "Ошибка конфигурации:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)

    if warnings:
        print("\n⚠️ Предупреждение конфигурации:")
        for w in warnings:
            print(f"  - {w}")

    return True


# Распечатать информацию о конфигурации (для отладки)
def print_config():
    """Распечатать текущую конфигурацию (скрыть конфиденциальную информацию)"""
    print(f"Имя приложения: {settings.app_name}")
    print(f"Версия: {settings.app_version}")
    print(f"Сервер: {settings.host}:{settings.port}")
    print(f"Ключ API Amap: {'настроено', если settings.amap_api_key еще 'не настроено'}")

    # Проверьте конфигурацию LLM
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    llm_base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
    llm_model = os.getenv("LLM_MODEL_ID") or settings.openai_model

    print(f"Ключ API LLM: {'настроено', если llm_api_key иначе 'не настроено'}")
    print(f"LLM Base URL: {llm_base_url}")
    print(f"LLM Model: {llm_model}")
    print(f"Уровень журнала: {settings.log_level}")

