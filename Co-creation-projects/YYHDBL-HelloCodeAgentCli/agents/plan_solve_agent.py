"""Plan and Solve Agent — декомпозиция плана и пошаговое выполнение"""

import ast
from typing import Optional, List, Dict
from core.agent import Agent
from core.llm import HelloAgentsLLM
from core.config import Config
from core.message import Message

DEFAULT_PLANNER_PROMPT = """
Вы — эксперт по планированию. Разбейте сложную задачу пользователя на простые шаги.
Каждый шаг должен быть независимой исполнимой подзадачей в строгой логической последовательности.
Вывод — Python-список строк с описанием подзадач.

Задача: {question}

Формат ответа:
```python
["Шаг 1", "Шаг 2", "Шаг 3", ...]
```
"""

DEFAULT_EXECUTOR_PROMPT = """
Вы — эксперт по выполнению. Строго следуйте плану и решайте задачу по шагам.
Вы получите исходный вопрос, полный план и историю уже выполненных шагов с результатами.
Сосредоточьтесь только на «текущем шаге» и выведите только его итоговый ответ без лишних пояснений.

# Исходный вопрос:
{question}

# Полный план:
{plan}

# История шагов и результатов:
{history}

# Текущий шаг:
{current_step}

Ответ только для текущего шага:
"""

class Planner:
    """Планировщик — разбивает сложную задачу на простые шаги"""

    def __init__(self, llm_client: HelloAgentsLLM, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_PLANNER_PROMPT

    def plan(self, question: str, **kwargs) -> List[str]:
        """
        Генерирует план выполнения

        Args:
            question: задача для решения
            **kwargs: параметры вызова LLM

        Returns:
            Список шагов
        """
        prompt = self.prompt_template.format(question=question)
        messages = [{"role": "user", "content": prompt}]

        print("--- Генерация плана ---")
        response_text = self.llm_client.invoke(messages, **kwargs) or ""
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

class Executor:
    """Исполнитель — выполняет план по шагам"""

    def __init__(self, llm_client: HelloAgentsLLM, prompt_template: Optional[str] = None):
        self.llm_client = llm_client
        self.prompt_template = prompt_template if prompt_template else DEFAULT_EXECUTOR_PROMPT

    def execute(self, question: str, plan: List[str], **kwargs) -> str:
        """
        Выполняет задачу по плану

        Args:
            question: исходный вопрос
            plan: план выполнения
            **kwargs: параметры вызова LLM

        Returns:
            Итоговый ответ
        """
        history = ""
        final_answer = ""

        print("\n--- Выполнение плана ---")
        for i, step in enumerate(plan, 1):
            print(f"\n-> Шаг {i}/{len(plan)}: {step}")
            prompt = self.prompt_template.format(
                question=question,
                plan=plan,
                history=history if history else "нет",
                current_step=step
            )
            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.invoke(messages, **kwargs) or ""

            history += f"Шаг {i}: {step}\nРезультат: {response_text}\n\n"
            final_answer = response_text
            print(f"✅ Шаг {i} завершён, результат: {final_answer}")

        return final_answer

class PlanAndSolveAgent(Agent):
    """
    Plan and Solve Agent — декомпозиция и пошаговое выполнение

    Агент умеет:
    1. Разбивать сложную задачу на простые шаги
    2. Выполнять план последовательно
    3. Вести историю выполнения и контекст
    4. Формировать итоговый ответ

    Подходит для многошаговых рассуждений, математики и сложного анализа.
    """
    
    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        """
        Инициализирует PlanAndSolveAgent

        Args:
            name: имя агента
            llm: экземпляр LLM
            system_prompt: системный промпт
            config: объект конфигурации
            custom_prompts: шаблоны {"planner": "", "executor": ""}
        """
        super().__init__(name, llm, system_prompt, config)

        if custom_prompts:
            planner_prompt = custom_prompts.get("planner")
            executor_prompt = custom_prompts.get("executor")
        else:
            planner_prompt = None
            executor_prompt = None

        self.planner = Planner(self.llm, planner_prompt)
        self.executor = Executor(self.llm, executor_prompt)
    
    def run(self, input_text: str, **kwargs) -> str:
        """
        Запускает Plan and Solve Agent
        
        Args:
            input_text: задача для решения
            **kwargs: прочие параметры
            
        Returns:
            Итоговый ответ
        """
        print(f"\n🤖 {self.name} начинает задачу: {input_text}")
        
        plan = self.planner.plan(input_text, **kwargs)
        if not plan:
            final_answer = "Не удалось сгенерировать исполнимый план, задача прервана."
            print(f"\n--- Задача прервана ---\n{final_answer}")
            
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(final_answer, "assistant"))
            
            return final_answer
        
        final_answer = self.executor.execute(input_text, plan, **kwargs)
        print(f"\n--- Задача завершена ---\nИтоговый ответ: {final_answer}")
        
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        
        return final_answer
