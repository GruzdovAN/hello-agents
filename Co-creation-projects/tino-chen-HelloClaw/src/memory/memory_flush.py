"""Диспетчер очистки памяти — напоминает агенту о необходимости сохранить память перед сжатием контекста."""

from datetime import datetime
from typing import Optional, Tuple


class MemoryFlushManager:
    """Менеджер очистки памяти

    Прежде чем контекст будет сжат, запустите тихий раунд, чтобы напомнить агенту о необходимости сохранить свою память.
    Это предотвращает потерю ценного контекста во время сжатия."""

    def __init__(
        self,
        context_window: int = 128000,
        compression_threshold: float = 0.8,
        soft_threshold_tokens: int = 4000,
        enabled: bool = True,
    ):
        """Инициализируйте диспетчер очистки памяти

        Аргументы:
            context_window: размер окна контекста
            compress_threshold: порог сжатия (коэффициент)
            soft_threshold_tokens: количество токенов мягкого порога (триггерная очистка перед точкой сжатия)
            включено: включать ли функцию смыва"""
        self.context_window = context_window
        self.compression_threshold = compression_threshold
        self.soft_threshold_tokens = soft_threshold_tokens
        self.enabled = enabled

        # Запишите, была ли запущена очистка (срабатывает только один раз за сеанс)

        self._flush_triggered = False

    def should_trigger_flush(self, current_tokens: int) -> bool:
        """Определите, следует ли запускать сброс

        Аргументы:
            current_tokens: текущий номер токена

        Возврат:
            Должен ли запускаться сброс"""
        if not self.enabled or self._flush_triggered:
            return False

        # Вычисление триггерных точек: Порог сжатия – Мягкий порог

        trigger_point = (
            self.context_window * self.compression_threshold
            - self.soft_threshold_tokens
        )

        if current_tokens >= trigger_point:
            self._flush_triggered = True
            return True

        return False

    def get_flush_prompt(self) -> str:
        """Получить слово подсказки для сброса

        Возврат:
            Слово-подсказка для тихого раунда"""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"""Pre-compaction memory flush.

The conversation context is about to be compressed. Please save any important memories now.

Guidelines:
- Use memory_add to save notable facts, decisions, or user preferences to memory/{today}.md
- Use memory_update_longterm for information that should persist across all sessions
- Focus on information that would be valuable for future conversations

If nothing important needs to be stored, reply with exactly: [SILENT]"""

    def is_silent_response(self, response: str) -> bool:
        """Определите, является ли это молчаливым ответом

        Аргументы:
            ответ: ответ агента

        Возврат:
            Является ли это молчаливым ответом (не обязательно возвращать пользователю)"""
        return response.strip() == "[SILENT]"

    def reset(self):
        """Сбросить состояние сброса (вызывается при новом сеансе)"""
        self._flush_triggered = False

    def get_status(self) -> dict:
        """Получить текущий статус

        Возврат:
            словарь информации о состоянии"""
        trigger_point = (
            self.context_window * self.compression_threshold
            - self.soft_threshold_tokens
        )
        return {
            "enabled": self.enabled,
            "context_window": self.context_window,
            "compression_threshold": self.compression_threshold,
            "soft_threshold_tokens": self.soft_threshold_tokens,
            "trigger_point": int(trigger_point),
            "flush_triggered": self._flush_triggered,
        }
