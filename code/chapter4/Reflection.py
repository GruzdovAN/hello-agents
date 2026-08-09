from typing import List, Dict, Any
# Предполагается файл llm_client.py с классом HelloAgentsLLM
from llm_client import HelloAgentsLLM

# --- Модуль 1: память ---

class Memory:
    """
    Простая кратковременная память: хранит траекторию действий и рефлексий агента.
    """
    def __init__(self):
        # Пустой список записей
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """
        Добавить запись в память.

        Параметры:
        - record_type (str): тип ('execution' или 'reflection').
        - content (str): содержимое (код или отзыв рефлексии).
        """
        self.records.append({"type": record_type, "content": content})
        print(f"📝 Память обновлена: новая запись '{record_type}'.")

    def get_trajectory(self) -> str:
        """
        Отформатировать все записи в связный текст для промпта.
        """
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"--- Предыдущая попытка (код) ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- Отзыв рецензента ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self) -> str:
        """
        Последний результат исполнения (например, свежий сгенерированный код).
        """
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None

# --- Модуль 2: Reflection-агент ---

# 1. Промпт начального исполнения
INITIAL_PROMPT_TEMPLATE = """
Ты — опытный Python-разработчик. Напиши Python-функцию по требованиям ниже.
Код должен включать полную сигнатуру, docstring и следовать PEP 8.

Требование: {task}

Выведи только код, без дополнительных пояснений.
"""

# 2. Промпт рефлексии
REFLECT_PROMPT_TEMPLATE = """
Ты — очень строгий рецензент кода и опытный алгоритмист, требовательный к производительности.
Проверь следующий Python-код и найди главные узкие места именно в **алгоритмической эффективности**.

# Исходная задача:
{task}

# Код на ревью:
```python
{code}
```

Оцени временную сложность и подумай, есть ли **алгоритмически лучшее** решение для заметного ускорения.
Если да — чётко укажи недостатки текущего алгоритма и предложи конкретные улучшения (например, решето вместо пробного деления).
Если алгоритм уже оптимален, ответь «улучшения не нужны».

Выведи только отзыв, без лишних пояснений.
"""

# 3. Промпт оптимизации
REFINE_PROMPT_TEMPLATE = """
Ты — опытный Python-разработчик. Ты улучшаешь код по отзыву рецензента.

# Исходная задача:
{task}

# Твой предыдущий код:
{last_code_attempt}

# Отзыв рецензента:
{feedback}

По отзыву сгенерируй оптимизированную версию.
Код должен включать полную сигнатуру, docstring и следовать PEP 8.
Выведи только оптимизированный код, без дополнительных пояснений.
"""

class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=3):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations

    def run(self, task: str):
        print(f"\n--- Обработка задачи ---\nЗадача: {task}")

        # --- 1. Начальная попытка ---
        print("\n--- Начальная попытка ---")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_code)

        # --- 2. Цикл: рефлексия и улучшение ---
        for i in range(self.max_iterations):
            print(f"\n--- Итерация {i+1}/{self.max_iterations} ---")

            # a. Рефлексия
            print("\n-> Рефлексия...")
            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            # b. Условие остановки
            if "улучшения не нужны" in feedback or "Никаких улучшений не требуется" in feedback or "no need for improvement" in feedback.lower():
                print("\n✅ Рефлексия: код уже достаточно хорош, задача завершена.")
                break

            # c. Оптимизация
            print("\n-> Оптимизация...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code,
                feedback=feedback
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_code)
        
        final_code = self.memory.get_last_execution()
        print(f"\n--- Готово ---\nИтоговый код:\n{final_code}")
        return final_code

    def _get_llm_response(self, prompt: str) -> str:
        """Вспомогательный метод: вызвать LLM и собрать полный потоковый ответ."""
        messages = [{"role": "user", "content": prompt}]
        # Генератор может вернуть None
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text

if __name__ == '__main__':
    # 1. LLM-клиент (.env и llm_client.py должны быть настроены)
    try:
        llm_client = HelloAgentsLLM()
    except Exception as e:
        print(f"Ошибка инициализации LLM-клиента: {e}")
        exit()

    # 2. Reflection-агент, не более 2 итераций
    agent = ReflectionAgent(llm_client, max_iterations=2)

    # 3. Задача и запуск
    task = "Напиши Python-функцию, которая находит все простые числа (prime numbers) от 1 до n."
    agent.run(task)
