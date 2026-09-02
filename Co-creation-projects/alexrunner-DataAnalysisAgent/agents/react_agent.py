import json
from typing import Optional, List
from hello_agents import ReActAgent, HelloAgentsLLM, Config, Message, ToolRegistry
from dotenv import load_dotenv

MY_REACT_PROMPT = """
Обратите внимание: вы — интеллектуальный помощник, способный вызывать внешние инструменты.

Доступные инструменты:
{tools}

Строго соблюдайте следующий формат ответа:

Пример 1:
{{
"Thought": "Сначала нужно узнать сегодняшний курс USD/CNY, а затем рассчитать чистую прибыль.",
"Action": {{"tool_name": "Search", "tool_input": "сегодняшний курс USD/CNY"}},
"Finish": []
}}

Пример 2:
{{
"Thought": "Размышления завершены, готов выдать итоговый ответ.",
"Action": {{}},
"Finish": ["описание подзадачи 1", "описание подзадачи 2", "описание подзадачи 3"]
}}

Пояснение формата:
Thought: ваш ход мыслей — анализ проблемы, декомпозиция задачи и планирование следующего шага.
Action: действие, которое вы решили предпринять; формат: `{{"tool_name": "Search", "tool_input": "сегодняшний курс USD/CNY"}}`; если действие не требуется — `{{}}`.
Finish: когда собрано достаточно информации для ответа на вопрос пользователя, выведите здесь итоговый результат; иначе — `[]`.


Теперь решите следующую задачу:
Question: {question}
History: {history}
"""

# Загрузка переменных окружения
load_dotenv()

class NewReActAgent(ReActAgent):
    """
    Переработанный ReAct Agent — агент, сочетающий рассуждение и действие
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
        print(f"✅ {name} инициализирован, максимум шагов: {max_steps}")

    def run(self, input_text: str, **kwargs) -> str:
        """Запуск ReAct Agent"""
        self.current_history = []
        current_step = 0

        print(f"\n🤖 {self.name} начинает обработку запроса: {input_text}")

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- Шаг {current_step} ---")

            # 1. Формирование промпта
            tools_desc = self.tool_registry.get_tools_description()
            history_str = "\n".join(self.current_history)
            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )

            # 2. Вызов LLM
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs)
            print(response_text)

            # 3. Разбор вывода
            thought, action, finish = self._parse_output(response_text)

            # 4. Проверка условия завершения
            if finish:
                final_answer = finish
                return final_answer

            # 5. Выполнение вызова инструмента
            if action:
                tool_name, tool_input = self._parse_action(action)
                observation = self.tool_registry.execute_tool(tool_name, tool_input)
                self.current_history.append(f"Action: {action}")
                self.current_history.append(f"Observation: {observation}")

        # Достигнут лимит шагов: LLM формирует итоговый ответ за один раз
        print(f"\n⚠️ Достигнут лимит шагов {self.max_steps}, формирование итогового ответа")
        history_str = "\n".join(self.current_history)
        final_prompt = self.prompt_template.format(
                tools="",
                question=input_text,
                history=history_str +
                "\n\nНа основе информации выше дайте итоговый ответ одним сообщением (обязательно заполните поле Finish)"
            )
        messages = [{"role": "user", "content": final_prompt}]
        final_response = self.llm.invoke(messages, **kwargs)
        thought, action, finish = self._parse_output(final_response)
        if finish:
            final_answer = finish
            return final_answer
        else:
            print("Предупреждение: при формировании итогового ответа поле Finish не найдено.")
            return "Извините, при попытке сформировать итоговый ответ произошла ошибка."

    def _parse_output(self, text: str):
        # Очистка вывода модели, попытка извлечь JSON-часть
        cleaned_text = self._extract_json_from_response(text)

        try:
            data = json.loads(cleaned_text)
            thought = data.get("Thought", "")
            action = data.get("Action")
            finish = data.get("Finish", [])
            return thought, action, finish
        except json.JSONDecodeError as e:
            print(f"Предупреждение: текст от LLM не является валидным JSON. Исходный текст: {text}")
            print(f"Ошибка разбора JSON: {e}")
            return "", None, ""

    def _extract_json_from_response(self, text: str) -> str:
        """Извлечение JSON-части из ответа модели"""
        start = text.find('{')
        end = text.rfind('}')

        if start != -1 and end != -1 and start < end:
            candidate = text[start:end+1]
            # Проверка валидности JSON
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

    def _parse_action(self, action_text: dict):
        # Извлечение tool_name и tool_input
        if not action_text or not isinstance(action_text, dict):
            return None, None
        tool_name = action_text.get("tool_name")
        tool_input = action_text.get("tool_input")
        return tool_name, tool_input


if __name__ == "__main__":
    llm = HelloAgentsLLM()
    tool_registry = ToolRegistry()
    agent = NewReActAgent(
        name="Agent",
        llm=llm,
        tool_registry=tool_registry,
        max_steps=5
    )
    question = "Кратко расскажите о себе"
    try:
        answer = agent.run(question)
        print(f"Итоговый ответ: {answer}")
    except Exception as e:
        print(f"Ошибка при выполнении: {e}")
