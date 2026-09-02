import os
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Define backend root directory
BACKEND_ROOT = Path(__file__).resolve().parent.parent

class SearchAPI(Enum):
"""Выполните поиск по списку поставщиков API.

Совместимо со старыми тестами и примерами:
- TAVILY: используйте поисковую систему Tavily.
- SERPAPI: используйте SerpApi.
- DDG: DuckDuckGo (内置 ddgs)
- ГИБРИД: гибридная стратегия (Tavily + SerpApi), значение по умолчанию.
    """
    TAVILY = "tavily"
    SERPAPI = "serpapi"
    DDG = "ddg"
    HYBRID = "hybrid"


class Configuration(BaseModel):
    """DeepCast Agent Configuration."""

    max_web_research_loops: int = Field(
        default=3,
        title="Research Depth",
        description="Number of research iterations",
    )
    llm_provider: str = Field(
        default="custom",
title="Поставщик LLM",
описание="идентификатор провайдера (настраиваемый)",
    )
    search_api: SearchAPI = Field(
        default=SearchAPI.HYBRID,
title="Поиск API",
описание="Использовать гибридную поисковую систему (Tavily + SerpApi)",
    )
    enable_notes: bool = Field(
        default=True,
title="Включить заметки",
описание="Сохранять ли прогресс выполнения задачи в NoteTool",
    )
    notes_workspace: str = Field(
        default=str(BACKEND_ROOT / "output" / "notes"),
title="Рабочая область "Заметки",
описание="Каталог NoteTool для сохранения заметок о задачах",
    )
    fetch_full_page: bool = Field(
        default=True,
title="Получить полную страницу",
описание="Включить полное содержимое страницы в результаты поиска",
    )
    strip_thinking_tokens: bool = Field(
        default=False,
title="Удалить жетон мышления",
описание="Удалять ли токен <think> из ответа модели",
    )
    use_tool_calling: bool = Field(
        default=False,
title="Использовать вызов инструмента",
описание="Используйте вызовы инструментов вместо схемы JSON для структурированного вывода",
    )
    llm_api_key: str | None = Field(
        default=None,
title="Ключ API LLM",
        description="使用自定义 OpenAI 兼容服务时的可选 API 密钥",
    )
    llm_base_url: str | None = Field(
        default=None,
title="Базовый URL LLM",
описание="Необязательный базовый URL-адрес при использовании пользовательского сервиса, совместимого с OpenAI",
    )
    llm_model_id: str | None = Field(
        default=None,
title="Идентификатор модели LLM",
описание="Необязательный идентификатор модели для пользовательских сервисов, совместимых с OpenAI",
    )
    smart_llm_model: str | None = Field(
        default="ecnu-reasoner",
        title="Smart LLM Model",
        description="复杂推理任务使用的模型 ID (e.g. Planning, Reporting)",
    )
    fast_llm_model: str | None = Field(
        default="ecnu-max",
        title="Fast LLM Model",
описание="Идентификатор модели, используемый задачами быстрого реагирования (например, веб-исследования, создание сценариев)",
    )
    tts_api_key: str | None = Field(
        default=None,
title="Ключ API TTS",
описание="Ключ API для сервиса TTS",
    )
    tts_base_url: str = Field(
        default="https://chat.ecnu.edu.cn/open/api/v1/audio/speech",
title="Базовый URL-адрес TTS",
описание="Базовый URL-адрес TTS API",
    )
    tts_model: str = Field(
        default="ecnu-tts",
title="Модель TTS",
описание="Идентификатор модели сервиса TTS",
    )
    audio_output_dir: str = Field(
        default=str(BACKEND_ROOT / "output" / "audio"),
        title="音频输出目录",
описание="Каталог, в котором сохраняются сгенерированные аудиофайлы",
    )
    ffmpeg_path: str | None = Field(
        default=None,
title="Путь к FFmpeg",
описание="путь к исполняемому файлу ffmpeg",
    )
    tavily_api_key: str | None = Field(
        default=None,
title="Ключ API Тавили",
описание="Ключ API для поиска Тавили",
    )
    serpapi_api_key: str | None = Field(
        default=None,
title="Ключ SerpApi",
описание="Ключ API для SerpApi",
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:5174,http://localhost:3000",
title="Разрешенные источники CORS",
описание="Список источников, разделенных запятыми, которые разрешают междоменные запросы",
    )
    host: str = Field(
        default="0.0.0.0",
title="Хост сервера",
описание="Адрес хоста, который прослушивает сервер FastAPI",
    )
    port: int = Field(
        default=8000,
title="Порт сервера",
описание="Порт прослушивания сервера FastAPI",
    )
    log_level: str = Field(
        default="INFO",
title="Уровень журнала",
        description="日志记录级别 (DEBUG, INFO, WARNING, ERROR)",
    )
    llm_timeout: int = Field(
        default=60,
title="Тайм-аут LLM",
описание="Тайм-аут запроса LLM (секунды)",
    )
    tts_timeout: int = Field(
        default=300,
title="Тайм-аут TTS",
описание="Тайм-аут запроса TTS (секунды)",
    )

    @field_validator("notes_workspace", "audio_output_dir")
    @classmethod
    def resolve_path(cls, v: str) -> str:
"""Убедитесь, что путь является абсолютным, если это относительный путь, он будет разрешен на основе BACKEND_ROOT."""
        if v is None:
            return v
        path = Path(v)
        if not path.is_absolute():
            return str(BACKEND_ROOT / path)
        return v

    @classmethod
    def from_env(cls, overrides: dict[str, Any] | None = None) -> "Configuration":
        """
Создайте объекты конфигурации, используя переменные среды и переопределения.
        
        Args:
переопределения: дополнительный словарь переопределений конфигурации.
            
        Returns:
Инициализированный объект конфигурации.
        """
        raw_values: dict[str, Any] = {}

# Загрузка значений из переменных среды на основе имен полей
        for field_name in cls.model_fields.keys():
            env_key = field_name.upper()
            if env_key in os.environ:
                raw_values[field_name] = os.environ[env_key]

        # 处理 NO_PROXY
        no_proxy = os.getenv("NO_PROXY")
        if no_proxy:
            os.environ["NO_PROXY"] = no_proxy
# Также установлен нижний регистр для совместимости
            os.environ["no_proxy"] = no_proxy

        if overrides:
            for key, value in overrides.items():
                if value is not None:
                    raw_values[key] = value

        return cls(**raw_values)

    def resolved_model(self) -> str | None:
"""Прилагается все усилия, чтобы разрешить идентификатор модели, который будет использоваться."""
        return self.llm_model_id
