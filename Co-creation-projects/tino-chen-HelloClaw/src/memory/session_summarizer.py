"""Средство суммирования сеансов — автоматическое создание сводок сеансов."""

import os
import re
from datetime import datetime
from typing import List, Optional, Dict, Any


class SessionSummarizer:
    """Сумматор бесед

    Отвечает за обобщение содержимого старых сеансов при создании новых сеансов, создание структурированных сводок и сохранение их в каталоге памяти."""

    def __init__(
        self,
        workspace_manager,
        llm_client=None,
        model_id: str = None,
        api_key: str = None,
        base_url: str = None,
    ):
        """Инициализировать сумматор сеансов

        Аргументы:
            workspace_manager:Рабочий Менеджер пространств
            llm_client: клиент LLM (необязательно, используется для создания сводок)
            model_id: идентификатор модели
            api_key: Ключ API
            base_url: Базовый URL-адрес API"""
        self.workspace = workspace_manager
        self._llm_client = llm_client
        self._model_id = model_id
        self._api_key = api_key
        self._base_url = base_url

    async def summarize_session(
        self,
        messages: List[dict],
        last_n: int = 10,
        session_id: str = None,
    ) -> Optional[str]:
        """Подведите итоги разговора

        Аргументы:
            сообщения: список сообщений сеанса
            Last_n: использовать только последние N раундов диалога
            session_id: идентификатор сеанса (для регистрации)

        Возврат:
            Сгенерированный путь к файлу сводки, в случае ошибки возвращается None."""
        if not messages:
            return None

        # Извлеките последние N раундов диалога

        excerpt = self._extract_excerpt(messages, last_n)
        if not excerpt:
            return None

        try:
            # Создание слизней и резюме

            slug = await self._generate_slug(excerpt)
            summary = await self._generate_summary(excerpt)

            if not slug or not summary:
                return None

            # сохранить в файл

            filename = self._generate_filename(slug)
            self.workspace.save_session_summary(filename, summary)

            return filename

        except Exception as e:
            print(f"⚠️ Ошибка сводки сессии: {e}")
            return None

    def _extract_excerpt(
        self,
        messages: List[dict],
        last_n: int = 10,
    ) -> str:
        """Извлечь текст сводки разговора

        Аргументы:
            сообщения: список сообщений
            Last_n: Пройти последние N раундов диалога.

        Возврат:
            Извлеченный текст"""
        # Сохраняйте только сообщения пользователей и помощников

        conversation = []
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                # Обрезать слишком длинный контент

                if len(content) > 500:
                    content = content[:500] + "..."
                conversation.append(f"[{role.upper()}]: {content}")

        # Возьмите только последние N раундов

        if len(conversation) > last_n * 2:
            conversation = conversation[-(last_n * 2) :]

        return "\n".join(conversation)

    async def _generate_slug(self, excerpt: str) -> str:
        """Создать описательный фрагмент

        Аргументы:
            отрывок: текст резюме сеанса

        Возврат:
            отрывок из 3-5 слов"""
        if not self._llm_client:
            # Если LLM нет, используйте простой метод для создания пули.

            return self._generate_simple_slug(excerpt)

подсказка = f"""Сгенерируйте краткое описание на английском языке (3-5 слов, связанных с символами) на основе следующего диалога категории.
Только вывод описывает себя, больше ничего не критикует.

对话содержимое:
{excerpt[:1000]}

описывать:"""

        try:
            # Позвонить в LLM

            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )

            response = await client.chat.completions.create(
                model=self._model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3,
            )

            slug = response.choices[0].message.content.strip()
            # Очистите слизней

            slug = re.sub(r"[^a-zA-Z0-9\-]", "", slug.replace(" ", "-").lower())
            slug = re.sub(r"-+", "-", slug).strip("-")

            # Ограничить длину

            if len(slug) > 50:
                slug = slug[:50]

            return slug or "conversation"

        except Exception as e:
print(f"⚠️ 生成 slug ошибка: {e}")
            return self._generate_simple_slug(excerpt)

    def _generate_simple_slug(self, excerpt: str) -> str:
        """Используйте простой метод для создания слизней

        Извлекайте ключевые слова из разговоров"""
        # Извлеките некоторые общие ключевые слова

        keywords = []
        common_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "ought",
            "used",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "nor",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "and",
            "but",
            "if",
            "or",
            "because",
            "until",
            "while",
            "about",
            "what",
            "which",
            "who",
            "whom",
            "this",
            "that",
            "these",
            "those",
            "i",
            "me",
            "my",
            "myself",
            "we",
            "our",
            "ours",
            "ourselves",
            "you",
            "your",
            "yours",
            "yourself",
            "yourselves",
            "he",
            "him",
            "his",
            "himself",
            "she",
            "her",
            "hers",
            "herself",
            "it",
            "its",
            "itself",
            "they",
            "them",
            "their",
            "theirs",
            "themselves",
        }

        # Извлечь английские слова

        words = re.findall(r"\b[a-zA-Z]{3,}\b", excerpt.lower())
        word_count = {}
        for word in words:
            if word not in common_words:
                word_count[word] = word_count.get(word, 0) + 1

        # Получите слово с самой высокой частотой

        sorted_words = sorted(word_count.items(), key=lambda x: -x[1])
        keywords = [w for w, _ in sorted_words[:3]]

        if keywords:
            return "-".join(keywords)
        return "conversation"

    async def _generate_summary(self, excerpt: str) -> str:
        """Создание структурированных сводок

        Аргументы:
            отрывок: текст резюме сеанса

        Возврат:
            Краткое описание формата Markdown"""
        if not self._llm_client:
            # Если LLM нет, верните простую форму

            return self._generate_simple_summary(excerpt)

        prompt = f"""Пожалуйста,为以下对话生成一个结构化的сессияитог。

Требовать:
1. Используйте формат Markdown.
2. Содержит следующие части:
- Тема: Краткое изложение одним предложением.
- Ключевые моменты: 3-5 ключевых моментов.
- Дела: если упоминается задача или элемент списка дел.
3. Будьте краткими и ясными, общее количество слов не должно превышать 300.

对话содержимое:
{excerpt[:2000]}

итог:"""

        try:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )

            response = await client.chat.completions.create(
                model=self._model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3,
            )

            summary = response.choices[0].message.content.strip()

            # Добавить заголовок метаинформации

            header = f"""---
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
type: session-summary
---

"""
            return header + summary

        except Exception as e:
print(f"⚠️ 生成итогошибка: {e}")
            return self._generate_simple_summary(excerpt)

    def _generate_simple_summary(self, excerpt: str) -> str:
        """Создание сводок в простом формате"""
        header = f"""---
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
type: session-summary
---

# сессиясводка

## Отрывки из разговора

"""
        # Обрезать первые 500 символов

        content = excerpt[:500]
        if len(excerpt) > 500:
            content += "..."
        return header + content

    def _generate_filename(self, slug: str) -> str:
        """Создать имя файла

        Аргументы:
            слизняк: описательный слизень

        Возврат:
            Имя файла (ГГГГ-ММ-ДД-slug.md)"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{date_str}-{slug}.md"
