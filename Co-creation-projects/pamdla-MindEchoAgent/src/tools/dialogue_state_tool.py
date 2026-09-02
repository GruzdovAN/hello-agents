# src/tools/dialogue_state_tool.py

from hello_agents.tools import Tool as BaseTool
from src.utils.state import DialogueState

class DialogueStateTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="dialogue_state_tool",
            description="Определяет, на каком этапе должен находиться текущий диалог"
        )
        self.name = "dialogue_state_tool"
        self.description = "Определяет, на каком этапе должен находиться текущий диалог"

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Ввод пользователя"},
                "current_state": {"type": "string", "description": "Текущее состояние"}
            },
            "required": ["query"]
        }

    def run(self, query: str, current_state: str = "") -> str:
        # MVP: срабатывание по ключевым словам
        lowered = query.casefold()
        if any(k in lowered for k in ("не могу уснуть", "бессонница", "тревог", "тревога", "бессон")):
            return DialogueState.ESCALATE.value
        if any(k in lowered for k in ("слуш", "музык")):
            return DialogueState.MUSIC.value
        if any(k in lowered for k in ("тяжело", "плохо", "груст", "несчаст")):
            return DialogueState.COMFORT.value
        return DialogueState.MOOD.value
