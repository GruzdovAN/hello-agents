# src/tools/mood_summary_tool.py

from hello_agents.tools import Tool as BaseTool

class MoodSummaryTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="mood_summary_tool",
            description="Шаблон сводки настроения для долгосрочной памяти (финальный текст генерирует LLM)"
        )
        self.name = "mood_summary_tool"
        self.description = "Шаблон сводки настроения для долгосрочной памяти (финальный текст генерирует LLM)"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Ввод пользователя"}
            },
            "required": ["query"]
        }

    def run(self, query: str) -> str:
        return (
            "Сформируй короткую сводку настроения (для долгосрочной памяти) на основе:\n"
            f"Ввод пользователя: {query}\n"
            "Должно включать:\n"
            "1. Текущее настроение (1–2 предложения)\n"
            "2. Триггеры (если есть)\n"
            "3. Возможные долгосрочные предпочтения (музыка/эмоции)\n"
        )
