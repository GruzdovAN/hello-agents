"""Инструмент памяти"""

from typing import List, Dict, Any, Optional
import re

from hello_agents.tools import Tool, ToolParameter, ToolResponse, tool_action


class MemoryTool(Tool):
    """инструменты управления памятью

    Может быть расширен на несколько подинструментов:
    - Memory_search: Поиск в памяти (возвращает контекст с номером строки)
    - Memory_get: прочитать определенный файл памяти или диапазон строк.
    - Memory_add: добавить ежедневную память
    - Memory_update_longterm: обновление Долгосрочная память
    - Memory_list: Список файлов памяти"""

    def __init__(self, workspace_manager):
        """Инструмент инициализации памяти

        Аргументы:
            workspace_manager: экземпляр рабочего пространства Менеджера"""
        super().__init__(
            name="memory",
description="память管理инструмент，поддержкаПоиск、读取、添加和обновлениепамять",
            expandable=True
        )
        self.workspace = workspace_manager

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        """Выполнение по умолчанию: Поиск в памяти."""
        keyword = parameters.get("keyword", "")
        return self._search_memory(keyword)

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="keyword",
                type="string",
                description="Ключевое слово",
                required=True
            )
        ]

    def _search_memory(self, keyword: str, context_lines: int = 3) -> ToolResponse:
        """Поиск в памяти (расширенная версия, возвращает контекст с номером строки)"""
        if not keyword:
            return ToolResponse.error(
                code="INVALID_INPUT",
                message="Пожалуйста,提供Ключевое слово"
            )

        # Используйте расширенный поиск

        results = self.workspace.search_memory_enhanced(
            keyword,
            context_lines=context_lines
        )

        if not results:
            return ToolResponse.success(
text=f"Не найдено совпадений для '{keyword}' 相关的память",
                data={"results": [], "keyword": keyword}
            )

        # Форматирование результатов

        formatted_parts = []
        total_matches = 0

        for r in results:
            source = r["source"]
            matches = r["matches"]
            total_matches += len(matches)

            for m in matches:
                start = m["start_line"]
                end = m["end_line"]
                content = m["content"]
line_range = f"行 {start}" if start == end else f"行 {start}-{end}"
                formatted_parts.append(
                    f"**{source}** ({line_range}):\n```\n{content}\n```"
                )

        return ToolResponse.success(
text=f"Найдено {total_matches} совпадений с '{keyword}':\n\n" + "\n\n".join(formatted_parts),
            data={"results": results, "count": total_matches, "keyword": keyword}
        )

    @tool_action("memory_search", "Поискисторияпамять")
    def _search(self, keyword: str, context_lines: int = 3) -> str:
        """Поиск в памяти

        Аргументы:
            ключевое слово: Ключевое слово
            context_lines: Строка контекста, по умолчанию 3"""
        response = self._search_memory(keyword, context_lines)
        return response.text

    @tool_action("memory_get", "读取特定памятьфайл或行范围")
    def _get_memory(
        self,
        filename: str = None,
        start_line: int = None,
        end_line: int = None,
        lines: str = None,
    ) -> str:
        """Прочитать содержимое файла памяти

        Аргументы:
            имя_файла: имя файла (MEMORY.md или ГГГГ-ММ-ДД.md), по умолчанию — сегодняшний дневник.
            start_line: номер начальной строки (начиная с 1)
            end_line: номер конечной строки
            линии: строка диапазона строк, например «10-20» или «15»."""
        from datetime import datetime

        # Параметр строк анализа

        if lines:
            match = re.match(r"(\d+)(?:\s*-\s*(\d+))?", lines)
            if match:
                start_line = int(match.group(1))
                if match.group(2):
                    end_line = int(match.group(2))

        # Имя файла по умолчанию

        if not filename:
            filename = datetime.now().strftime("%Y-%m-%d.md")

        # Убедитесь, что имя файла заканчивается на .md.

        if not filename.endswith(".md"):
            filename += ".md"

        # прочитать файл

        content = self.workspace.read_memory_lines(filename, start_line, end_line)

        if content is None:
            available = self._list_memory_files_brief()
return f"файл '{filename}' не существует。可用файл:\n{available}"

        if not content:
return f"файл '{filename}' пуст"

        display_name = filename
        if start_line or end_line:
range_str = f"行 {start_line или 1}"
            if end_line and end_line != start_line:
                range_str += f"-{end_line}"
            display_name += f" ({range_str})"

        return f"**{display_name}**:\n```\n{content}\n```"

    @tool_action("memory_add", "添加содержимое到今日память")
    def _add_daily(self, content: str, category: str = None) -> str:
        """Добавить ежедневную память

        Аргументы:
            содержание: Содержимое записи
            Категория: метка категории (предпочтение/решение/субъект/факт), необязательно."""
        if category:
            # Использовать тегированное хранилище

            self.workspace.append_classified_memory(content, category)
            return f"Добавлено в память за сегодня [{category}]: {content[:50]}..."
        else:
            # Используйте оригинальный метод

            self.workspace.append_to_daily_memory(content)
            return f"Добавлено в память за сегодня: {content[:50]}..."

    @tool_action("memory_update_longterm", "обновлениедолгосрочнаяпамять")
    def _update_longterm(self, content: str) -> str:
        """Обновить Долгосрочную память

        Аргументы:
            content: Контент для добавления в Долгосрочную память"""
        current = self.workspace.load_config("MEMORY") or ""
        updated = current + f"\n\n## 新增\n\n{content}\n"
        self.workspace.save_config("MEMORY", updated)
        return "ужеобновлениедолгосрочнаяпамять"

    @tool_action("memory_list", "列出所有памятьфайл")
    def _list(self) -> str:
        """Список файлов памяти"""
        files = self.workspace.list_memory_files()

        if not files:
            return "пока нетпамятьфайл"

        lines = ["# памятьфайлсписок\n"]

        # Группировать по типу

        longterm = [f for f in files if f["type"] == "longterm"]
        daily = [f for f in files if f["type"] == "daily"]

        if longterm:
            lines.append("## долгосрочнаяпамять")
            for f in longterm:
                size_kb = f["size"] / 1024
                lines.append(f"- **{f['name']}** ({size_kb:.1f} KB)")

        if daily:
            lines.append("\n## дневнаяпамять")
            for f in daily:
                size_kb = f["size"] / 1024
                lines.append(f"- **{f['name']}** ({size_kb:.1f} KB)")

        return "\n".join(lines)

    @tool_action("memory_cleanup", "очисткаустаревший的дневнаяпамять")
    def _cleanup(self, days: int = 30) -> str:
        """Очистить устаревшую память

        Аргументы:
            дни: количество дней хранения. Если число превышает это число, оно будет очищено. По умолчанию — 30 дней."""
        deleted = self.workspace.cleanup_old_memories(days)

        if not deleted:
            return f"没有需要очистка的память（保留最近 {days} 天）"

        return f"Очищено {len(deleted)} устаревших файлов памяти:\n" + "\n".join(f"- {f}" for f in deleted)

    def _list_memory_files_brief(self) -> str:
        """Краткий список файлов памяти"""
        files = self.workspace.list_memory_files()
        if not files:
вернуть «нет»
        return "\n".join(f"- {f['name']}" for f in files)
