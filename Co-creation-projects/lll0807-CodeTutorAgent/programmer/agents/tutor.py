from hello_agents import SimpleAgent, HelloAgentsLLM
from typing import Dict, Any

class TutorAgent(SimpleAgent):
    """
    Главный координирующий агент; управляет подагентами Planner, Exercise и Reviewer.
    Простой режим прямого вызова без A2A.
    """
    
    def __init__(self, llm: HelloAgentsLLM, knowledge_service):
        """
        Инициализация TutorAgent и всех подагентов.
        
        Args:
            llm: экземпляр LLM для всех агентов.
        """
        # Импорт здесь во избежание циклических зависимостей
        from agents.planner import PlannerAgent
        from agents.exercise import ExerciseAgent
        from agents.reviewer import ReviewerAgent
        from tools.code_runner import CodeRunner
        from tools.agent_tool import AgentTool
        self.knowledge = knowledge_service
        # Создание подагентов
        self.planner = PlannerAgent(llm, knowledge_service)
        self.exercise = ExerciseAgent(llm)
        self.reviewer = ReviewerAgent(llm, tools=[CodeRunner()], knowledge_service=knowledge_service)
        
        # Системный промпт
        system_prompt = """
        Ты интеллектуальный наставник по программированию (Tutor). Координируешь персонализированное обучение.
        
        У тебя есть специализированные помощники (инструменты):
        - call_planner: планировщик курса — персональный план обучения, обзор уже созданных планов
        - call_exercise: генератор задач — практические задания по программированию
        - call_reviewer: ревьюер — проверка кода и обратная связь
        
        **Важно: ты должен использовать инструменты, не выполнять эти задачи сам!**
        
        Формат вызова инструмента (строго):
        [TOOL_CALL:имя_инструмента:параметры]
        
        Примеры:
        
        Пример 1 — план обучения:
        Пользователь: «Хочу изучить list comprehensions в Python»
        Твой ответ: [TOOL_CALL:call_planner:query=Составь план обучения list comprehensions в Python]
        
        Пример 2 — обзор плана:
        Пользователь: «Хочу пересмотреть план по list comprehensions в Python»
        Твой ответ: [TOOL_CALL:call_planner:query=Пересмотри план обучения list comprehensions в Python]
        
        Пример 3 — практическая задача:
        Пользователь: «Дай мне задачу по программированию»
        Твой ответ: [TOOL_CALL:call_exercise:query=Дай мне задачу по программированию]
        
        Пример 4 — ревью кода (самый важный!):
        Пользователь: «Проверь код: numbers = [1, 2, 3]»
        Твой ответ: [TOOL_CALL:call_reviewer:query=Проверь код: numbers = [1, 2, 3]]
        
        Рабочий процесс (строго):
        1. Пользователь выражает цель обучения → сразу call_planner
        2. Пользователь просит задачу → сразу call_exercise
        3. Пользователь отправляет код или просит ревью → сразу call_reviewer
        
        **Категорически запрещено**:
        - ❌ Самостоятельно составлять план обучения
        - ❌ Самостоятельно давать задачи
        - ❌ Самостоятельно ревьюить код (даже простой)
        - ❌ Говорить «вызов инструмента не удался» и делать задачу сам
        
        Правильное поведение:
        - ✅ Распознать намерение пользователя
        - ✅ Сразу сформировать вызов инструмента ([TOOL_CALL:имя:query=...])
        - ✅ Дождаться результата инструмента
        - ✅ Дружелюбно представить результат пользователю
        """
        
        # Инициализация родительского класса
        super().__init__(
            name="Tutor",
            llm=llm,
            system_prompt=system_prompt
        )

        # Простой идентификатор пользователя
        self.user_id = "default_user"
        self.current_problem = []

        # Обёртка подагентов в инструменты и регистрация
        self.add_tool(AgentTool(
            self.planner,
            name="call_planner",
            description="Вызов планировщика курса для персонального плана обучения"
        ))
        
        self.add_tool(AgentTool(
            self.exercise,
            name="call_exercise",
            description="Вызов генератора задач по теме обучения"
        ))
        
        self.add_tool(AgentTool(
            self.reviewer,
            name="call_reviewer",
            description="Вызов ревьюера для проверки кода и обратной связи"
        ))


    # def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
    #     result = super().run(input_text)
    #     return result


