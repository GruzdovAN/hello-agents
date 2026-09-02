"""Реестр инструментов — нативная система инструментов HelloAgents"""

from typing import Optional, Any, Callable
import json
from .base import Tool

class ToolRegistry:
    """
    Реестр инструментов HelloAgents

    Регистрация, управление и выполнение инструментов.
    Поддерживаются два способа регистрации:
    1. Объект Tool (рекомендуется)
    2. Прямая регистрация функции (упрощённый способ)
    """

    def __init__(self):
        self._tools: dict[str, Tool] = {}
        self._functions: dict[str, dict[str, Any]] = {}

    def register_tool(self, tool: Tool):
        """
        Регистрирует объект Tool

        Args:
            tool: экземпляр Tool
        """
        if tool.name in self._tools:
            print(f"⚠️ Предупреждение: инструмент '{tool.name}' уже существует и будет перезаписан.")

        self._tools[tool.name] = tool
        print(f"✅ Инструмент '{tool.name}' зарегистрирован.")

    def register_function(self, name: str, description: str, func: Callable[[str], str]):
        """
        Регистрирует функцию как инструмент (упрощённый способ)

        Args:
            name: имя инструмента
            description: описание инструмента
            func: функция инструмента: принимает строку, возвращает строку
        """
        if name in self._functions:
            print(f"⚠️ Предупреждение: инструмент '{name}' уже существует и будет перезаписан.")

        self._functions[name] = {
            "description": description,
            "func": func
        }
        print(f"✅ Инструмент '{name}' зарегистрирован.")

    def unregister(self, name: str):
        """Удаляет инструмент из реестра"""
        if name in self._tools:
            del self._tools[name]
            print(f"🗑️ Инструмент '{name}' удалён из реестра.")
        elif name in self._functions:
            del self._functions[name]
            print(f"🗑️ Инструмент '{name}' удалён из реестра.")
        else:
            print(f"⚠️ Инструмент '{name}' не существует.")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Возвращает объект Tool"""
        return self._tools.get(name)

    def get_function(self, name: str) -> Optional[Callable]:
        """Возвращает функцию инструмента"""
        func_info = self._functions.get(name)
        return func_info["func"] if func_info else None

    def execute_tool(self, name: str, input_text: str) -> str:
        """
        Выполняет инструмент

        Args:
            name: имя инструмента
            input_text: входные параметры

        Returns:
            Результат выполнения инструмента
        """
        if name in self._tools:
            tool = self._tools[name]
            try:
                raw = (input_text or "").strip()
                
                # Предобработка: если ввод содержит перевод строки и другой Action, берём только первую строку
                if '\n' in raw and 'Action:' in raw:
                    lines = raw.split('\n')
                    raw = lines[0].strip()

                def _try_json(txt: str):
                    try:
                        return json.loads(txt)
                    except Exception:
                        return None

                obj = None
                if raw.startswith("{") and raw.endswith("}"):
                    obj = _try_json(raw)
                if obj is None and raw.startswith("{") and raw.endswith("}]"):
                    obj = _try_json(raw[:-1].strip())
                if obj is None and raw.startswith("[") and raw.endswith("]"):
                    arr = _try_json(raw)
                    if isinstance(arr, list) and len(arr) == 1 and isinstance(arr[0], dict):
                        obj = arr[0]
                if obj is None and raw.endswith("}]") and raw.count("{") == 1 and raw.count("}") == 2:
                    obj = _try_json(raw[:-1])
                if obj is None and "{" in raw and "}" in raw:
                    try:
                        import re
                        def extract_first_json_object(text: str):
                            """Извлекает из текста первый полный JSON-объект"""
                            start = text.find('{')
                            if start == -1:
                                return None
                            depth = 0
                            in_string = False
                            escape = False
                            for i, c in enumerate(text[start:], start):
                                if escape:
                                    escape = False
                                    continue
                                if c == '\\' and in_string:
                                    escape = True
                                    continue
                                if c == '"' and not escape:
                                    in_string = not in_string
                                    continue
                                if in_string:
                                    continue
                                if c == '{':
                                    depth += 1
                                elif c == '}':
                                    depth -= 1
                                    if depth == 0:
                                        return text[start:i+1]
                            return None
                        
                        json_str = extract_first_json_object(raw)
                        if json_str:
                            obj = json.loads(json_str)
                    except Exception:
                        pass

                if isinstance(obj, dict):
                    return tool.run(obj)

                params = tool.get_parameters()
                required = [p for p in params if p.required]
                if len(required) == 1:
                    return tool.run({required[0].name: input_text})

                if any(p.name == "input" for p in params):
                    return tool.run({"input": input_text})

                return (
                    f"Ошибка: инструмент '{name}' требует структурированные параметры. "
                    "Используйте JSON, например: tool[{{\"param\":\"value\"}}]"
                )
            except Exception as e:
                return f"Ошибка: при выполнении инструмента '{name}' возникло исключение: {str(e)}"

        elif name in self._functions:
            func = self._functions[name]["func"]
            try:
                return func(input_text)
            except Exception as e:
                return f"Ошибка: при выполнении инструмента '{name}' возникло исключение: {str(e)}"

        else:
            return f"Ошибка: инструмент с именем '{name}' не найден."

    def get_tools_description(self) -> str:
        """
        Возвращает форматированное описание всех доступных инструментов

        Returns:
            Описание инструментов для построения промпта
        """
        descriptions = []

        for tool in self._tools.values():
            descriptions.append(f"- {tool.name}: {tool.description}")

        for name, info in self._functions.items():
            descriptions.append(f"- {name}: {info['description']}")

        return "\n".join(descriptions) if descriptions else "Нет доступных инструментов"

    def list_tools(self) -> list[str]:
        """Список имён всех инструментов"""
        return list(self._tools.keys()) + list(self._functions.keys())

    def get_all_tools(self) -> list[Tool]:
        """Возвращает все объекты Tool"""
        return list(self._tools.values())

    def clear(self):
        """Очищает все инструменты"""
        self._tools.clear()
        self._functions.clear()
        print("🧹 Все инструменты очищены.")

global_registry = ToolRegistry()
