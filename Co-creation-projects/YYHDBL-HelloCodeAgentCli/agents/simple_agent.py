"""SimpleAgent — на базе нативного API OpenAI"""

from typing import Optional, Iterator, TYPE_CHECKING, Callable
import re

from core.agent import Agent
from core.llm import HelloAgentsLLM
from core.config import Config
from core.message import Message

if TYPE_CHECKING:
    from tools.registry import ToolRegistry

class SimpleAgent(Agent):
    """Простой диалоговый агент с опциональными инструментами"""
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True,
        tool_confirm_callback: Optional[Callable[[str, dict], bool]] = None,
    ):
        """
        Инициализирует SimpleAgent
        
        Args:
            name: Имя агента
            llm: Экземпляр LLM
            system_prompt: Системный промпт
            config: Объект конфигурации
            tool_registry: Реестр инструментов (опционально)
            enable_tool_calling: Включить вызов инструментов (только с tool_registry)
        """
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        self.tool_confirm_callback = tool_confirm_callback
    
    def _get_enhanced_system_prompt(self) -> str:
        """Строит расширенный системный промпт с информацией об инструментах"""
        base_prompt = self.system_prompt or "Вы — полезный ИИ-ассистент."
        
        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt
        
        # Описание инструментов
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "Нет доступных инструментов":
            return base_prompt
        
        tools_section = "\n\n## Доступные инструменты\n"
        tools_section += "Доступные инструменты для ответа:\n"
        tools_section += tools_description + "\n"

        tools_section += "\n## Формат вызова инструментов\n"
        tools_section += "Для вызова инструмента используйте формат:\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n\n"

        tools_section += "### Формат параметров\n"
        tools_section += "1. **Несколько параметров**: `key=value`, через запятую\n"
        tools_section += "   Пример: `[TOOL_CALL:calculator_multiply:a=12,b=8]`\n"
        tools_section += "   Пример: `[TOOL_CALL:filesystem_read_file:path=README.md]`\n\n"
        tools_section += "2. **Один параметр**: `key=value`\n"
        tools_section += "   Пример: `[TOOL_CALL:search:query=Python]`\n\n"
        tools_section += "3. **Простой запрос**: можно передать текст напрямую\n"
        tools_section += "   Пример: `[TOOL_CALL:search:Python]`\n\n"

        tools_section += "### Важно\n"
        tools_section += "- Имена параметров должны совпадать с определением инструмента\n"
        tools_section += "- Числа без кавычек: `a=12`, не `a=\"12\"`\n"
        tools_section += "- Пути к файлам: `path=README.md`\n"
        tools_section += "- Результат инструмента вставляется в диалог для продолжения ответа\n"

        return base_prompt + tools_section
    
    def _parse_tool_calls(self, text: str) -> list:
        """Разбирает вызовы инструментов в тексте"""
        pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        matches = re.findall(pattern, text)
        
        tool_calls = []
        for tool_name, parameters in matches:
            tool_calls.append({
                'tool_name': tool_name.strip(),
                'parameters': parameters.strip(),
                'original': f'[TOOL_CALL:{tool_name}:{parameters}]'
            })
        
        return tool_calls
    
    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """Выполняет вызов инструмента"""
        if not self.tool_registry:
            return f"❌ Ошибка: реестр инструментов не настроен"

        try:
            # Возвращает объект Tool
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                return f"❌ Ошибка: инструмент не найден '{tool_name}'"

            # Умный разбор параметров
            param_dict = self._parse_tool_parameters(tool_name, parameters)

            # Интерактивное подтверждение (решает верхний уровень)
            if self.tool_confirm_callback is not None:
                try:
                    allowed = bool(self.tool_confirm_callback(tool_name, param_dict))
                except Exception as e:
                    return f"❌ Ошибка подтверждения вызова инструмента: {str(e)}"
                if not allowed:
                    return "⛔️ Вызов инструмента отменён (требуется подтверждение пользователя)."

            # Вызов инструмента
            result = tool.run(param_dict)
            return f"🔧 Инструмент {tool_name} — результат:\n{result}"

        except Exception as e:
            return f"❌ Вызов инструмента не удался: {str(e)}"

    def _parse_tool_parameters(self, tool_name: str, parameters: str) -> dict:
        """Умный разбор параметров инструмента"""
        import json
        param_dict = {}

        # Попытка разбора JSON
        if parameters.strip().startswith('{'):
            try:
                param_dict = json.loads(parameters)
                # JSON разобран — преобразование типов
                param_dict = self._convert_parameter_types(tool_name, param_dict)
                return param_dict
            except json.JSONDecodeError:
                # JSON не разобран — другие способы
                pass

        if '=' in parameters:
            # Формат: key=value или action=search,query=Python
            if ',' in parameters:
                # Несколько параметров
                pairs = parameters.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        param_dict[key.strip()] = value.strip()
            else:
                # Один параметр
                key, value = parameters.split('=', 1)
                param_dict[key.strip()] = value.strip()

            # Преобразование типов
            param_dict = self._convert_parameter_types(tool_name, param_dict)

            # Вывод action, если не указан
            if 'action' not in param_dict:
                param_dict = self._infer_action(tool_name, param_dict)
        else:
            # Прямой ввод — вывод по типу инструмента
            param_dict = self._infer_simple_parameters(tool_name, parameters)

        return param_dict

    def _convert_parameter_types(self, tool_name: str, param_dict: dict) -> dict:
        """
        Преобразует типы по определению параметров инструмента

        Args:
            tool_name: Имя инструмента
            param_dict: Словарь параметров

        Returns:
            Словарь параметров после преобразования типов
        """
        if not self.tool_registry:
            return param_dict

        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return param_dict

        # Определения параметров инструмента
        try:
            tool_params = tool.get_parameters()
        except:
            return param_dict

        # Карта типов параметров
        param_types = {}
        for param in tool_params:
            param_types[param.name] = param.type

        # Преобразование типов
        converted_dict = {}
        for key, value in param_dict.items():
            if key in param_types:
                param_type = param_types[key]
                try:
                    if param_type == 'number' or param_type == 'integer':
                        # В число
                        if isinstance(value, str):
                            converted_dict[key] = float(value) if param_type == 'number' else int(value)
                        else:
                            converted_dict[key] = value
                    elif param_type == 'boolean':
                        # В булево
                        if isinstance(value, str):
                            converted_dict[key] = value.lower() in ('true', '1', 'yes')
                        else:
                            converted_dict[key] = bool(value)
                    else:
                        converted_dict[key] = value
                except (ValueError, TypeError):
                    # Ошибка преобразования — исходное значение
                    converted_dict[key] = value
            else:
                converted_dict[key] = value

        return converted_dict

    def _infer_action(self, tool_name: str, param_dict: dict) -> dict:
        """Выводит action по типу инструмента и параметрам"""
        if tool_name == 'memory':
            if 'recall' in param_dict:
                param_dict['action'] = 'search'
                param_dict['query'] = param_dict.pop('recall')
            elif 'store' in param_dict:
                param_dict['action'] = 'add'
                param_dict['content'] = param_dict.pop('store')
            elif 'query' in param_dict:
                param_dict['action'] = 'search'
            elif 'content' in param_dict:
                param_dict['action'] = 'add'
        elif tool_name == 'rag':
            if 'search' in param_dict:
                param_dict['action'] = 'search'
                param_dict['query'] = param_dict.pop('search')
            elif 'query' in param_dict:
                param_dict['action'] = 'search'
            elif 'text' in param_dict:
                param_dict['action'] = 'add_text'

        return param_dict

    def _infer_simple_parameters(self, tool_name: str, parameters: str) -> dict:
        """Строит полный словарь параметров для простого ввода"""
        if tool_name == 'rag':
            return {'action': 'search', 'query': parameters}
        elif tool_name == 'memory':
            return {'action': 'search', 'query': parameters}
        else:
            return {'input': parameters}

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """
        Запускает SimpleAgent с опциональными инструментами
        
        Args:
            input_text: Ввод пользователя
            max_tool_iterations: Макс. итераций вызова инструментов
            **kwargs: прочие параметры
            
        Returns:
            Ответ агента
        """
        # Список сообщений
        messages = []
        
        # Системное сообщение (с инструментами)
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})
        
        # История
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Текущее сообщение пользователя
        messages.append({"role": "user", "content": input_text})
        
        # Без инструментов — базовая логика
        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            return response
        
        # Итерации с многораундовыми вызовами
        current_iteration = 0
        final_response = ""

        while current_iteration < max_tool_iterations:
            # Вызов LLM
            response = self.llm.invoke(messages, **kwargs)

            # Проверка вызовов инструментов
            tool_calls = self._parse_tool_calls(response)

            if tool_calls:
                # Выполнение всех вызовов
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    # Удаление маркеров из ответа
                    clean_response = clean_response.replace(call['original'], "")

                # Сообщение с результатами инструментов
                messages.append({"role": "assistant", "content": clean_response})

                # Результаты инструментов
                tool_results_text = "\n\n".join(tool_results)
                messages.append({"role": "user", "content": f"Результат выполнения инструмента:\n{tool_results_text}\n\nДайте полный ответ на основе этих результатов."})

                current_iteration += 1
                continue

            # Финальный ответ без инструментов
            final_response = response
            break

        # При превышении лимита — последний ответ
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs)
        
        # Сохранение в историю
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))

        return final_response

    def add_tool(self, tool) -> None:
        """
        Добавляет инструмент агенту (удобный метод)

        MCP с auto_expand разворачивается в отдельные инструменты
        """
        if not self.tool_registry:
            from tools.registry import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True

        # MCP с развёртыванием
        if hasattr(tool, 'auto_expand') and tool.auto_expand:
            # Список развёрнутых инструментов
            expanded_tools = tool.get_expanded_tools()
            if expanded_tools:
                # Регистрация всех развёрнутых
                for expanded_tool in expanded_tools:
                    self.tool_registry.register_tool(expanded_tool)
                print(f"✅ MCP-инструмент '{tool.name}' развёрнут в {len(expanded_tools)} отдельных инструментов")
                return

        # Обычный или несвёрнутый MCP
        self.tool_registry.register_tool(tool)

    def remove_tool(self, tool_name: str) -> bool:
        """Удаляет инструмент (удобный метод)"""
        if self.tool_registry:
            return self.tool_registry.unregister_tool(tool_name)
        return False

    def list_tools(self) -> list:
        """Список доступных инструментов"""
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []

    def has_tools(self) -> bool:
        """Проверяет наличие инструментов"""
        return self.enable_tool_calling and self.tool_registry is not None

    def stream_run(self, input_text: str, **kwargs) -> Iterator[str]:
        """
        Потоковый запуск агента
        
        Args:
            input_text: Ввод пользователя
            **kwargs: прочие параметры
            
        Yields:
            Фрагменты ответа агента
        """
        # Список сообщений
        messages = []
        
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        
        messages.append({"role": "user", "content": input_text})
        
        # Потоковый вызов LLM
        full_response = ""
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            yield chunk
        
        # Сохранение диалога в историю
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(full_response, "assistant"))
