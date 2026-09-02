from hello_agents import SimpleAgent, HelloAgentsLLM
from typing import Dict, Any

class TutorAgent(SimpleAgent):
    """
    Главный координирующий агент, напрямую управляющий подагентами Planner, Exercise и Reviewer.
    Использует простой режим прямого вызова без протокола A2A.
    """
    
    def __init__(self, llm: HelloAgentsLLM):
        """
        Инициализация TutorAgent и всех подагентов.
        
        Args:
            llm: экземпляр LLM для всех агентов.
        """
        # Импорт здесь, чтобы избежать циклического импорта
        from agents.planner import PlannerAgent
        from agents.exercise import ExerciseAgent
        from agents.reviewer import ReviewerAgent
        from tools.code_runner import CodeRunner
        from tools.agent_tool import AgentTool
        
        # Создание экземпляров подагентов
        self.planner = PlannerAgent(llm)
        self.exercise = ExerciseAgent(llm)
        self.reviewer = ReviewerAgent(llm, tools=[CodeRunner()])
        
        # Системный промпт
        system_prompt = """
        Вы — интеллектуальный наставник по программированию (Tutor). Вы координируете персонализированный учебный процесс.
        
        У вас есть следующие специализированные помощники (инструменты):
        - call_planner: планировщик курса, составляет персональный учебный план
        - call_exercise: автор задач, генерирует программные упражнения
        - call_reviewer: ревьюер, проверяет код и даёт обратную связь
        
        **Ключевое правило: вы обязаны использовать инструменты, а не выполнять эти задачи сами!**
        
        Формат вызова инструмента (строго соблюдайте):
        [TOOL_CALL:имя_инструмента:параметры]
        
        Примеры:
        
        Пример 1 — учебный план:
        Пользователь: «Хочу изучить list comprehensions в Python»
        Ваш ответ: [TOOL_CALL:call_planner:query=Составь учебный план по list comprehensions в Python]
        
        Пример 2 — упражнение:
        Пользователь: «Дай задачу по list comprehensions»
        Ваш ответ: [TOOL_CALL:call_exercise:query=Составь упражнение по list comprehensions]
        
        Пример 3 — ревью кода (самое важное!):
        Пользователь: «Проверь код: numbers = [1, 2, 3]»
        Ваш ответ: [TOOL_CALL:call_reviewer:query=Проверь код: numbers = [1, 2, 3]]
        
        Рабочий процесс (строго соблюдайте):
        1. Пользователь формулирует учебную цель → сразу вызывайте call_planner
        2. Пользователь просит упражнение → сразу вызывайте call_exercise
        3. Пользователь отправляет код или просит ревью → сразу вызывайте call_reviewer
        
        **Абсолютно запрещено**:
        - ❌ Самостоятельно составлять учебный план
        - ❌ Самостоятельно придумывать упражнения
        - ❌ Самостоятельно ревьюить код (даже если он простой)
        - ❌ Говорить «вызов инструмента не удался» и выполнять задачу сами
        
        Правильное поведение:
        - ✅ Распознать намерение пользователя
        - ✅ Сразу сформировать вызов инструмента (формат: [TOOL_CALL:имя:query=...])
        - ✅ Дождаться результата инструмента
        - ✅ Дружелюбно представить результат пользователю
        """
        
        # Инициализация родительского класса
        super().__init__(
            name="Tutor",
            llm=llm,
            system_prompt=system_prompt
        )
        
        # Обёртка подагентов в инструменты и регистрация
        self.add_tool(AgentTool(
            self.planner,
            name="call_planner",
            description="Вызов планировщика курса для составления персонального учебного плана"
        ))
        
        self.add_tool(AgentTool(
            self.exercise,
            name="call_exercise",
            description="Вызов автора задач для генерации программных упражнений по теме обучения"
        ))
        
        self.add_tool(AgentTool(
            self.reviewer,
            name="call_reviewer",
            description="Вызов ревьюера для проверки и обратной связи по коду пользователя"
        ))
