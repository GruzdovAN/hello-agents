import re
from llm_client import HelloAgentsLLM
from tools import ToolExecutor, search

# (здесь опущен полный разбор шаблона; шаблон задан ниже)
REACT_PROMPT_TEMPLATE = """
Обрати внимание: ты — умный ассистент, способный вызывать внешние инструменты.

Доступные инструменты:
{tools}

Отвечай строго в следующем формате:

Thought: твои рассуждения — анализ задачи, декомпозиция и план следующего шага.
Action: действие, которое ты решил выполнить; один из форматов:
- `{{tool_name}}[{{tool_input}}]`: вызвать доступный инструмент.
- `Finish[итоговый ответ]`: когда считаешь, что получил финальный ответ.
- Когда собрано достаточно информации для ответа пользователю, в поле `Action:` обязательно используй `Finish[итоговый ответ]`.


Теперь реши задачу:
Question: {question}
History: {history}
"""

class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []

    def run(self, question: str):
        self.history = []
        current_step = 0

        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- Шаг {current_step} ---")

            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(tools=tools_desc, question=question, history=history_str)

            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("Ошибка: LLM не вернул корректный ответ."); break

            thought, action = self._parse_output(response_text)
            if thought: print(f"🤔 Мысль: {thought}")
            if not action: print("Предупреждение: не удалось разобрать Action, цикл остановлен."); break
            
            if action.startswith("Finish"):
                # Finish — извлечь финальный ответ и завершить
                final_answer = self._parse_action_input(action)
                print(f"🎉 Итоговый ответ: {final_answer}")
                return final_answer
            
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                self.history.append("Observation: неверный формат Action, проверьте."); continue

            print(f"🎬 Действие: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            observation = tool_function(tool_input) if tool_function else f"Ошибка: инструмент '{tool_name}' не найден."
            
            print(f"👀 Наблюдение: {observation}")
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("Достигнуто максимальное число шагов, цикл остановлен.")
        return None

    def _parse_output(self, text: str):
        # Thought: до Action: или до конца текста
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: до конца текста
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parse_action_input(self, action_text: str):
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""

if __name__ == '__main__':
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    search_desc = "Веб-поисковик. Используй, когда нужны актуальные факты или сведения, которых нет в твоей базе знаний."
    tool_executor.registerTool("Search", search_desc, search)
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "Какая последняя модель телефона Huawei и в чём её главные плюсы?"
    agent.run(question)
