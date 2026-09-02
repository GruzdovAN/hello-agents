"""Менеджер рабочего пространства"""

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Set


# Список конфигурационных файлов
CONFIG_FILES = [
    "BOOTSTRAP",
    "IDENTITY",
    "SOUL",
    "USER",
    "MEMORY",
    "AGENTS",
    "HEARTBEAT",
]

# Каталог шаблонов (относительно текущего файла)
TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_default_global_config() -> dict:
    """Глобальная конфигурация по умолчанию (из шаблона)"""
    template_path = TEMPLATES_DIR / "config.json"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"llm": {"model_id": "", "base_url": "", "api_key": ""}}


class WorkspaceManager:
    """Менеджер рабочего пространства

    Отвечает за:
    - Создание и управление структурой каталогов
    - Загрузка и сохранение конфигурационных файлов
    - Управление файлами памяти (ежедневная и долгосрочная)
    """

    def __init__(self, workspace_path: str):
        """Инициализация менеджера рабочего пространства

        Args:
            workspace_path: Путь к корневому каталогу рабочего пространства
        """
        self.workspace_path = os.path.expanduser(workspace_path)
        self.memory_path = os.path.join(self.workspace_path, "memory")
        self.sessions_path = os.path.join(self.workspace_path, "sessions")

    # ==================== Чтение глобальной конфигурации ====================

    def load_global_config(self) -> dict:
        """Загрузите глобальный config.json

        Возврат:
            Словарь конфигурации; пустой, если файл не найден"""
        config_path = os.path.expanduser("~/.helloclaw/config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def get_llm_config(self) -> dict:
        """Получить конфигурацию LLM

        Приоритет: config.json > env > по умолчанию

        Возврат:
            Словарь, содержащий model_id, api_key, base_url"""
        global_config = self.load_global_config()
        llm_config = global_config.get("llm", {})

        return {
            "model_id": llm_config.get("model_id") or os.getenv("LLM_MODEL_ID") or "glm-4",
            "api_key": llm_config.get("api_key") or os.getenv("LLM_API_KEY"),
            "base_url": llm_config.get("base_url") or os.getenv("LLM_BASE_URL"),
        }

    # ==================== Проверка онбординга ====================

    def is_onboarding_completed(self) -> bool:
        """Проверка завершения онбординга

        Завершён, когда BOOTSTRAP.md отсутствует.
        При заданной личности BOOTSTRAP.md удаляется.

        Returns:
            Завершён ли онбординг
        """
        # Сначала проверьте, нужно ли удалять BOOTSTRAP (личность определена, но файл все еще существует)

        self._check_and_delete_bootstrap()

        return not os.path.exists(self.get_config_path("BOOTSTRAP"))

    def ensure_workspace_exists(self):
        """Создать рабочее пространство при необходимости

        Если нет — создать каталоги и конфигурацию
        """
        # Создание каталогов
        os.makedirs(self.workspace_path, exist_ok=True)
        os.makedirs(self.memory_path, exist_ok=True)
        os.makedirs(self.sessions_path, exist_ok=True)

        # Создать конфиг по умолчанию
        for config_name in CONFIG_FILES:
            config_path = self.get_config_path(config_name)
            if not os.path.exists(config_path):
                self._create_default_config(config_name)

        # Проверьте, нужно ли удалить BOOTSTRAP (миграция устаревшей рабочей области).

        self._check_and_delete_bootstrap()

    def get_config_path(self, name: str) -> str:
        """Путь к конфигурационному файлу

        Args:
            name: Имя файла (без расширения)

        Returns:
            Полный путь к файлу
        """
        return os.path.join(self.workspace_path, f"{name}.md")

    def load_config(self, name: str) -> Optional[str]:
        """Загрузить содержимое файла конфигурации

        Аргументы:
            имя: имя файла конфигурации

        Возврат:
            Содержимое; Нет, если нет"""
        config_path = self.get_config_path(name)
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def save_config(self, name: str, content: str):
        """Сохранить файл конфигурации

        Аргументы:
            имя: имя файла конфигурации
            содержимое: содержимое файла конфигурации"""
        config_path = self.get_config_path(name)
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)

        # При сохранении IDENTITY — проверить BOOTSTRAP
        if name == "IDENTITY":
            self._check_and_delete_bootstrap()

    def list_configs(self) -> list:
        """Список всех файлов конфигурации

        Возврат:
            Список имён конфигов"""
        configs = []
        for name in CONFIG_FILES:
            config_path = self.get_config_path(name)
            if os.path.exists(config_path):
                configs.append(name)
        return configs

    def get_daily_memory_path(self, date: datetime = None) -> str:
        """Путь к ежедневной памяти

        Args:
            date: Дата (по умолчанию сегодня)

        Returns:
            Путь к ежедневной памяти
        """
        date = date or datetime.now()
        filename = date.strftime("%Y-%m-%d.md")
        return os.path.join(self.memory_path, filename)

    def append_to_daily_memory(self, content: str, date: datetime = None):
        """Добавить в ежедневную память

        Args:
            content: Содержимое записи
            date: Дата (по умолчанию сегодня)
        """
        memory_path = self.get_daily_memory_path(date)
        timestamp = datetime.now().strftime("%H:%M:%S")

        with open(memory_path, "a", encoding="utf-8") as f:
            f.write(f"\n## {timestamp}\n\n{content}\n")

    def search_memory(self, keyword: str, include_daily: bool = True) -> list:
        """Поиск в памяти

        Args:
            keyword: Ключевое слово
            include_daily: Включать ежедневную память

        Returns:
            Совпавшие фрагменты
        """
        results = []

        # Поиск в долгосрочной памяти
        memory_content = self.load_config("MEMORY")
        if memory_content and keyword.lower() in memory_content.lower():
            results.append({
                "source": "MEMORY.md",
                "content": memory_content,
            })

        # Поиск в ежедневной памяти
        if include_daily:
            for filename in os.listdir(self.memory_path):
                if filename.endswith(".md"):
                    filepath = os.path.join(self.memory_path, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        if keyword.lower() in content.lower():
                            results.append({
                                "source": f"memory/{filename}",
                                "content": content,
                            })

        return results

    def search_memory_enhanced(
        self,
        keyword: str,
        include_daily: bool = True,
        context_lines: int = 3,
    ) -> list:
        """Расширенный поиск по номерам строк

        Аргументы:
            ключевое слово: Ключевое слово
            include_daily: Включать ежедневную память
            context_lines: Просмотреть контекст

        Возврат:
            Совпавшие фрагменты, включая номер строки и контекст"""
        results = []

        # Поиск в долгосрочной памяти
        memory_content = self.load_config("MEMORY")
        if memory_content:
            matches = self._find_matches_with_context(
                memory_content, keyword, context_lines
            )
            if matches:
                results.append({
                    "source": "MEMORY.md",
                    "matches": matches,
                })

        # Поиск в ежедневной памяти
        if include_daily:
            for filename in sorted(os.listdir(self.memory_path)):
                if filename.endswith(".md"):
                    filepath = os.path.join(self.memory_path, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    matches = self._find_matches_with_context(
                        content, keyword, context_lines
                    )
                    if matches:
                        results.append({
                            "source": f"memory/{filename}",
                            "matches": matches,
                        })

        return results

    def _find_matches_with_context(
        self,
        content: str,
        keyword: str,
        context_lines: int = 3,
    ) -> list:
        """Поиск контекстоми номеров строк

        Аргументы:
            содержимое: содержимое файла
            ключевое слово: Ключевое слово
            context_lines: Просмотреть контекст

        Возврат:
            Список совпадающих фрагментов, каждый из которых содержит начальную_строку, конечную_строку и содержимое."""
        lines = content.split("\n")
        keyword_lower = keyword.lower()

        # Найти все совпадающие номера строк

        matched_lines = set()
        for i, line in enumerate(lines):
            if keyword_lower in line.lower():
                # Добавьте совпадающие строки и их контекст

                for j in range(
                    max(0, i - context_lines),
                    min(len(lines), i + context_lines + 1),
                ):
                    matched_lines.add(j)

        if not matched_lines:
            return []

        # Объединить соседние диапазоны строк

        sorted_lines = sorted(matched_lines)
        ranges = []
        start = sorted_lines[0]
        end = sorted_lines[0]

        for line_num in sorted_lines[1:]:
            if line_num <= end + 1:
                end = line_num
            else:
                ranges.append((start, end))
                start = line_num
                end = line_num
        ranges.append((start, end))

        # Результаты сборки

        results = []
        for start_line, end_line in ranges:
            # Номера строк начинаются с 1

            context = "\n".join(
                f"{i + 1:4d} | {lines[i]}"
                for i in range(start_line, end_line + 1)
            )
            results.append({
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "content": context,
            })

        return results

    def read_memory_lines(
        self,
        filename: str,
        start_line: int = None,
        end_line: int = None,
    ) -> Optional[str]:
        """Чтение записанных строк

        Аргументы:
            имя_файла: имя файла (MEMORY.md или ГГГГ-ММ-ДД.md)
            start_line: начальная строка (начиная с 1), по умолчанию — 1.
            end_line: Конечная строка, по умолчанию — конец файла.

        Возврат:
            Содержимое с номером строки, возвращает None, если файл не существует."""
        # Определить путь к файлу

        if filename == "MEMORY.md":
            filepath = self.get_config_path("MEMORY")
        else:
            filepath = os.path.join(self.memory_path, filename)

        if not os.path.exists(filepath):
            return None

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            return ""

        # значение по умолчанию

        start = max(1, start_line or 1) - 1  # Преобразовать в 0-индексированный

        end = end_line or len(lines)

        # Прочитать указанный диапазон

        selected_lines = lines[start:end]

        # Форматированный вывод (с номерами строк)

        result_lines = []
        for i, line in enumerate(selected_lines, start=start + 1):
            # Удалить конечную новую строку и добавить номер строки

            result_lines.append(f"{i:4d} | {line.rstrip()}")

        return "\n".join(result_lines)

    def list_memory_files(self) -> list:
        """Список файлов памяти

        Returns:
            Сведения о файлах памяти
        """
        files = []

        # Долгосрочная память
        memory_path = self.get_config_path("MEMORY")
        if os.path.exists(memory_path):
            stat = os.stat(memory_path)
            files.append({
                "name": "MEMORY.md",
                "type": "longterm",
                "size": stat.st_size,
                "updated_at": stat.st_mtime,
            })

        # Ежедневная память
        if os.path.exists(self.memory_path):
            for filename in sorted(os.listdir(self.memory_path), reverse=True):
                if filename.endswith(".md"):
                    filepath = os.path.join(self.memory_path, filename)
                    stat = os.stat(filepath)
                    files.append({
                        "name": filename,
                        "type": "daily",
                        "size": stat.st_size,
                        "updated_at": stat.st_mtime,
                    })

        return files

    def _check_and_delete_bootstrap(self):
        """Удалить BOOTSTRAP при заданной личности"""
        bootstrap_path = self.get_config_path("BOOTSTRAP")

        # BOOTSTRAP не существует, обрабатывать не нужно

        if not os.path.exists(bootstrap_path):
            return

        # Проверить личность Задана ли

        if self._is_identity_established():
            os.remove(bootstrap_path)

    def _is_identity_established(self) -> bool:
        """Личность задана (поле имени заполнено)

        Returns:
            Задана ли личность
        """
        identity = self.load_config("IDENTITY")
        if not identity:
            return False

        # Попробуйте сопоставить поле имени

        # Формат: - **Имя:** xxx или - **Имя:** xxx

match = re.search(r'\*\*Name[::]\*\*\s*(.+?)(?:\n|$)', тождество)
        if match:
            name = match.group(1).strip()
            # Если имя не является заполнителем, личность считается установленной.

            # Характеристики заполнителя: начинается с подчеркивания, содержит «выберите один», содержит «(»

if name, а не name.startswith('_') и '选一个' не по имени и '（' не по имени:
                return True

        return False

    def _create_default_config(self, name: str):
        """Создать конфиг по умолчанию

        Шаблон или базовый вариант

        Аргументы:
            имя: имя файла конфигурации"""
        template_path = TEMPLATES_DIR / f"{name}.md"

        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            # Вернуться к базовому шаблону

            content = f"# {name}\n\n(ожидает настройки)"

        # Заменить заполнитель даты

        content = content.replace("{date}", datetime.now().strftime("%Y-%m-%d"))

        self.save_config(name, content)

    def reset_to_templates(self, reset_sessions: bool = False, reset_memory: bool = False, reset_global_config: bool = False):
        """Сброс к начальным шаблонам

        Args:
            reset_sessions: Очистить сессии
            reset_memory: Очистить ежедневную память
            reset_global_config: Сбросить глобальный конфиг

        Внимание: перезапись всех конфигов!
        """
        # Сброс файлов конфигурации (включая BOOTSTRAP)

        for config_name in CONFIG_FILES:
            self._create_default_config(config_name)

        # очистить сеанс

        if reset_sessions:
            self._clear_sessions()

        # Очистить ежедневную память

        if reset_memory:
            self._clear_daily_memory()

        # Сбросить глобальную конфигурацию

        if reset_global_config:
            self._reset_global_config()

    def _clear_sessions(self):
        """Очистить все разговоры"""
        if os.path.exists(self.sessions_path):
            for filename in os.listdir(self.sessions_path):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.sessions_path, filename)
                    os.remove(filepath)

    def _clear_daily_memory(self):
        """Очистить все Ежедневная память"""
        if os.path.exists(self.memory_path):
            for filename in os.listdir(self.memory_path):
                if filename.endswith(".md"):
                    filepath = os.path.join(self.memory_path, filename)
                    os.remove(filepath)

    def _reset_global_config(self):
        """Сбросить файл глобальной конфигурации"""
        config_path = os.path.expanduser("~/.helloclaw/config.json")
        os.makedirs(os.path.dirname(config_path), exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(get_default_global_config(), f, indent=2, ensure_ascii=False)

    # ==================== Сводки сессий ====================

    def save_session_summary(self, filename: str, content: str):
        """Сохранение сводки сеанса в каталог памяти

        Аргументы:
            имя_файла: имя файла (например, 2026-02-26-project-discussion.md)
            содержание: обобщить содержание"""
        filepath = os.path.join(self.memory_path, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def list_session_summaries(self) -> list:
        """Список всех сводок сеансов

        Возврат:
            Список файлов сводки сеанса"""
        summaries = []

        if not os.path.exists(self.memory_path):
            return summaries

        for filename in sorted(os.listdir(self.memory_path), reverse=True):
            if filename.endswith(".md") and "-" in filename:
                # Исключить простой формат даты (Ежедневная память)

                if re.match(r"\d{4}-\d{2}-\d{2}\.md$", filename):
                    continue

                # Формат сводки сеанса: ГГГГ-ММ-ДД-slug.md.

                filepath = os.path.join(self.memory_path, filename)
                stat = os.stat(filepath)

                # Попробуйте извлечь слизняк

                match = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", filename)
                if match:
                    date_str = match.group(1)
                    slug = match.group(2)
                else:
                    date_str = ""
                    slug = filename[:-3]

                summaries.append({
                    "filename": filename,
                    "date": date_str,
                    "slug": slug,
                    "size": stat.st_size,
                    "updated_at": stat.st_mtime,
                })

        return summaries

    def load_session_summary(self, filename: str) -> Optional[str]:
        """Загрузить сводный контент сеанса

        Аргументы:
            имя файла: имя файла

        Возврат:
            Обобщить содержимое, вернуть None, если оно не существует."""
        filepath = os.path.join(self.memory_path, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return None

    # ==================== Классификация и дедупликация памяти ====================

    def append_classified_memory(
        self,
        content: str,
        category: str,
        date: datetime = None,
    ):
        """Добавьте памяти с помощью тегов категорий

        Аргументы:
            содержание: Содержимое записи
            категория: классификационная метка (предпочтение/решение/субъект/факт)
            дата: Дата (по сегодняшнему по умолчанию)"""
        memory_path = self.get_daily_memory_path(date)
        timestamp = datetime.now().strftime("%H:%M")

        # Убедитесь, что файл существует и имеет заголовок

        if not os.path.exists(memory_path):
            date_str = (date or datetime.now()).strftime("%Y-%m-%d")
            with open(memory_path, "w", encoding="utf-8") as f:
                f.write(f"# {date_str}\n")

        # Добавьте памяти с помощью тегов категорий

        with open(memory_path, "a", encoding="utf-8") as f:
            f.write(f"\n## {timestamp} - автозахват\n\n- [{category}] {content}\n")

    def check_duplicate_memory(self, content: str, threshold: float = 0.7) -> bool:
        """Проверьте память на наличие дубликатов

        Определите, дублируется ли он с существующими воспоминаниями, с помощью обнаружения перекрытия ключевых слов.

        Аргументы:
            контент: контент, который нужно проверить
            порог: порог сходства, по умолчанию 0,7

        Возврат:
            Повторять ли (True указывает на повторение и его следует пропустить)"""
        # Извлечь ключевые слова

        keywords = self._extract_keywords(content)
        if not keywords:
            return False

        # Проверьте сегодняшнюю память

        today_path = self.get_daily_memory_path()
        if os.path.exists(today_path):
            with open(today_path, "r", encoding="utf-8") as f:
                today_content = f.read()
            if self._calculate_overlap(keywords, today_content) >= threshold:
                return True

        # Проверить Долгосрочную память

        longterm_content = self.load_config("MEMORY")
        if longterm_content:
            if self._calculate_overlap(keywords, longterm_content) >= threshold:
                return True

        # Проверьте ближайшую ежедневную память

        recent_files = self.get_recent_memory_day(days=2)
        for filename in recent_files:
            filepath = os.path.join(self.memory_path, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    file_content = f.read()
                if self._calculate_overlap(keywords, file_content) >= threshold:
                    return True

        return False

    def cleanup_old_memories(self, days: int = 30) -> List[str]:
        """Очистка истекла Ежедневная память

        Аргументы:
            дней: количество дней, в течение которых он будет храниться, после чего он будет очищен.

        Возврат:
            Список имен удаленных файлов"""
        deleted = []
        cutoff_date = datetime.now() - timedelta(days=days)

        if not os.path.exists(self.memory_path):
            return deleted

        for filename in os.listdir(self.memory_path):
            if not filename.endswith(".md"):
                continue

            # Попробуйте разобрать дату

            try:
                date_str = filename.replace(".md", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                # Проверьте, истек ли срок действия

                if file_date < cutoff_date:
                    filepath = os.path.join(self.memory_path, filename)
                    os.remove(filepath)
                    deleted.append(filename)
            except ValueError:
                # Имя файла не в формате даты, пропустите

                continue

        return deleted

    def get_recent_memory_day(self, days: int = 2) -> List[str]:
        """Получить список имен файлов памяти за последние N дней.

        Аргументы:
            дни: количество дней

        Возврат:
            Список имен файлов памяти (формат ГГГГ-ММ-ДД.md)"""
        files = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            filename = date.strftime("%Y-%m-%d.md")
            filepath = os.path.join(self.memory_path, filename)
            if os.path.exists(filepath):
                files.append(filename)
        return files

    def _extract_keywords(self, text: str) -> Set[str]:
        """Ключевые слова (фильтр китайских стоп-слов)

        Аргументы:
            текст: введите текст

        Возврат:
            коллекция ключевых слов"""
        # Таблица китайских стоп-слов
        stopwords = {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
            "什么", "这个", "那个", "可以", "就是", "这样", "然后",
            "还是", "但是", "因为", "所以", "如果", "虽然", "可能",
            "需要", "应该", "或者", "而且", "уже经", "还有", "一直",
            "的话", "一下", "一些", "一点", "东西", "知道", "觉得",
            "喜欢", "偏好", "пользователь", "记住", "记下", "决定", "选定",
        }

        # Regex для китайских и английских слов
        # Китайский: 2+ иероглифа
        # Английский: 3+ буквы
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        english_words = re.findall(r'[a-zA-Z]{3,}', text)

        keywords = set()

        # Китайские слова без стоп-слов
        for word in chinese_words:
            if word not in stopwords:
                keywords.add(word.lower())

        # Английские слова в нижнем регистре
        for word in english_words:
            keywords.add(word.lower())

        return keywords

    def _calculate_overlap(self, keywords: Set[str], text: str) -> float:
        """Доля совпадений ключевых слов

        Аргументы:
            ключевые слова: коллекция ключевых слов
            текст: целевой текст

        Возврат:
            Коэффициент совпадения (0,0 – 1,0)"""
        if not keywords:
            return 0.0

        text_lower = text.lower()
        matched = sum(1 for kw in keywords if kw in text_lower)

        return matched / len(keywords)
