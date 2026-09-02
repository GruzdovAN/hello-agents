from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools.builtin.note_tool import NoteTool


class PlannerAgent(SimpleAgent):
    """
    Агент создания и обновления пути обучения.
    """

    def __init__(self, llm: HelloAgentsLLM, knowledge_service):
        """
        Инициализация PlannerAgent.
        
        Args:
            llm: экземпляр LLM для генерации плана.
        """
        self.knowledge = knowledge_service


        system_prompt = """
        Ты профессиональный планировщик курсов по компьютерным наукам.
        Создаёшь персональный путь обучения по целям и текущему уровню пользователя.
        
        При создании плана:
        1. Анализируй цель (например, «data science в Python»).
        2. Разбей на логические модули/этапы.
        3. Для каждого модуля перечисли ключевые концепции.
        4. В конце названия каждого этапа используй Markdown чеклист:
           - `[ ]` — не завершено
           - `[x]` — завершено (по умолчанию при создании — не завершено)
        5. При создании плана строго следуй формату:

            ### План обучения
            
            # Тема обучения: <тема>
            
            ## Цели обучения
            - ...
            
            ## Путь обучения
            1. Этап 1: <название этапа> []
               - ключевые концепции
            2. Этап 2: <название этапа> []
               - ключевые концепции
            
            ## Рекомендации
            - ...
            
            Весь план — готовый Markdown-документ для сохранения.
        
        При запросе【обновить план / обновить прогресс】:
        
        1. Считай, что документ «План обучения» уже существует.
        2. По последним действиям пользователя (завершил тему, отправил код и прошёл ревью):
           - обнови соответствующий `[ ]` на `[x]`
        3. Выведи【полный обновлённый Markdown план】 (не только diff), начиная с ### Обновление плана обучения.
        
        """
        super().__init__(
            name="Planner",
            llm=llm,
            system_prompt=system_prompt
        )
        self.note_tool = NoteTool(workspace="notes")

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        # ===== Обзор прошлого обучения =====
        if any(k in input_text.casefold() for k in ["раньше", "обзор", "изучал", "помню", "вспомни"]):
            return self.knowledge.recall(input_text)
        result = super().run(input_text)
        # Planner определяет: это план обучения
        if result.strip().startswith("### План обучения"):
            self._save_learning_plan(result, input_text)
        if result.strip().startswith("### Обновление плана обучения"):
            self._update_learning_plan(result, input_text)

        return result

    def _update_learning_plan(self, markdown: str, input_text: str):
        title_and_note_id_str = self.knowledge.recall(input_text)
        self.note_tool.run({
            "note_id": self.note_tool.notes_index['notes'][-1]['id'],
            "action": "update",
            "title": "План обучения",
            "content": markdown,
            "tags": ["learning-plan", "progress"]
        })

    def _save_learning_plan(self, markdown: str, input_text: str):

        note_id = self.note_tool.run({
            "action": "create",
            "title": "План обучения",
            "content": markdown,
            "tags": ["learning-plan", "planner"]
        })
        content = f"title: {input_text} note_id: {note_id}"
        self.knowledge.add_note(content=content)
