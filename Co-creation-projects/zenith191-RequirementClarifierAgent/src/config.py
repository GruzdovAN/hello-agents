"""Чтение и проверка конфигурации LLM."""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(ValueError):
    """Конфигурация отсутствует или значение недопустимо."""


def _read_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} должно быть числом") from exc


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ConfigurationError(f"{name} должно быть целым числом") from exc


@dataclass(frozen=True)
class LLMSettings:
    """Явная конфигурация для HelloAgentsLLM."""

    model: str
    api_key: str
    base_url: str
    temperature: float = 0.2
    timeout: int = 120

    @classmethod
    def from_env(cls) -> "LLMSettings":
        """Читает конфигурацию из официальных переменных HelloAgents и проверяет её."""

        settings = cls(
            model=os.getenv("LLM_MODEL_ID", "").strip(),
            api_key=os.getenv("LLM_API_KEY", "").strip(),
            base_url=os.getenv("LLM_BASE_URL", "").strip(),
            temperature=_read_float("LLM_TEMPERATURE", 0.2),
            timeout=_read_int("LLM_TIMEOUT", 120),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        """Отклоняет отсутствующие, placeholder или выходящие за границы значения."""

        missing = [
            name
            for name, value in (
                ("LLM_MODEL_ID", self.model),
                ("LLM_API_KEY", self.api_key),
                ("LLM_BASE_URL", self.base_url),
            )
            if not value
        ]
        if missing:
            raise ConfigurationError(
                "Отсутствует конфигурация LLM: " + ", ".join(missing) + ". Скопируйте и заполните .env."
            )

        lowered_key = self.api_key.casefold()
        if lowered_key.startswith("your_") or lowered_key in {"changeme", "replace_me"}:
            raise ConfigurationError("LLM_API_KEY — placeholder; укажите реальный ключ в .env")
        if not 0 <= self.temperature <= 2:
            raise ConfigurationError("LLM_TEMPERATURE должно быть от 0 до 2")
        if self.timeout <= 0:
            raise ConfigurationError("LLM_TIMEOUT должно быть больше 0")
