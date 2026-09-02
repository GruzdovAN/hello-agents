"""Менеджер захвата памяти — автоматически идентифицирует и сохраняет важную информацию из разговоров."""

import asyncio
import re
from datetime import datetime
from typing import List, Optional, Tuple


# правила триггера памяти

MEMORY_TRIGGERS = [
    # явно просил запомнить

(r"помни|примечание|помни|име в виду", "факт"),
    # выражение предпочтения

    (r"我喜欢|我偏好|prefer|like|love|hate|讨厌|不喜欢", "preference"),
    # протокол решения

    (r"决定了|decision|用这个|选定|确定用|就用", "decision"),
    # номер телефона

    (r"\+\d{10,}|\d{3,4}[-\s]?\d{7,8}", "entity"),
    # Адрес электронной почты

    (r"[\w.-]+@[\w.-]+\.\w+", "entity"),
    # Информация об объекте (мой xxx)

    (r"我的\w+是|is my|我的电话|我的邮箱|我的地址|我的名字", "entity"),
    # констатация фактов

(r"На самом деле|на самом деле|факт|оказывается", "факт"),
]

# Ключевые слова классификации (используются для вспомогательной классификации)

CATEGORY_KEYWORDS = {
«предпочтение»: [«нравится», «предпочтение», «предпочитаю», «нравится», «люблю», «ненавижу», «ненавижу», «не люблю», «привычный», «привыкший»],
"decision": ["решение", "выбрано", "использовать это", "подтвердить", "выбрать", "решить", "решение"],
"сущность": ["телефон", "электронная почта", "адрес", "имя", "учетная запись", "телефон", "электронная почта", "адрес", "учетная запись"],
    "fact": ["记住", "记下", "事实", "实际上", "remember", "fact"],
}


class MemoryCaptureManager:
    """менеджер захвата памяти

    Отвечает за автоматическое определение, классификацию и дедупликацию информации, которую стоит запомнить после разговора.

    Как использовать:
        менеджер = MemoryCaptureManager(workspace_manager)
        воспоминания = менеджер.capture("Пользователь: мне нравится лаконичный стиль ответа")
        # Возврат: [{"content": "Пользователям нравится лаконичный стиль ответа", "category": "preference"}]"""

    def __init__(self, workspace_manager):
        """Инициализировать диспетчер захвата памяти

        Аргументы:
            workspace_manager: экземпляр WorkspaceManager"""
        self.workspace = workspace_manager
        # Скомпилировать регулярное выражение

        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), category)
            for pattern, category in MEMORY_TRIGGERS
        ]

    def capture(self, text: str) -> List[dict]:
        """Анализируйте текст и запоминайте запоминающуюся информацию.

        Аргументы:
            текст: текст для анализа (обычно сообщение пользователя или сводка разговора).

        Возврат:
            Список захваченных воспоминаний, каждый элемент содержит контент и категорию"""
        memories = []
        seen_contents = set()  # Используется для удаления дубликатов


        # Разделить по предложению

        sentences = self._split_sentences(text)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 5:
                continue

            # Проверьте, совпадают ли правила запуска

            category = self._match_trigger(sentence)
            if not category:
                continue

            # Извлечь Содержимое записи

            content = self._extract_memory(sentence, category)
            if not content:
                continue

            # Проверка дедупликации

            content_key = content.lower().strip()
            if content_key in seen_contents:
                continue

            # Проверьте, не является ли это дубликатом существующей памяти.

            if self.workspace.check_duplicate_memory(content, threshold=0.7):
                continue

            seen_contents.add(content_key)
            memories.append({
                "content": content,
                "category": category,
                "timestamp": datetime.now().strftime("%H:%M"),
            })

        return memories

    async def acapture(self, text: str) -> List[dict]:
        """Асинхронно анализируйте текст и собирайте запоминающуюся информацию.

        Аргументы:
            текст: текст для анализа

        Возврат:
            Список запечатленных воспоминаний"""
        # Используйте пул потоков для выполнения задач, интенсивно использующих ЦП.

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.capture, text)

    def capture_and_store(self, text: str, date: datetime = None) -> List[dict]:
        """Анализируйте текст и сохраняйте захваченные воспоминания

        Аргументы:
            текст: текст для анализа
            дата: Дата (по сегодняшнему по умолчанию)

        Возврат:
            фактический список сохраненной памяти"""
        memories = self.capture(text)
        stored = []

        for memory in memories:
            try:
                self.workspace.append_classified_memory(
                    content=memory["content"],
                    category=memory["category"],
                    date=date,
                )
                stored.append(memory)
            except Exception as e:
