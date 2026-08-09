# my_simple_agent.py
from typing import Optional, Iterator
from hello_agents import SimpleAgent, HelloAgentsLLM, Config, Message
import re

class MySimpleAgent(SimpleAgent):
    """
    Переписан простой диалоговый агент.
    Показывает, как создать собственный агент на основе базовых классов платформы.
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        print(f"✅ Инициализация {name} завершена, вызов инструмента: {'enable' if self.enable_tool_calling else 'disable'}")
    
    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """
        Переписанный метод запуска — реализует простую логику диалога и поддерживает дополнительные вызовы инструментов.
        """
        print(f"🤖 {self.name} обрабатывает: {input_text}")

        # Создать список сообщений
        messages = []

        # Добавить системные сообщения (могут содержать информацию об инструменте)
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})

        # Добавить историческое сообщение
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        # Добавить текущее сообщение пользователя
        messages.append({"role": "user", "content": input_text})

        # Если вызов инструмента не включен, используйте простую логику диалога.
        if not self.enable_tool_calling:
            response = self.llm.invoke(messages, **kwargs)
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            print(f"✅ Ответ {self.name} завершен")
            return response

        # Логика, поддерживающая несколько циклов вызовов инструментов
        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)

    def _get_enhanced_system_prompt(self) -> str:
        """Создайте расширенные системные подсказки, включающие информацию об инструменте."""
        base_prompt = self.system_prompt or "Вы полезный помощник ИИ."

        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt

        # Получить описание инструмента
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "Инструментов пока нет":
            return base_prompt

        tools_section = "\n\n## Доступные инструменты\n"
        tools_section += "Чтобы ответить на ваши вопросы, вы можете использовать следующие инструменты:\n"
        tools_section += tools_description + "\n"

        tools_section += "\n## Формат вызова инструмента\n"
        tools_section += "При использовании инструмента используйте следующий формат:\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n"
        tools_section += "Например: `[TOOL_CALL:search:Программирование на Python]` или `[TOOL_CALL:memory:recall=информация о пользователе]`\n\n"
        tools_section += "Результаты вызова инструмента автоматически вставляются в разговор, и вы можете продолжить свой ответ на основе результатов. \п"

        return base_prompt + tools_section
    
    def _run_with_tools(self, messages: list, input_text: str, max_tool_iterations: int, **kwargs) -> str:
        """Поддержка текущей логики вызовов инструментов"""
        current_iteration = 0
        final_response = ""

        while current_iteration < max_tool_iterations:
            # Позвонить в LLM
            response = self.llm.invoke(messages, **kwargs)

            # Проверьте, есть ли вызов инструмента
            tool_calls = self._parse_tool_calls(response)

            if tool_calls:
                print(f"🔧 Обнаружены вызовы инструментов {len(tool_calls)}")
                # Выполнять все вызовы инструментов и собирать результаты
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    # Удалить маркер вызова инструмента из ответа
                    clean_response = clean_response.replace(call['original'], "")

                # Создайте сообщение, содержащее результаты работы инструмента.
                messages.append({"role": "assistant", "content": clean_response})

                # Добавить результаты инструмента
                tool_results_text = "\n\n".join(tool_results)
                messages.append({"role": "user", "content": f"Результаты выполнения инструмента:\n{tool_results_text}\n\nПожалуйста, дайте полный ответ на основе этих результатов."})

                current_iteration += 1
                continue

            # Никаких вызовов инструментов, это окончательный ответ
            final_response = response
            break

        # Если максимальное количество итераций превышено, получить последний ответ
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs)

        # Сохранить в историю
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        print(f"✅ Ответ {self.name} завершен")

        return final_response

    def _parse_tool_calls(self, text: str) -> list:
        """Анализ вызовов инструментов в тексте"""
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
        """Выполнить вызов инструмента"""
        if not self.tool_registry:
            return f"❌ Ошибка: реестр инструментов не настроен."

        try:
            # Интеллектуальный анализ параметров
            if tool_name == 'calculator':
                # Инструмент калькулятора напрямую передает выражение
                result = self.tool_registry.execute_tool(tool_name, parameters)
            else:
                # Другие инструменты используют интеллектуальный анализ параметров.
                param_dict = self._parse_tool_parameters(tool_name, parameters)
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    return f"❌ Ошибка: инструмент «{tool_name}» не найден."
                result = tool.run(param_dict)

            return f"🔧 Результат выполнения инструмента {tool_name}:\n{result}"

        except Exception as e:
            return f"❌ Ошибка вызова инструмента: {str(e)}"

    def _parse_tool_parameters(self, tool_name: str, parameters: str) -> dict:
        """Параметры инструмента интеллектуального анализа"""
        param_dict = {}

        if '=' in parameters:
            # Формат: ключ=значение или действие=поиск,запрос=Python.
            if ',' in parameters:
                # Несколько параметров: action=search,query=Python,limit=3.
                pairs = parameters.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        param_dict[key.strip()] = value.strip()
            else:
                # Один параметр: ключ=значение.
                key, value = parameters.split('=', 1)
                param_dict[key.strip()] = value.strip()
        else:
            # Непосредственная передача параметров и интеллектуальный вывод на основе типа инструмента
            if tool_name == 'search':
                param_dict = {'query': parameters}
            elif tool_name == 'memory':
                param_dict = {'action': 'search', 'query': parameters}
            else:
                param_dict = {'input': parameters}

        return param_dict
    
    def stream_run(self, input_text: str, **kwargs) -> Iterator[str]:
        """
        Пользовательский метод запуска потоковой передачи
        """
        print(f"🌊 {self.name} начинает трансляцию: {input_text}")

        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": input_text})

        # Потоковый звонок в LLM
        full_response = ""
        print("📝Ответ в режиме реального времени: ", end="")
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            print(chunk, end="", flush=True)
            yield chunk

        print()  # новая строка

        # Сохранить весь разговор в истории
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(full_response, "assistant"))
        print(f"✅ Ответ потоковой передачи {self.name} завершен")

    def add_tool(self, tool) -> None:
        """Добавить инструменты в Агент (удобный способ)"""
        if not self.tool_registry:
            from hello_agents import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True

        self.tool_registry.register_tool(tool)
        print(f"🔧 Добавлен инструмент «{tool.name}».")

    def has_tools(self) -> bool:
        """Проверьте наличие инструментов"""
        return self.enable_tool_calling and self.tool_registry is not None
    
    def remove_tool(self, tool_name: str) -> bool:
        """Инструмент для удаления (удобный метод)"""
        if self.tool_registry:
            self.tool_registry.unregister(tool_name)
            return True
        return False
    
    def list_tools(self) -> list:
        """Список всех доступных инструментов"""
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []