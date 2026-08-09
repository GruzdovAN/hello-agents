import os
import ast
from llm_client import HelloAgentsLLM
from dotenv import load_dotenv
from typing import List, Dict

# Загрузить .env; если файла нет — продолжить с системным окружением
try:
    load_dotenv()
except FileNotFoundError:
    print("Предупреждение: файл .env не найден, используются системные переменные.")
except Exception as e:
    print(f"Предупреждение: ошибка загрузки .env: {e}")

# --- 1. LLM-клиент ---
# Предполагается файл llm_client.py с классом HelloAgentsLLM

# --- 2. Планировщик (Planner) ---
PLANNER_PROMPT_TEMPLATE = """
Ты — эксперт по планированию для ИИ. Разбей сложный вопрос пользователя на план из простых шагов.
Каждый шаг — независимая, выполнимая подзадача; шаги строго в логическом порядке.
Ответ должен быть Python-списком строк — описаний подзадач.

Вопрос: {question}

Выведи план строго в таком виде (обязательны префикс ```python и суффикс ```):
```python
["шаг1", "шаг2", "шаг3", ...]
```
"""

class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]
        
        print("--- Генерация плана ---")
        response_text = self.llm_client.think(messages=messages) or ""
        print(f"✅ План сгенерирован:\n{response_text}")
        
        try:
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ Ошибка разбора плана: {e}")
            print(f"Исходный ответ: {response_text}")
            return []
        except Exception as e:
            print(f"❌ Неизвестная ошибка при разборе плана: {e}")
            return []

# --- 3. Исполнитель (Executor) ---
EXECUTOR_PROMPT_TEMPLATE = """
Ты — эксперт по исполнению планов для ИИ. Строго следуй данному плану, шаг за шагом.
Тебе даны исходный вопрос, полный план и уже выполненные шаги с результатами.
Сосредоточься на «текущем шаге» и выдай только его итоговый ответ — без лишних пояснений.

# Исходный вопрос:
{question}

# Полный план:
{plan}

# История шагов и результатов:
{history}

# Текущий шаг:
{current_step}

Выведи только ответ для «текущего шага»:
"""

class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        history = ""
        final_answer = ""
        
        print("\n--- Исполнение плана ---")
        for i, step in enumerate(plan, 1):
            print(f"\n-> Шаг {i}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history if history else "нет", current_step=step
            )
            messages = [{"role": "user", "content": prompt}]
            
            response_text = self.llm_client.think(messages=messages) or ""
            
            history += f"Шаг {i}: {step}\nРезультат: {response_text}\n\n"
            final_answer = response_text
            print(f"✅ Шаг {i} выполнен, результат: {final_answer}")
            
        return final_answer

# --- 4. Сборка агента ---
class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        print(f"\n--- Обработка вопроса ---\nВопрос: {question}")
        plan = self.planner.plan(question)
        if not plan:
            print("\n--- Задача прервана ---\nНе удалось сформировать план.")
            return
        final_answer = self.executor.execute(question, plan)
        print(f"\n--- Готово ---\nИтоговый ответ: {final_answer}")

# --- 5. Точка входа ---
if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "В понедельник фруктовый магазин продал 15 яблок. Во вторник — вдвое больше, чем в понедельник. В среду — на 5 меньше, чем во вторник. Сколько яблок продали за три дня?"
        agent.run(question)
    except ValueError as e:
        print(e)