print(f"⚠️ Не удалось сохранить память: {e}")

        return stored

    async def acapture_and_store(self, text: str, date: datetime = None) -> List[dict]:
        """Асинхронно анализируйте текст и сохраняйте захваченные воспоминания.

        Аргументы:
            текст: текст для анализа
            дата: Дата (по сегодняшнему по умолчанию)

        Возврат:
            фактический список сохраненной памяти"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.capture_and_store, text, date
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Разбить текст на предложения

        Аргументы:
            текст: введите текст

        Возврат:
            список предложений"""
        # Разделить по общим разделителям

        # Поддерживает китайские и английские точки, вопросительные знаки, восклицательные знаки и разрывы строк.

        sentences = re.split(r'[。！？.!?]\s*|\n+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _match_trigger(self, sentence: str) -> Optional[str]:
        """Проверьте, соответствует ли предложение инициирующему правилу

        Аргументы:
            предложение: предложение проверить

        Возврат:
            Соответствующая классификация или «Нет», если соответствия нет."""
        for pattern, category in self._compiled_patterns:
            if pattern.search(sentence):
                return category
        return None

    def _extract_memory(self, sentence: str, category: str) -> Optional[str]:
        """Извлечение Содержимое записи из предложения

        Аргументы:
            предложение: оригинальное предложение
            категория: категория

        Возврат:
            Извлеченные Содержимые записи"""
        # Очистите предложения

        content = sentence.strip()

        # Удалите префиксы (например, «user:», «me:» и т. д.).

content = re.sub(r'^(user|me|you|assistant|user)[::]\s*', '', content)

        # Удалить кавычки

        content = content.strip('"\'""' '')

        # Если контент слишком короткий, это может быть шум.

        if len(content) < 5:
            return None

        # Отформатируйте соответствующим образом в соответствии с классификацией

        if category == "preference":
            # Убедитесь, что память класса предпочтений начинается с «user».

если не content.startswith("用户") и не content.startswith("I "):
контент = f"пользователь{контент}"

        return content

    def analyze_conversation(self, messages: List[dict]) -> List[dict]:
        """Анализируйте полные разговоры и извлекайте воспоминания

        Аргументы:
            сообщения: список сообщений беседы, каждый элемент содержит роль и контент.

        Возврат:
            Список запечатленных воспоминаний"""
        all_memories = []

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            # Анализируйте только сообщения пользователей

            if role == "user" and content:
                memories = self.capture(content)
                all_memories.extend(memories)

        return all_memories

    def get_category_stats(self) -> dict:
        """Получить статистику классификации памяти

        Возврат:
            Статистика количества воспоминаний в каждой категории"""
        # Прочтите сегодняшние воспоминания

        today_path = self.workspace.get_daily_memory_path()
        stats = {
            "preference": 0,
            "decision": 0,
            "entity": 0,
            "fact": 0,
            "total": 0,
        }

        try:
            with open(today_path, "r", encoding="utf-8") as f:
                content = f.read()

            for category in stats:
                if category != "total":
                    # Подсчитайте количество вхождений тега [category]

                    pattern = rf'\[{category}\]'
                    count = len(re.findall(pattern, content, re.IGNORECASE))
                    stats[category] = count
                    stats["total"] += count
        except FileNotFoundError:
            pass

        return stats
