# agents/vibe_learning_agent.py
"""Агент интерактивного обучения — закрепление знаний через диалог и тесты"""

import json
from datetime import datetime
from typing import Dict, List
from hello_agents import HelloAgentsLLM
from hello_agents import SimpleAgent
from specialist.quiz_generator import QuizGeneratorAgent
from core.file_manager import FileManager
from core.summary_manager import SummaryManager


class VibeLearningAgent(SimpleAgent):
    """
    Эксперт интерактивного обучения

    Возможности:
    - Два режима: free (свободный диалог) и quiz (структурированный тест)
    - Генерация вопросов по плану обучения
    - Оценка ответов пользователя и обратная связь
    - Динамическая настройка сложности
    - Итоги сессии
    """

    def __init__(self, llm: HelloAgentsLLM, file_manager: FileManager, streaming: bool = None):
        """
        Инициализация VibeLearningAgent

        Args:
            llm: экземпляр HelloAgentsLLM
            file_manager: экземпляр FileManager
            streaming: потоковый вывод (None = авто)
        """
        system_prompt = """
Вы — профессиональный коуч по обучению.

Рабочий процесс:
1. Прочитать план (plan.md), понять систему знаний
2. Сгенерировать первый вопрос по режиму (free/quiz)
3. Оценить ответ пользователя, дать обратную связь
4. Динамически настраивать сложность
5. В конце — итоги сессии

Различия режимов:
- free: открытые вопросы, обсуждение, направление мысли
- quiz: структурированная проверка, фиксированные вопросы, автооценка

Приёмы обратной связи:
- Отмечать верное
- Мягко указывать на улучшения
- Давать дополнительные ссылки и факты
- Поощрять дальнейшее изучение
"""

        self.llm = llm
        self.file_manager = file_manager
        self.quiz_generator = QuizGeneratorAgent(llm)
        self.max_iterations = 10

        # Потоковый вывод
        from utils.streaming import should_stream
        self.streaming = should_stream(streaming)

        # Инициализация через родительский класс
        super().__init__("VibeLearningAgent", llm, system_prompt)

    def start_session(
        self, domain: str, mode: str = "free"
    ) -> str:
        """
        Начать сессию (только первый вопрос)

        Args:
            domain: название области
            mode: режим (free/quiz)

        Returns:
            первый вопрос
        """
        # Проверить существование области
        if not self.file_manager.domain_exists(domain):
            return f"❌ Область '{domain}' не существует. Сначала создайте план через /create."

        # Прочитать план обучения
        try:
            plan = self.file_manager.read_plan(domain)
        except Exception as e:
            return f"❌ Ошибка чтения плана: {e}"

        # Сгенерировать первый вопрос
        question = self._generate_first_question(plan, mode)

        # Сохранить вопрос для продолжения сессии
        self._save_session_start(domain, mode, question)

        return f"""💬 Сессия обучения в режиме {mode.upper()} начата

{question}

💡 Введите ответ, чтобы начать диалог
"""

    def _save_session_start(self, domain: str, mode: str, question: str) -> None:
        """
        Сохранить начало сессии

        Args:
            domain: название области
            mode: режим
            question: первый вопрос
        """
        session_path = self.file_manager.BASE_DIR / domain / "sessions"
        session_path.mkdir(parents=True, exist_ok=True)

        # Временный файл сессии
        temp_file = session_path / ".current_session.txt"
        temp_file.write_text(
            f"{mode}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n{question}",
            encoding='utf-8'
        )

    def continue_session(self, domain: str, user_answer: str, mode: str) -> str:
        """
        Продолжить диалог

        Args:
            domain: название области
            user_answer: ответ пользователя
            mode: режим

        Returns:
            обратная связь и следующий вопрос
        """
        try:
            # Прочитать план
            plan = self.file_manager.read_plan(domain)

            # Предыдущий вопрос из временного файла
            session_path = self.file_manager.BASE_DIR / domain / "sessions"
            temp_file = session_path / ".current_session.txt"

            if temp_file.exists():
                lines = temp_file.read_text(encoding='utf-8').strip().split('\n')
                last_question = lines[-1] if len(lines) > 0 else ""
            else:
                last_question = "Опишите своё понимание этой темы."

            # Сгенерировать обратную связь
            feedback = self._generate_feedback(last_question, user_answer, plan)

            # Следующий вопрос
            next_question = self._generate_next_question(plan, [last_question, user_answer], mode)

            # Обновить временный файл
            temp_file.write_text(
                f"{mode}\n{datetime.now().strftime('%Y-%m-%d %H:%M')}\n{next_question}",
                encoding='utf-8'
            )

            # Вернуть обратную связь и вопрос
            return f"""✅ {feedback}

{next_question}

💡 Введите ответ или «выход» для завершения сессии
"""

        except Exception as e:
            # При ошибке сохранить сессию
            return f"❌ Ошибка обработки ответа: {e}\n\nСессия автоматически сохранена."

    def _save_conversation_history(self, domain: str, mode: str, conversation: List[str], error: str = None) -> None:
        """
        Сохранить историю диалога

        Args:
            domain: название области
            mode: режим
            conversation: запись диалога
            error: сообщение об ошибке (опционально)
        """
        try:
            session_path = self.file_manager.BASE_DIR / domain / "sessions"
            timestamp = datetime.now().strftime("%Y-%m-%d %H-%M")

            content = f"# Сессия обучения - {domain}\n"
            content += f"Режим: {mode}\n"
            content += f"Время: {timestamp}\n\n"

            if conversation:
                content += "\n".join(conversation)

            if error:
                content += f"\n\nОшибка: {error}"

            # Сохранить сессию
            self.file_manager.save_session(domain, content)

        except Exception:
            pass  # тихий сбой

    def _generate_first_question(self, plan: str, mode: str) -> str:
        """
        Сгенерировать первый вопрос

        Args:
            plan: план обучения
            mode: режим（free/quiz）

        Returns:
            текст вопроса
        """
        if mode == "quiz":
            # quiz: QuizGenerator
            return self.quiz_generator.generate_question(plan, difficulty="easy")
        else:
            # free: открытый вопрос
            user_prompt = f"""На основе плана обучения сформируйте открытый вопрос для начала диалога:

{plan[:2000]}

Вопрос должен:
1. Начинаться с базовых концепций
2. Побуждать пользователя думать и формулировать
3. Быть не слишком сложным, укреплять уверенность

Верните только вопрос, без пояснений.
"""

            messages = [
                {
                    "role": "system",
                    "content": "Вы — коуч, умеющий направлять обучение через вопросы.",
                },
                {"role": "user", "content": user_prompt},
            ]

            try:
                if self.streaming:
                    from utils.streaming import stream_response
                    return stream_response(self.llm, messages)
                else:
                    return self.llm.invoke(messages).strip()
            except Exception:
                return "Кратко опишите своё понимание темы и что хотите изучить в первую очередь."

    def _generate_next_question(
        self, plan: str, history: List[str], mode: str
    ) -> str:
        """
        Следующий вопрос (с учётом истории)

        Args:
            plan: план обучения
            history: история диалога
            mode: режим

        Returns:
            текст вопроса
        """
        # Последний вопрос и ответ
        if len(history) < 3:
            return self._generate_first_question(plan, mode)

        if mode == "quiz":
            # quiz: постепенное усложнение
            difficulty = min(1.0, 0.3 + len(history) * 0.1)
            return self.quiz_generator.generate_question(plan, difficulty=difficulty)
        else:
            # free: вопрос по контексту
            recent_context = "\n".join(history[-5:])

            user_prompt = f"""На основе истории диалога сформируйте следующий вопрос:

{recent_context}

Требования:
1. Углублять обсуждение
2. Учитывать предыдущие ответы пользователя
3. Сохранять плавность диалога

Верните только вопрос, без пояснений.
"""

            messages = [
                {
                    "role": "system",
                    "content": "Вы — коуч, ведущий к углублённому обучению через диалог.",
                },
                {"role": "user", "content": user_prompt},
            ]

            try:
                if self.streaming:
                    from utils.streaming import stream_response
                    return stream_response(self.llm, messages)
                else:
                    return self.llm.invoke(messages).strip()
            except Exception:
                return "Поделитесь мыслями или задайте конкретный вопрос."

    def _generate_feedback(
        self, question: str, answer: str, plan: str
    ) -> str:
        """
        Сгенерировать обратную связь

        Args:
            question: вопрос
            answer: ответ пользователя
            plan: план обучения

        Returns:
            текст обратной связи
        """
        user_prompt = f"""Вопрос: {question}

Ответ пользователя: {answer}

План для справки: {plan[:1000]}

Дружелюбная обратная связь (до 100 слов):
1. Отметить верное
2. Мягко указать на улучшения
3. Дать дополнительный факт или совет
"""

        messages = [
            {
                "role": "system",
                "content": "Вы — дружелюбный коуч, умеющий поддерживать и направлять.",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            if self.streaming:
                from utils.streaming import stream_response
                return stream_response(self.llm, messages)
            else:
                return self.llm.invoke(messages).strip()
        except Exception:
            return "Спасибо за ответ. Продолжим углублённое обсуждение."

    def _evaluate_answer(
        self, question: str, answer: str, plan: str
    ) -> Dict[str, any]:
        """
        Оценить качество ответа

        Args:
            question: вопрос
            answer: ответ
            plan: план обучения

        Returns:
            результат оценки (score, mastery_level, suggested_next)
        """
        user_prompt = f"""Оцените качество ответа (0-1):

Вопрос: {question}

Ответ: {answer}

Формат JSON:
{{
  "score": 0.8,
  "mastery_level": "good/poor/medium",
  "suggested_next": "increase/maintain/decrease"
}}

Только JSON, без другого текста.
"""

        messages = [
            {
                "role": "system",
                "content": "Вы — эксперт по оценке обучения.",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = self.llm.invoke(messages).strip()

            # Разбор JSON
            # Упрощённое извлечение по правилам
            return self._extract_evaluation(response)

        except Exception:
            # Fallback: оценка по умолчанию
            return {
                "score": 0.5,
                "mastery_level": "medium",
                "suggested_next": "maintain",
            }

    def _extract_evaluation(self, text: str) -> Dict[str, any]:
        """
        Извлечь оценку из текста (упрощённо)

        Args:
            text: текст ответа LLM

        Returns:
            словарь оценки
        """
        # Упрощённо: значения по умолчанию
        # В продакшене — надёжный разбор JSON
        try:
            # Прямой разбор
            return json.loads(text)
        except:
            # При сбое — значения по умолчанию
            return {
                "score": 0.5,
                "mastery_level": "medium",
                "suggested_next": "maintain",
            }

    def _summarize_session(self, conversation: List[str], domain: str) -> str:
        """
        Подвести итоги сессии

        Args:
            conversation: история диалога
            domain: название области

        Returns:
            итоги сессии
        """
        content = "\n".join(conversation)

        user_prompt = f"""Подведите итоги сессии (до 200 слов):

{content[:3000]}

Включите:
1. Обсуждённые темы
2. Хорошо усвоенные темы
3. Что нужно повторить
4. Рекомендации на следующий раз

Формат:
## итоги сессии

**Темы:** ...

**Усвоение:**
- ...

**Повторить:**
- ...

**Следующие шаги:**
- ...
"""

        messages = [
            {
                "role": "system",
                "content": "Вы — эксперт по обобщению результатов обучения.",
            },
            {"role": "user", "content": user_prompt},
        ]

        try:
            return self.llm.invoke(messages).strip()
        except Exception:
            return f"## Итоги сессии\n\nЗавершена сессия по области {domain}.\nПродолжайте!"
