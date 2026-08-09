"""Service that consolidates task results into the final report."""

from __future__ import annotations

import json

from hello_agents import ToolAwareSimpleAgent

from models import SummaryState
from config import Configuration
from utils import strip_thinking_tokens
from services.text_processing import strip_tool_calls


class ReportingService:
    """Generates the final structured report."""

    def __init__(self, report_agent: ToolAwareSimpleAgent, config: Configuration) -> None:
        self._agent = report_agent
        self._config = config

    def generate_report(self, state: SummaryState) -> str:
        """Generate a structured report based on completed tasks."""

        tasks_block = []
        for task in state.todo_items:
            summary_block = task.summary or "Информации пока нет"
            sources_block = task.sources_summary or "Источника пока нет"
            tasks_block.append(
                f"### Задача {task.id}: {task.title}\n"
                f"-Цель задачи: {task.intent}\n"
                f"- Поисковый запрос: {task.query}\n"
                f"- Статус выполнения: {task.status}\n"
                f"- Сводка задачи:\n{summary_block}\n"
                f"- Обзор источника:\n{sources_block}\n"
            )

        note_references = []
        for task in state.todo_items:
            if task.note_id:
                note_references.append(
                    f"– Задача {task.id}《{task.title}》: note_id={task.note_id}"
                )

        notes_section = "\n".join(note_references) if note_references else "- Пока нет доступных заметок о задачах"

        read_template = json.dumps({"action": "read", "note_id": "<note_id>"}, ensure_ascii=False)
        create_conclusion_template = json.dumps(
            {
                "action": "create",
                "title": f"Отчет об исследовании: {state.research_topic}",
                "note_type": "conclusion",
                "tags": ["deep_research", "report"],
                "content": "Пожалуйста, суммируйте ключевые моменты итогового отчета здесь.",
            },
            ensure_ascii=False,
        )

        prompt = (
            f"Тема исследования: {state.research_topic}\n"
            f"Обзор задачи:\n{''.join(tasks_block)}\n"
            f"Доступные заметки к задачам:\n{notes_section}\n"
            f"Используйте формат для каждого примечания к задаче: [TOOL_CALL:note:{read_template}], чтобы прочитать содержимое, объединить всю информацию и написать отчет. \п"
            f"Если вам нужно вывести сводные выводы, вы можете дополнительно вызвать: [TOOL_CALL:note:{create_conclusion_template}], чтобы сохранить основные моменты отчета."
        )

        response = self._agent.run(prompt)
        self._agent.clear_history()

        report_text = response.strip()
        if self._config.strip_thinking_tokens:
            report_text = strip_thinking_tokens(report_text)

        report_text = strip_tool_calls(report_text).strip()

        return report_text or "Не удалось создать отчет. Проверьте введенные данные."

