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
            summary_block = task.summary or "Информация недоступна"
            sources_block = task.sources_summary or "Источники отсутствуют"
            tasks_block.append(
                f"### Задача {task.id}: {task.title}\n"
                f"- Цель задачи: {task.intent}\n"
                f"- Поисковый запрос: {task.query}\n"
                f"- Статус выполнения: {task.status}\n"
                f"- Сводка задачи:\n{summary_block}\n"
                f"- Обзор источников:\n{sources_block}\n"
            )

        note_references = []
        for task in state.todo_items:
            if task.note_id:
                note_references.append(
                    f"- Задача {task.id} «{task.title}»: note_id={task.note_id}"
                )

        notes_section = "\n".join(note_references) if note_references else "- Заметки по задачам недоступны"

        read_template = json.dumps({"action": "read", "note_id": "<note_id>"}, ensure_ascii=False)
        create_conclusion_template = json.dumps(
            {
                "action": "create",
                "title": f"Исследовательский отчёт: {state.research_topic}",
                "note_type": "conclusion",
                "tags": ["deep_research", "report"],
                "content": "Зафиксируйте здесь ключевые выводы итогового отчёта",
            },
            ensure_ascii=False,
        )

        prompt = (
            f"Тема исследования: {state.research_topic}\n"
            f"Обзор задач:\n{''.join(tasks_block)}\n"
            f"Доступные заметки по задачам:\n{notes_section}\n"
            f"Для каждой заметки используйте формат: [TOOL_CALL:note:{read_template}] для чтения, затем объедините всё в отчёт.\n"
            f"Для итоговых выводов можно дополнительно вызвать: [TOOL_CALL:note:{create_conclusion_template}] для сохранения ключевых пунктов."
        )

        response = self._agent.run(prompt)
        self._agent.clear_history()

        report_text = response.strip()
        if self._config.strip_thinking_tokens:
            report_text = strip_thinking_tokens(report_text)

        report_text = strip_tool_calls(report_text).strip()

        return report_text or "Не удалось сформировать отчёт. Проверьте входные данные."
