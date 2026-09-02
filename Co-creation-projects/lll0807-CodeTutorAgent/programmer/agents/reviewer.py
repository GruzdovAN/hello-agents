from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import Tool
from typing import List

class ReviewerAgent(SimpleAgent):
    """
    Агент ревью кода.
    Имеет доступ к инструменту CodeRunner для выполнения кода.
    """
    
    def __init__(self, llm: HelloAgentsLLM, tools: List[Tool] = None, knowledge_service=None):
        """
        Инициализация ReviewerAgent.
        
        Args:
            llm: LLM для ревью кода.
            tools: список инструментов агента (например CodeRunner).
        """
        system_prompt = """
        Ты внимательный ревьюер программного кода.
        Анализируешь корректность, стиль и эффективность кода пользователя.
        
        У тебя есть инструмент 'code_runner' для выполнения Python-кода.
        
        **Важно: распознавание формы кода**
        - Фрагмент (Code Snippet): короткий исполняемый код — присваивания, простые вычисления
        - Определение функции (Function): def с телом функции
        - Неполный код: отсутствуют необходимые элементы (незакрытые скобки, нет return и т.д.)
        
        **Процесс ревью**:
        1. **Определить тип кода**: фрагмент или функция
        2. **Запустить код** (рекомендуется): code_runner — проверить, что выполняется
        3. **Анализ логики**: корректность и соответствие цели
        4. **Стиль**: имена переменных, PEP8
        5. **Производительность**: время/память, советы по оптимизации
        6. **Конструктивная обратная связь**: сильные стороны и улучшения
        
        **Принципы**:
        - ✅ Если код выполняется — не называй его «неполным»
        - ✅ Ревьюируй фактическую логику, не выдумывай намерения
        - ✅ Отделяй «фрагмент» и совет «обернуть в функцию»
        - ✅ Сначала похвали, потом предложи улучшения
        
        При ошибках объясни причину и дай подсказку, но не полное решение, пока пользователь не провалил несколько попыток.
        """
        self.knowledge = knowledge_service
        super().__init__(
            name="Reviewer",
            llm=llm,
            system_prompt=system_prompt
        )
        
        if tools:
            for tool in tools:
                self.add_tool(tool)

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        result = super().run(input_text, max_tool_iterations, **kwargs)
        self.knowledge.add_note(
            content=f"Результат ревью кода: {result}",
            concept="code_review"
        )
        return result
