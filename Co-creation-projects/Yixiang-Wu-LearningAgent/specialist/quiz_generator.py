# specialist/quiz_generator.py
"""Генератор викторин - создание вопросов викторины на основе учебного плана"""

import json
from typing import List, Union
from hello_agents import HelloAgentsLLM


class QuizGeneratorAgent:
    """
Агент генерации тестов

Функция:
- Генерировать вопросы на основе плана исследования
- Поддерживает различные уровни сложности (легкий/средний/сложный или 0,0–1,0).
- Генерация одного или нескольких вопросов
    """

    def __init__(self, llm: HelloAgentsLLM):
        """
Инициализация QuizGeneratorAgent

        Args:
llm: экземпляр HelloAgentsLLM
        """
        self.llm = llm

    def generate_question(
        self, plan: str, difficulty: Union[str, float] = "medium"
    ) -> str:
        """
Создать один вопрос

        Args:
план: содержание плана обучения
сложность: уровень сложности
                - str: "easy", "medium", "hard"
                - float: 0.0-1.0（0.0=最简单，1.0=最难）

        Returns:
Сгенерированный текст вопроса
        """
# Конвертируем уровень сложности
        difficulty_level = self._normalize_difficulty(difficulty)

# Составьте слова-подсказки
        user_prompt = f"""请基于以下学习计划，生成一个{difficulty_level}难度的问题：

【План обучения】
{plan[:2000]}

Требовать:
1. Вопросы должны быть ясными и конкретными.
2. Сложность соответствует {difficulty_level}.
3. Возврат к вопросу напрямую без дополнительных пояснений.
"""

        messages = [
            {
                "role": "system",
                "content": "你是一个教育专家，擅长根据学习内容生成合适的测验问题。",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.llm.invoke(messages)
            return response.strip()
        except Exception as e:
# Понижение версии: возврат к вопросу по умолчанию
            return f"请简要描述你从学习计划中学到的核心内容（难度：{difficulty_level}）"

    def generate_questions(
        self,
        plan: str,
        count: int = 3,
        difficulty: Union[str, float] = "medium",
    ) -> List[str]:
        """
Создать несколько вопросов

        Args:
план: содержание плана обучения
count: количество вопросов
сложность: уровень сложности

        Returns:
Список вопросов
        """
        questions = []

        for i in range(count):
# Немного отрегулируйте сложность каждого вопроса, чтобы увеличить разнообразие
            if isinstance(difficulty, float):
# Плавающее ±0,1 от базовой сложности.
                adjusted_difficulty = max(0.0, min(1.0, difficulty + (i - 1) * 0.1))
            else:
                adjusted_difficulty = difficulty

            question = self.generate_question(plan, adjusted_difficulty)
            questions.append(question)

        return questions

    def _normalize_difficulty(self, difficulty: Union[str, float]) -> str:
        """
Стандартизированный уровень сложности

        Args:
сложность: сложность (str или float)

        Returns:
Стандартизированное описание сложности
        """
        if isinstance(difficulty, float):
            if difficulty < 0.3:
вернуть «простой»
            elif difficulty < 0.7:
вернуть «средний»
            else:
вернуть «сложность»
        else:
#Сопоставить строку с китайским языком
            mapping = {
"легко": "легко",
«средний»: «средний»,
«сложный»: «сложность»,
            }
            return mapping.get(difficulty.lower(), "中等")
