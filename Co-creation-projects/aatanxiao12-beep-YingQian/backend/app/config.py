"""Управление конфигурацией - все ключи берутся из переменных среды, жесткое программирование запрещено."""

import os
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Сначала загружаем бэкэнд/.env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)
load_dotenv() # Совместимо с запуском из корневого каталога хранилища



class Settings(BaseSettings):
"""Конфигурация приложения (pydantic-settings)"""

    model_config = SettingsConfigDict(
        env_file=str(_env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

app_name: str = "Помощник по рекомендациям фильмов LLM"
    app_version: str = "0.1.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

# Разделяются запятыми, а затем разделяются на список в коде
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:3000,http://127.0.0.1:3000"
    )

# TMDB: выберите один из двух (токен доступа имеет приоритет)
    tmdb_access_token: str = ""
    tmdb_api_key: str = ""
    tmdb_language: str = "zh-CN"
    tmdb_include_adult: bool = False
    tmdb_image_base_url: str = "https://image.tmdb.org/t/p/w500"

    # LLM 也可由 HelloAgents 直接读 LLM_* 环境变量；此处仅作展示/兜底
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model_id: str = ""

    log_level: str = "INFO"

# HelloAgents Trace (запись в память/трассировки; открыть снова во время отладки)
    trace_enabled: bool = False
    trace_dir: str = "memory/traces"

    def get_cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def has_tmdb_credentials(self) -> bool:
        return bool(self.tmdb_access_token or self.tmdb_api_key)

    def resolve_tmdb_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """返回 (access_token, api_key)；Access Token 优先用于 Bearer 鉴权。"""
        token = (self.tmdb_access_token or "").strip() or None
        api_key = (self.tmdb_api_key or "").strip() or None
        return token, api_key


settings = Settings()


def get_settings() -> Settings:
    return settings


def validate_config() -> bool:
    """startup 校验：本回合仅警告，不阻断启动（便于先跑 /health）。"""
    warnings: list[str] = []

    if not settings.has_tmdb_credentials():
alerts.append("TMDB_ACCESS_TOKEN/TMDB_API_KEY не настроены, интерфейс библиотеки позже не будет доступен")

    llm_key = (
        os.getenv("LLM_API_KEY")
        or settings.llm_api_key
        or os.getenv("OPENAI_API_KEY")
    )
    if not llm_key:
        warnings.append("LLM_API_KEY 未配置，多智能体推荐稍后可能无法调用模型")

    if warnings:
print("\n⚠️ Предупреждение конфигурации:")
        for w in warnings:
            print(f"  - {w}")

    return True


def print_config() -> None:
    llm_key = (
        os.getenv("LLM_API_KEY")
        or settings.llm_api_key
        or os.getenv("OPENAI_API_KEY")
    )
llm_base = os.getenv("LLM_BASE_URL") или settings.llm_base_url или "(默认)"
llm_model = os.getenv("LLM_MODEL_ID") или settings.llm_model_id или "(默认)"

print(f"Имя приложения: {settings.app_name}")
print(f"Версия: {settings.app_version}")
    print(f"服务器: {settings.host}:{settings.port}")
print(f"TMDB: {'настроено', если settings.has_tmdb_credentials() иначе 'не настроено'}")
    print(f"LLM API Key: {'已配置' if llm_key else '未配置'}")
    print(f"LLM Base URL: {llm_base}")
    print(f"LLM Model: {llm_model}")
print(f"Уровень журнала: {settings.log_level}")
print(f"Agent Trace: {'开启' if settings.trace_enabled else '关闭'} ({settings.trace_dir})")"
