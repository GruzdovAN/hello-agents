# processors/add_knowledge.py
"""Обработчик добавления знаний — анализ, классификация и сохранение через LLM"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from hello_agents import HelloAgentsLLM
from core.file_manager import FileManager
from core.summary_manager import SummaryManager


class AddKnowledgeProcessor:
    """
    Обработчик добавления знаний

    Возможности:
    - Определение типа ввода (текст/файл/URL)
    - Анализ содержания через LLM
    - Интеллектуальная классификация и теги
    - Извлечение ключевых концепций
    - Генерация имени файла
    - Сохранение в каталог knowledge
    - Обновление knowledge_summary.md
    """

    def __init__(self, llm: HelloAgentsLLM, file_manager: FileManager):
        """
        Инициализация AddKnowledgeProcessor

        Args:
            llm: экземпляр HelloAgentsLLM
            file_manager: экземпляр FileManager
        """
        self.llm = llm
        self.file_manager = file_manager
        self.summary_manager = SummaryManager(file_manager)

    def _identify_input_type(self, input_data: str) -> str:
        """
        Определить тип ввода

        Args:
            input_data: ввод пользователя

        Returns:
            тип ввода (text/file/url)
        """
        # Проверка URL
        if input_data.startswith("http://") or input_data.startswith("https://"):
            return "url"

        # Проверка пути к файлу
        if (
            input_data.startswith("~")
            or input_data.startswith("/")
            or input_data.startswith("./")
        ):
            return "file"

        # По умолчанию — текст
        return "text"

    def _read_file(self, file_path: str) -> str:
        """
        Прочитать содержимое файла

        Args:
            file_path: путь к файлу

        Returns:
            Содержимое файла
        """
        # Обработка пути ~
        if file_path.startswith("~"):
            file_path = os.path.expanduser(file_path)

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _analyze_content(self, content: str, domain: str) -> Dict[str, any]:
        """
        Анализ содержания через LLM

        Args:
            content: содержание знания
            domain: название области

        Returns:
            словарь результатов анализа:
            - category: категория
            - tags: список тегов
            - key_concepts: список ключевых концепций
            - summary: краткое резюме
        """
        user_prompt = f"""Проанализируйте содержание и извлеките ключевую информацию:

【Область】
{domain}

【Содержание】
{content[:2000]}

Предоставьте информацию (формат JSON):
{{
  "category": "категория (алгоритмы, концепции, инструменты, практика и т.д.)",
  "tags": ["тег1", "тег2", "тег3"],
  "key_concepts": ["концепция1", "концепция2", "концепция3"],
  "summary": "краткое резюме (до 50 слов)"
}}
"""

        messages = [
            {
                "role": "system",
                "content": "Вы — эксперт по управлению знаниями: анализ, извлечение ключевой информации, классификация и теги.",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.llm.invoke(messages)

            # Попытка разбора JSON (упрощённо — правила)
            return self._extract_metadata_from_text(response)
        except Exception:
            # Fallback: анализ по правилам
            return {
                "category": self._classify_content(content, domain),
                "tags": self._extract_tags_from_content(content),
                "key_concepts": self._extract_concepts_from_content(content),
                "summary": content[:100] + "..." if len(content) > 100 else content,
                "domain": domain,  # поле domain
            }

    def _extract_metadata_from_text(self, text: str) -> Dict[str, any]:
        """
        Извлечь метаданные из текста (упрощённо)

        Args:
            text: текст ответа LLM

        Returns:
            словарь метаданных
        """
        # Упрощённо: извлечение по правилам
        lines = text.strip().split("\n")

        category = "общее"
        tags = []
        key_concepts = []
        summary = ""

        for line in lines:
            line = line.strip()
            if "категор" in line.lower() or "category" in line.lower():
                category = line.split("：")[-1].split(":")[-1].strip()
            elif "тег" in line.lower() or "tags" in line.lower():
                tags = [
                    tag.strip(" \"'[]{}")
                    for tag in line.split("：")[-1].split(":")[-1].split(",")
                ]
            elif "концепц" in line.lower() or "concepts" in line.lower():
                key_concepts = [
                    c.strip(" \"'[]{}")
                    for c in line.split("：")[-1].split(":")[-1].split(",")
                ]
            elif "резюме" in line.lower() or "summary" in line.lower():
                summary = line.split("：")[-1].split(":")[-1].strip()

        return {
            "category": category if category else "общее",
            "tags": [t for t in tags if t],
            "key_concepts": [c for c in key_concepts if c],
            "summary": summary if summary else "заметка",
            "domain": domain,  # поле domain
        }

    def _extract_tags_from_content(self, content: str) -> List[str]:
        """
        Извлечь теги из содержания (по ключевым словам)

        Args:
            content: текст содержания

        Returns:
            список тегов
        """
        # Распространённые технические ключевые слова
        keywords = [
            "алгоритмы",
            "структуры данных",
            "машинное обучение",
            "глубокое обучение",
            "Python",
            "JavaScript",
            "TypeScript",
            "Java",
            "фреймворк",
            "библиотека",
            "инструмент",
            "API",
            "фронтенд",
            "бэкенд",
            "фулстек",
            "база данных",
            "теория",
            "практика",
            "туториал",
            "пример",
        ]

        found = []
        content_lower = content.lower()
        for keyword in keywords:
            if keyword.lower() in content_lower:
                found.append(keyword)

        return found[:5]  # максимум 5 тегов

    def _extract_concepts_from_content(self, content: str) -> List[str]:
        """
        Извлечь ключевые концепции из содержания

        Args:
            content: текст содержания

        Returns:
            список ключевых концепций
        """
        # Заголовки с # как концепции
        concepts = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                # Убрать # и пробелы
                concept = line.lstrip("#").strip()
                if concept and len(concept) < 50:  # ограничение длины
                    concepts.append(concept)

        return concepts[:5]  # максимум 5 концепций

    def _generate_filename(self, title: str, category: str = "") -> str:
        """
        Сгенерировать имя файла

        Args:
            title: заголовок
            category: категория (опционально)

        Returns:
            имя файла с расширением
        """
        # Первая строка как имя файла
        if len(title) > 50:
            title = title[:50]

        # Очистка спецсимволов
        title = title.replace(" ", "-")
        title = "".join(c for c in title if c.isalnum() or c in "-_")

        # Добавить метку времени
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")

        if category:
            base_name = f"{timestamp}-{category}-{title}"
        else:
            base_name = f"{timestamp}-{title}"

        return f"{base_name}.md"

    def _save_knowledge(
        self, domain: str, content: str, metadata: Dict[str, any]
    ) -> Path:
        """
        Сохранить заметку

        Args:
            domain: название области
            content: содержание знания
            metadata: метаданные

        Returns:
            путь сохранённого файла
        """
        # Имя файла (_generate_filename уже с .md)
        title = content.split("\n")[0].lstrip("#").strip()
        filename = self._generate_filename(title, metadata.get("category", ""))

        # Добавить метаданные в содержание
        full_content = f"""# {title}

