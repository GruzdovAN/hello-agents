"""Инструмент получения контекста — расширенный контекст по запросу модели

Идея (по аналогии с Claude Code):
- базовый контекст собирает ContextBuilder (системный промпт, история, сводка инструментов)
- расширенный — через этот инструмент по запросу (notes, memory, files, tests)
- модель сама решает, когда нужны дополнительные данные
"""

from typing import Dict, Any, List, Optional
import subprocess
import os

from ..base import Tool, ToolParameter


class ContextFetchTool(Tool):
    """Инструмент получения контекста
    
    Источники:
    - notes: заметки (blocker, insight, decision и т.д.)
    - memory: эпизодическая память
    - files: поиск в коде (rg + контекстные строки)
    - tests: последние ошибки тестов
    
    Сценарии:
    - недостаточно данных в базовом контексте
    - упоминание класса/функции/стека ошибки
    - вопрос «что делали раньше»
    """
    
    def __init__(
        self,
        workspace: str,
        note_tool: Optional[Any] = None,
        memory_tool: Optional[Any] = None,
        max_tokens_per_source: int = 800,
        context_lines: int = 5,
    ):
        super().__init__(
            name="context_fetch",
            description=(
                "Получить расширенный контекст, когда базового недостаточно. "
                "Источники: notes(заметки), memory(память), files(код), tests(тесты). "
                "Возвращает структурированные блоки доказательств."
            ),
        )
        self.workspace = workspace
        self.note_tool = note_tool
        self.memory_tool = memory_tool
        self.max_tokens_per_source = max_tokens_per_source
        self.context_lines = context_lines
        
        self._cache: Dict[str, str] = {}
        self._cache_max_size = 20
    
    def get_parameters(self) -> List[ToolParameter]:
        """Определения параметров по интерфейсу базового класса"""
        return [
            ToolParameter(
                name="sources",
                type="array",
                description="Список источников: notes, memory, files, tests",
                required=True,
            ),
            ToolParameter(
                name="query",
                type="string",
                description="Ключевые слова / имя символа / фрагмент стека ошибки",
                required=True,
            ),
            ToolParameter(
                name="paths",
                type="string",
                description="Glob для ограничения поиска по файлам, напр. 'src/**/*.py'",
                required=False,
            ),
            ToolParameter(
                name="budget_tokens",
                type="integer",
                description="Лимит токенов на источник, по умолчанию 800",
                required=False,
            ),
        ]
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """Выполняет получение контекста"""
        sources = parameters.get("sources", [])
        query = parameters.get("query", "")
        paths = parameters.get("paths", "")
        budget = parameters.get("budget_tokens", self.max_tokens_per_source)
        
        if not sources or not query:
            return "Ошибка: укажите sources и query"
        
        cache_key = f"{','.join(sorted(sources))}|{query}|{paths}"
        if cache_key in self._cache:
            return f"[из кэша]\n{self._cache[cache_key]}"
        
        results: List[str] = []
        
        for source in sources:
            if source == "notes":
                result = self._fetch_notes(query, budget)
            elif source == "memory":
                result = self._fetch_memory(query, budget)
            elif source == "files":
                result = self._fetch_files(query, paths, budget)
            elif source == "tests":
                result = self._fetch_tests(query, budget)
            else:
                result = f"[{source}] неизвестный источник"
            
            if result:
                results.append(result)
        
        output = "\n\n".join(results) if results else "Релевантный контекст не найден"
        
        if len(self._cache) >= self._cache_max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        self._cache[cache_key] = output
        
        return output
    
    def _fetch_notes(self, query: str, budget: int) -> str:
        """Поиск в заметках"""
        if not self.note_tool:
            return "[notes] инструмент заметок не настроен"
        
        try:
            result = self.note_tool.run({
                "action": "search",
                "query": query,
                "limit": 5,
            })
            if result and "не найдено" not in result:
                return f"[notes] релевантные заметки:\n{self._truncate(result, budget)}"
            return "[notes] релевантные заметки не найдены"
        except Exception as e:
            return f"[notes] ошибка поиска: {e}"
    
    def _fetch_memory(self, query: str, budget: int) -> str:
        """Поиск в памяти"""
        if not self.memory_tool:
            return "[memory] инструмент памяти не настроен"
        
        try:
            result = self.memory_tool.run({
                "action": "search",
                "query": query,
                "memory_types": getattr(self.memory_tool, "memory_types", ["episodic"]),
                "limit": 5,
                "min_importance": 0.0,
            })
            if result and "не найдено" not in result:
                return f"[memory] релевантная память:\n{self._truncate(result, budget)}"
            return "[memory] релевантная память не найдена"
        except Exception as e:
            return f"[memory] ошибка поиска: {e}"
    
    def _fetch_files(self, query: str, paths: str, budget: int) -> str:
        """Поиск в файлах кода"""
        try:
            cmd = ["rg", "--color=never", "-n", "-C", str(self.context_lines)]
            
            if paths:
                cmd.extend(["-g", paths])
            
            cmd.append(query)
            cmd.append(self.workspace)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.workspace,
            )
            
            output = result.stdout.strip()
            if output:
                lines = output.split("\n")
                grouped = self._group_by_file(lines)
                formatted = self._format_file_results(grouped, budget)
                return f"[files] результаты поиска в коде:\n{formatted}"
            return f"[files] совпадений по '{query}' не найдено"
        except subprocess.TimeoutExpired:
            return "[files] таймаут поиска"
        except FileNotFoundError:
            return self._fetch_files_fallback(query, paths, budget)
        except Exception as e:
            return f"[files] ошибка поиска: {e}"
    
    def _fetch_files_fallback(self, query: str, paths: str, budget: int) -> str:
        """Запасной вариант без ripgrep"""
        try:
            cmd = f"grep -rn '{query}' {self.workspace}"
            if paths:
                cmd = f"find {self.workspace} -path '{paths}' -type f | xargs grep -n '{query}'"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            output = result.stdout.strip()
            if output:
                return f"[files] результат grep:\n{self._truncate(output, budget)}"
            return f"[files] совпадений по '{query}' не найдено"
        except Exception as e:
            return f"[files] ошибка grep: {e}"
    
    def _fetch_tests(self, query: str, budget: int) -> str:
        """Информация о тестах"""
        test_patterns = [
            ".pytest_cache/v/cache/lastfailed",
            "test-results.xml",
            ".coverage",
        ]
        
        results = []
        for pattern in test_patterns:
            path = os.path.join(self.workspace, pattern)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    if query.lower() in content.lower():
                        results.append(f"[tests] {pattern}:\n{self._truncate(content, budget // 2)}")
                except Exception:
                    pass
        
        if results:
            return "\n".join(results)
        return "[tests] релевантная информация о тестах не найдена"
    
    def _group_by_file(self, lines: List[str]) -> Dict[str, List[str]]:
        """Группирует вывод ripgrep по файлам"""
        grouped: Dict[str, List[str]] = {}
        current_file = None
        
        for line in lines:
            if ":" in line:
                parts = line.split(":", 2) if ":" in line else line.split("-", 2)
                if len(parts) >= 2:
                    file_path = parts[0]
                    if file_path != current_file:
                        current_file = file_path
                        grouped[current_file] = []
                    grouped[current_file].append(line)
            elif current_file:
                grouped[current_file].append(line)
        
        return grouped
    
    def _format_file_results(self, grouped: Dict[str, List[str]], budget: int) -> str:
        """Форматирует результаты поиска по файлам"""
        output_parts = []
        tokens_used = 0
        tokens_per_file = budget // max(len(grouped), 1)
        
        for file_path, lines in grouped.items():
            content = "\n".join(lines)
            truncated = self._truncate(content, tokens_per_file)
            
            rel_path = file_path.replace(self.workspace, "").lstrip("/")
            output_parts.append(f"--- {rel_path} ---\n{truncated}")
            
            tokens_used += len(truncated) // 4
            if tokens_used >= budget:
                output_parts.append("...(дальнейшие результаты обрезаны)...")
                break
        
        return "\n\n".join(output_parts)
    
    def _truncate(self, text: str, max_tokens: int) -> str:
        """Обрезает текст до лимита токенов"""
        max_chars = max_tokens * 3
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n...(обрезано)..."
    
    def clear_cache(self):
        """Очищает кэш"""
        self._cache.clear()
