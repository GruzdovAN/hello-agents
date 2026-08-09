"""Конфигурационный файл"""

import os
from typing import Optional

class Settings:
    """Конфигурация приложения"""
    
    # Конфигурация API
    API_TITLE = "Кибергород API"
    API_VERSION = "1.0.0"
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    
    # Конфигурация NPC
    NPC_UPDATE_INTERVAL = 30  # Интервал обновления статуса NPC (секунды)
    
    # Конфигурация LLM (читается из переменных среды)
    # Платформа HelloAgents использует пользовательскую конфигурацию LLM и не требует OPENAI_API_KEY.
    LLM_MODEL_ID: str = os.getenv("LLM_MODEL_ID", "Qwen/Qwen2.5-72B-Instruct")
    LLM_API_KEY: Optional[str] = os.getenv("LLM_API_KEY")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api-inference.modelscope.cn/v1/")

    # Конфигурация CORS
    CORS_ORIGINS = ["*"]  # Производственные среды должны быть ограничены конкретными доменными именами.

    @classmethod
    def validate(cls):
        """Проверьте конфигурацию"""
        if not cls.LLM_API_KEY:
            print("⚠️ ВНИМАНИЕ: переменная среды LLM_API_KEY не установлена.")
            print("   Пожалуйста, настройте LLM_API_KEY в файле .env.")
            print("   Пример: LLM_API_KEY=\"ваш-api-ключ\"")
            return False

        print(f"✅ Конфигурация LLM:")
        print(f"   Модель: {cls.LLM_MODEL_ID}")
        print(f"   Адрес службы: {cls.LLM_BASE_URL}")
        return True

settings = Settings()

