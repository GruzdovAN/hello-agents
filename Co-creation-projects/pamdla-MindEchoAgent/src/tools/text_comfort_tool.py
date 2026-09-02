# src/tools/text_comfort_tool.py

from hello_agents.tools import Tool as BaseTool

class TextComfortTool(BaseTool):

    def __init__(self):
        super().__init__(
            name="text_comfort_tool",
            description="Предоставляет ключевые пункты успокоения; LLM формирует естественный текст"
        )
        self.name = "text_comfort_tool"
        self.description = "Предоставляет ключевые пункты успокоения; LLM формирует естественный текст"

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
            "Ключевые пункты успокоения:\n"
            "1. Эмпатия: признать, что эмоции существуют\n"
            "2. Разрешить паузу: не нужно сразу чувствовать себя лучше\n"
            "3. Маленькие действия: глубокое дыхание, короткий отдых, лёгкая музыка\n"
            "4. При продолжающихся трудностях — эскалация к SleepAgent"
        )
