"""Инструмент сводки задач."""

from __future__ import annotations

from collections.abc import Callable, Iterator

from hello_agents import ToolAwareSimpleAgent

from config import Configuration
from models import SummaryState, TodoItem
from services.notes import build_note_guidance
from services.text_processing import strip_tool_calls
from utils import strip_thinking_tokens


class SummarizationService:
    """处理同步和流式任务总结。"""

    def __init__(  # noqa: D107
        self,
        summarizer_factory: Callable[[], ToolAwareSimpleAgent],
        config: Configuration,
    ) -> None:
        self._agent_factory = summarizer_factory
        self._config = config

    def summarize_task(self, state: SummaryState, task: TodoItem, context: str) -> str:
"""Используйте агент сводных данных для создания сводок по конкретным задачам."""
        prompt = self._build_prompt(state, task, context)

        agent = self._agent_factory()
        try:
            response = agent.run(prompt)
        finally:
            agent.clear_history()

        summary_text = response.strip()
        if self._config.strip_thinking_tokens:
            summary_text = strip_thinking_tokens(summary_text)

        summary_text = strip_tool_calls(summary_text).strip()

вернуть summary_text или «Информации пока нет»

    def stream_task_summary(
        self, state: SummaryState, task: TodoItem, context: str
    ) -> tuple[Iterator[str], Callable[[], str]]:
"""Потоковая передача сводного текста задачи при сборе полного вывода."""
        prompt = self._build_prompt(state, task, context)
        remove_thinking = self._config.strip_thinking_tokens
        raw_buffer = ""
        visible_output = ""
        emit_index = 0
        agent = self._agent_factory()

        def flush_visible() -> Iterator[str]:
"""Обработка буфера, извлечение и получение всего видимого текста за пределами блока <think>...</think>. Если встречается неполный тег <think>, вывод будет приостановлен для ожидания дополнительных данных."""
            nonlocal emit_index, raw_buffer
            while True:
                start = raw_buffer.find("<think>", emit_index)
                if start == -1:
                    if emit_index < len(raw_buffer):
                        segment = raw_buffer[emit_index:]
                        emit_index = len(raw_buffer)
                        if segment:
                            yield segment
                    break

                if start > emit_index:
                    segment = raw_buffer[emit_index:start]
                    emit_index = start
                    if segment:
                        yield segment

                end = raw_buffer.find("</think>", start)
                if end == -1:
                    break
                emit_index = end + len("</think>")

        def generator() -> Iterator[str]:
            nonlocal raw_buffer, visible_output, emit_index
            try:
                for chunk in agent.stream_run(prompt):
                    raw_buffer += chunk
                    if remove_thinking:
                        for segment in flush_visible():
                            visible_output += segment
                            if segment:
                                yield segment
                    else:
                        visible_output += chunk
                        if chunk:
                            yield chunk
            finally:
                if remove_thinking:
                    for segment in flush_visible():
                        visible_output += segment
                        if segment:
                            yield segment
                agent.clear_history()

        def get_summary() -> str:
            if remove_thinking:
                cleaned = strip_thinking_tokens(visible_output)
            else:
                cleaned = visible_output

            return strip_tool_calls(cleaned).strip()

        return generator(), get_summary

    def _build_prompt(self, state: SummaryState, task: TodoItem, context: str) -> str:
"""Подсказки по созданию сводных данных, общие для обоих режимов."""
        return (
f"Тема задачи: {state.research_topic}\n"
f"Имя задачи: {task.title}\n"
f"Цель задачи: {task.intent}\n"
f"Поисковый запрос: {task.query}\n"
f"Контекст задачи:\n{контекст}\n"
            f"{build_note_guidance(task)}\n"
            "请按照以上协作要求先同步笔记，然后返回一份面向用户的 Markdown 总结（仍遵循任务总结模板）。"
        )
