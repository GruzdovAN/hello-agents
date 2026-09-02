from hello_agents.tools.builtin.note_tool import NoteTool

class LearningNotesService:
    def __init__(self, workspace: str):
        self.note_tool = NoteTool(workspace=workspace)

    def save_learning_progress(
        self,
        user_id: str,
        progress: "LearningProgress"
    ):
        """Сохраняет путь обучения и прогресс"""
        content = self._format_learning_content(progress)

        self.note_tool.run({
            "action": "create",
            "title": f"Прогресс обучения｜{progress.topic}",
            "content": content,
            "tags": [
                "learning",
                "progress",
                progress.level,
                user_id
            ]
        })

    def _format_learning_content(self, progress: "LearningProgress") -> str:
        content = f"# Тема обучения: {progress.topic}\n\n"
        content += f"**Текущий уровень**: {progress.level}\n\n"

        # Путь обучения
        content += "## Путь обучения\n\n"
        for idx, step in enumerate(progress.steps, start=1):
            status_icon = {
                "completed": "✅",
                "in_progress": "⏳",
                "not_started": "⬜"
            }.get(step.status, "⬜")

            content += f"{idx}. {status_icon} **{step.title}**\n"
            if step.notes:
                content += f"   - Заметка: {step.notes}\n"
        content += "\n"

        # Освоенные темы
        if progress.mastered_points:
            content += "## Освоенные темы\n\n"
            for p in progress.mastered_points:
                content += f"- ✅ {p}\n"
            content += "\n"

        # Слабые места
        if progress.weak_points:
            content += "## Слабые места\n\n"
            for p in progress.weak_points:
                content += f"- ⚠️ {p}\n"
            content += "\n"

        # Следующий шаг
        content += "## Рекомендации для следующего шага\n\n"
        content += f"{progress.next_suggestion}\n"

        return content
