"""Сервис, объединяющий результаты задач в итоговый отчет."""

from __future__ import annotations

import json

from hello_agents import ToolAwareSimpleAgent

from config import Configuration
from models import SummaryState
from services.text_processing import strip_tool_calls
from utils import strip_thinking_tokens


class ReportingService:
"""Создать окончательный структурированный отчет."""

    def __init__(  # noqa: D107
        self, report_agent: ToolAwareSimpleAgent, config: Configuration
    ) -> None:
        self._agent = report_agent
        self._config = config

    def generate_report(self, state: SummaryState) -> str:
        """
Формируйте структурированные отчеты на основе выполненных задач.

        Args:
состояние: статус исследования, включая результаты задач и примечания.

        Returns:
Текст отчета в формате Markdown.
        """
        tasks_block = []
        for task in state.todo_items:
            summary_block = task.summary or "暂无可用信息"
            sources_block = task.sources_summary or "暂无来源"
            tasks_block.append(
                f"### 任务 {task.id}: {task.title}\n"
f"-Цель задачи: {task.intent}\n"
f"- Поисковый запрос: {task.query}\n"
f"-Статус выполнения: {task.status}\n"
f"-Сводка задачи:\n{summary_block}\n"
f"- Обзор источника:\n{sources_block}\n"
            )

        note_references = []
        for task in state.todo_items:
            if task.note_id:
                note_references.append(
f"- 任务 {task.id}《{task.title}》:note_id={task.note_id}"
                )

        notes_section = (
"\n".join(note_references) if note_references else "- Заметки к задаче пока недоступны"
        )

        read_template = json.dumps(
            {"action": "read", "note_id": "<note_id>"}, ensure_ascii=False
        )
# Шаблон заключительной записки, позвольте LLM самостоятельно заполнить фактическое содержание
        create_conclusion_template = json.dumps(
            {
                "action": "create",
                "title": f"研究报告：{state.research_topic}",
                "note_type": "conclusion",
                "tags": ["deep_research", "report"],
"content": "<Пожалуйста, укажите здесь основные положения отчета>",
            },
            ensure_ascii=False,
        )

        prompt = (
f"Тема исследования: {state.research_topic}\n"
f"Обзор задачи:\n{''.join(tasks_block)}\n"
f"Доступные заметки к задаче:\n{notes_section}\n"
f"Пожалуйста, используйте формат для каждого примечания к задаче: [TOOL_CALL:note:{read_template}], чтобы прочитать содержимое, объединить всю информацию и написать отчет.\n"
f"Если вам необходимо вывести сводные выводы, вы можете дополнительно вызвать инструмент заметок, чтобы сохранить ключевые точки отчета. Шаблон параметра следующий (содержимое необходимо заменить фактическими ключевыми точками отчета):\n"
            f"  {create_conclusion_template}\n"
            "**重要**：content 字段必须填写本次研究的实际核心发现和结论，不要使用占位文本。"
        )

        response = self._agent.run(prompt)
        self._agent.clear_history()

        report_text = response.strip()
        if self._config.strip_thinking_tokens:
            report_text = strip_thinking_tokens(report_text)

        report_text = strip_tool_calls(report_text).strip()

return report_text или «Не удалось создать отчет, проверьте ввод».
