MY_REACT_PROMPT = """Вы — помощник искусственного интеллекта, обладающий способностями к рассуждению и действию. Вы можете обдумать и проанализировать проблему, затем использовать соответствующие инструменты для получения информации и, наконец, дать точный ответ.

## Доступные инструменты
{инструменты}

## Рабочий процесс
Пожалуйста, отвечайте строго в следующем формате, делая только один шаг за раз:

Мысль: ваш мыслительный процесс для анализа проблем, разбиения задач и планирования следующих шагов.
Действие: Действие, которое вы решите предпринять, должно быть в одном из следующих форматов:
- `{{tool_name}}[{{tool_input}}]` - вызвать указанный инструмент
- `Завершить[окончательный ответ]` - когда у вас достаточно информации, чтобы дать окончательный ответ.

## Важное напоминание
1. Каждый ответ должен состоять из двух частей: Мысли и Действия.
2. Строго соблюдать формат вызова инструмента: имя инструмента [параметр]
3. Используйте «Готово» только в том случае, если вы уверены, что у вас достаточно информации для ответа на вопрос.
4. Если информации, возвращаемой инструментом, недостаточно, продолжайте использовать другие инструменты или другие параметры того же инструмента.

## Текущая задача
**Вопрос:** {вопрос}

## История выполнения
{история}

Теперь приступайте к рассуждениям и действиям:
"""

import re
from typing import Optional, List, Tuple
from hello_agents import ReActAgent, HelloAgentsLLM, Config, Message, ToolRegistry

class MyReActAgent(ReActAgent):
    """
    Переписанный ReAct Agent — агент, сочетающий рассуждения и действия.
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
        custom_prompt: Optional[str] = None
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        self.current_history: List[str] = []
        self.prompt_template = custom_prompt if custom_prompt else MY_REACT_PROMPT
        print(f"✅ Инициализация {name} завершена, максимальное количество шагов: {max_steps}")

    def run(self, input_text: str, **kwargs) -> str:
        """Запустите агент ReAct"""
        self.current_history = []
        current_step = 0

        print(f"\n🤖 {self.name} Начать обработку проблемы: {input_text}")

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n---Шаг {current_step} ---")

            # 1. Составьте слова-подсказки
            tools_desc = self.tool_registry.get_tools_description()
            history_str = "\n".join(self.current_history)
            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )

            # 2. Позвоните в LLM
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs)

            # 3. Анализ вывода
            thought, action = self._parse_output(response_text)

            # 4. Проверьте условия завершения
            if action and action.startswith("Finish"):
                final_answer = self._parse_action_input(action)
                self.add_message(Message(input_text, "user"))
                self.add_message(Message(final_answer, "assistant"))
                return final_answer

            # 5. Выполнить вызов инструмента
            if action:
                tool_name, tool_input = self._parse_action(action)
                observation = self.tool_registry.execute_tool(tool_name, tool_input)
                self.current_history.append(f"Action: {action}")
                self.current_history.append(f"Observation: {observation}")

        # Достигнуто максимальное количество шагов.
        final_answer = "Извините, я не могу выполнить эту задачу за ограниченное количество шагов."
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer