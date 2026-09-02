"""Reflection Agent — агент с саморефлексией и итеративной оптимизацией"""

from typing import Optional, List, Dict, Any
from core.agent import Agent
from core.llm import HelloAgentsLLM
from core.config import Config
from core.message import Message

DEFAULT_PROMPTS = {
    "initial": """
Выполните задачу согласно требованиям:

Задача: {task}

Дайте полный и точный ответ.
""",
    "reflect": """
Внимательно проверьте следующий ответ и найдите возможные проблемы или улучшения:

# Исходная задача:
{task}

# Текущий ответ:
{content}

Оцените качество ответа, укажите недостатки и конкретные рекомендации по улучшению.
Если ответ уже хорош, ответьте «улучшения не требуются».
""",
    "refine": """
Улучшите ответ с учётом обратной связи:

# Исходная задача:
{task}

# Предыдущая попытка:
{last_attempt}

# Обратная связь:
{feedback}

Дайте улучшенный ответ.
"""
}

class Memory:
    """
    Простой модуль кратковременной памяти для хранения действий и рефлексий агента.
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """Добавляет новую запись в память"""
        self.records.append({"type": record_type, "content": content})
        print(f"📝 Память обновлена, добавлена запись типа '{record_type}'.")

    def get_trajectory(self) -> str:
        """Форматирует все записи памяти в связный текст"""
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"--- Предыдущая попытка (код) ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- Отзыв рецензента ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self) -> str:
        """Возвращает результат последнего выполнения"""
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return ""

class ReflectionAgent(Agent):
    """
    Reflection Agent — агент с саморефлексией и итеративной оптимизацией

    Агент умеет:
    1. Выполнять начальную задачу
    2. Рефлексировать над результатом
    3. Оптимизировать ответ по итогам рефлексии
    4. Итеративно улучшать до достижения качества

    Подходит для генерации кода, документов, аналитических отчётов и других задач,
    требующих итеративной доработки.

    Поддерживает пользовательские шаблоны промптов для разных доменов.
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_iterations: int = 3,
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        """
        Инициализирует ReflectionAgent

        Args:
            name: имя агента
            llm: экземпляр LLM
            system_prompt: системный промпт
            config: объект конфигурации
            max_iterations: максимум итераций
            custom_prompts: пользовательские шаблоны {"initial": "", "reflect": "", "refine": ""}
        """
        super().__init__(name, llm, system_prompt, config)
        self.max_iterations = max_iterations
        self.memory = Memory()

        self.prompts = custom_prompts if custom_prompts else DEFAULT_PROMPTS
    
    def run(self, input_text: str, **kwargs) -> str:
        """
        Запускает Reflection Agent

        Args:
            input_text: описание задачи
            **kwargs: прочие параметры

        Returns:
            Итоговый оптимизированный результат
        """
        print(f"\n🤖 {self.name} начинает задачу: {input_text}")

        self.memory = Memory()

        print("\n--- Начальная попытка ---")
        initial_prompt = self.prompts["initial"].format(task=input_text)
        initial_result = self._get_llm_response(initial_prompt, **kwargs)
        self.memory.add_record("execution", initial_result)

        for i in range(self.max_iterations):
            print(f"\n--- Итерация {i+1}/{self.max_iterations} ---")

            print("\n-> Рефлексия...")
            last_result = self.memory.get_last_execution()
            reflect_prompt = self.prompts["reflect"].format(
                task=input_text,
                content=last_result
            )
            feedback = self._get_llm_response(reflect_prompt, **kwargs)
            self.memory.add_record("reflection", feedback)

            if "无需改进" in feedback or "улучшения не требуются" in feedback or "no need for improvement" in feedback.lower():
                print("\n✅ Рефлексия считает результат достаточным, задача завершена.")
                break

            print("\n-> Оптимизация...")
            refine_prompt = self.prompts["refine"].format(
                task=input_text,
                last_attempt=last_result,
                feedback=feedback
            )
            refined_result = self._get_llm_response(refine_prompt, **kwargs)
            self.memory.add_record("execution", refined_result)

        final_result = self.memory.get_last_execution()
        print(f"\n--- Задача завершена ---\nИтог:\n{final_result}")

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_result, "assistant"))

        return final_result
    
    def _get_llm_response(self, prompt: str, **kwargs) -> str:
        """Вызывает LLM и возвращает полный ответ"""
        messages = [{"role": "user", "content": prompt}]
        return self.llm.invoke(messages, **kwargs) or ""
