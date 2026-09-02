# src/tools/mood_music_tool.py

from hello_agents.tools import Tool as BaseTool
from src.utils.loader import load_mood_music_map

class MoodMusicTool(BaseTool):
    """
    Инструмент «эмоция → музыкальные рекомендации» (полностью имитация)
    """

    def __init__(self):
        super().__init__(
            name="mood_music_tool",
            description = "По описанию настроения пользователя возвращает список музыкальных рекомендаций"
        )
        self.name = "mood_music_tool"
        self.description = "По описанию настроения пользователя возвращает список музыкальных рекомендаций"
        self.mood_map = load_mood_music_map()

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Ввод пользователя"}
            },
            "required": ["query"]
        }

    def run(self, query: str) -> str:
        """
        query: описание настроения пользователя
        """
        # Простое сопоставление по правилам (стабильно)
        for mood, songs in self.mood_map.items():
            if mood in query:
                return self._format_result(mood, songs)

        # fallback
        return self._format_result(
            "Не распознано",
            ["Tycho - Awake", "Ólafur Arnalds - Near Light"]
        )

    def _format_result(self, mood, songs):
        result = f"🎧 Распознанное настроение: {mood}\n\nРекомендуемая музыка:\n"
        for i, song in enumerate(songs, 1):
            result += f"{i}. {song}\n"
        return result