> **Категория**: {metadata.get('category', 'общее')}
> **Теги**: {', '.join(metadata.get('tags', []))}
> **Добавлено**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

{content}

## Ключевые концепции
{chr(10).join(f"- {c}" for c in metadata.get('key_concepts', []))}

## Резюме
{metadata.get('summary', 'нет')}
"""

        # Сохранить файл
        self.file_manager.save_knowledge(domain, filename, full_content)

        # Вернуть полный путь
        return self.file_manager.BASE_DIR / domain / "knowledge" / filename

    def _classify_content(self, content: str, domain: str) -> str:
        """
        Классифицировать содержание

        Args:
            content: содержание
            domain: область

        Returns:
            название категории
        """
        # Простая классификация по правилам
        content_lower = content.lower()

        if any(
            word in content_lower for word in ["алгоритмы", "algorithm", "метод", "method"]
        ):
            return "алгоритмы"
        elif any(
            word in content_lower for word in ["концепц", "concept", "принцип", "principle"]
        ):
            return "концепции"
        elif any(
            word in content_lower
            for word in ["инструмент", "tool", "фреймворк", "framework", "библиотека", "library"]
        ):
            return "инструмент"
        elif any(
            word in content_lower
            for word in ["практика", "practice", "кейс", "case", "проект", "project"]
        ):
            return "практика"
        elif any(
            word in content_lower for word in ["туториал", "tutorial", "руководство", "guide"]
        ):
            return "туториал"
        else:
            return "общее"

    def add(self, domain: str, input_data: str, input_type: str = None) -> str:
        """
        Добавить знание

        Args:
            domain: название области
            input_data: входные данные (текст/путь/URL)
            input_type: тип ввода (опционально, авто)

        Returns:
            результат выполнения
        """
        # Определить тип ввода
        if not input_type:
            input_type = self._identify_input_type(input_data)

        # Получить содержание
        if input_type == "text":
            content = input_data
        elif input_type == "file":
            try:
                content = self._read_file(input_data)
            except Exception as e:
                return f"❌ Ошибка чтения файла: {e}"
        elif input_type == "url":
            # Упрощённо: попросить пользователя вставить содержание
            content = f"# Знание из URL\n\nИсточник: {input_data}\n\nДобавьте содержание вручную..."
        else:
            return f"❌ Неизвестный тип ввода: {input_type}"

        # Анализ содержания
        metadata = self._analyze_content(content, domain)

        # Сохранить знание
        try:
            file_path = self._save_knowledge(domain, content, metadata)

            # Обновить сводку
            self.summary_manager.update_knowledge_summary(domain, file_path.name)

            return f"""✅ Знание добавлено

📁 Путь: {domain}/knowledge/{file_path.name}
📊 Категория: {metadata.get('category', 'общее')}
🏷️  Теги: {', '.join(metadata.get('tags', []))}
"""

        except Exception as e:
            return f"❌ Ошибка добавления знания: {e}"
