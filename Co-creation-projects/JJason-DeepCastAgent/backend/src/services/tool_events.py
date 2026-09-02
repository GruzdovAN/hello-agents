"""Утилита для сбора и предоставления информации о событиях запуска инструментов."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any

from models import SummaryState, TodoItem

logger = logging.getLogger(__name__)


@dataclass
class ToolCallEvent:
"""Внутреннее представление событий вызова инструмента."""

    id: int
    agent: str
    tool: str
    raw_parameters: str
    parsed_parameters: dict[str, Any]
    result: str
    task_id: int | None
    note_id: str | None


class ToolCallTracker:
"""Собирайте события вызова инструмента и преобразуйте их в полезные данные SSE."""

    def __init__(self, notes_workspace: str | None) -> None:
        self._notes_workspace = notes_workspace
        self._events: list[ToolCallEvent] = []
        self._cursor = 0
        self._lock = Lock()
        self._event_sink: Callable[[dict[str, Any]], None] | None = None

    def record(self, payload: dict[str, Any]) -> None:
        """
Записывайте статус вызова инструментов модели, чтобы облегчить журналирование и внешнее отображение.
        
        Args:
полезные данные: полезные данные события вызова инструмента, включая имя инструмента, параметры и результаты.
        """
        agent_name = str(payload.get("agent_name") or "unknown")
        tool_name = str(payload.get("tool_name") or "unknown")
        raw_parameters = str(payload.get("raw_parameters") or "")
        parsed_parameters = payload.get("parsed_parameters") or {}
        result_text = str(payload.get("result") or "")

        if not isinstance(parsed_parameters, dict):
            parsed_parameters = {}

        task_id = self._infer_task_id(parsed_parameters)
        note_id: str | None = None

        if tool_name == "note":
            note_id = parsed_parameters.get("note_id")
            if note_id is None:
                note_id = self._extract_note_id(result_text)

        event = ToolCallEvent(
            id=len(self._events) + 1,
            agent=agent_name,
            tool=tool_name,
            raw_parameters=raw_parameters,
            parsed_parameters=parsed_parameters,
            result=result_text,
            task_id=task_id,
            note_id=note_id,
        )

        with self._lock:
            self._events.append(event)

        logger.info(
            "Tool call recorded: agent=%s tool=%s task_id=%s note_id=%s parsed_parameters=%s",
            agent_name,
            tool_name,
            task_id,
            note_id,
            parsed_parameters,
        )

        sink = self._event_sink
        if sink:
            sink(self._build_payload(event, step=None))

    # ------------------------------------------------------------------
# помощник по выбросам
    # ------------------------------------------------------------------
    def drain(self, state: SummaryState, *, step: int | None = None) -> list[dict[str, Any]]:
        """
Извлеките события вызова инструмента, которые не были использованы, и синхронизируйте note_id задачи.
        
Этот метод является потокобезопасным и удаляет извлеченные события, чтобы избежать дублирования обработки.
При этом будет проверяться вызов инструмента заметок и обновляться note_id в статусе задачи.
        
        Args:
состояние: текущий статус исследования.
шаг: необязательный номер шага для добавления к возвращаемому событию.
            
        Returns:
Подготовьте список словарей событий для отправки во внешний интерфейс.
        """
        with self._lock:
            if self._cursor >= len(self._events):
                return []
            new_events = self._events[self._cursor :]
            self._cursor = len(self._events)

        if state.todo_items:
            for event in new_events:
                task_id = event.task_id
                note_id = event.note_id
                if task_id is None or not note_id:
                    continue
                self._attach_note_to_task(state.todo_items, task_id, note_id)

        payloads: list[dict[str, Any]] = []
        for event in new_events:
            payload = self._build_payload(event, step=step)
            payloads.append(payload)

        return payloads

    def reset(self) -> None:
        """
Сбрасывает текущие зарегистрированные события вызова инструмента.
        
Этот метод очищает список внутренних событий и сбрасывает курсор для использования в том же
Избегайте утечки событий между задачами и сеансами при повторном использовании в экземплярах Tracker.
        """
        with self._lock:
            self._events.clear()
            self._cursor = 0
    def as_dicts(self) -> list[dict[str, Any]]:
        """
Предоставьте снимок исходного события для обратной совместимости.
        
        Returns:
Список словарей, содержащий все события вызова инструмента.
        """
        with self._lock:
            return [
                {
                    "id": event.id,
                    "agent": event.agent,
                    "tool": event.tool,
                    "raw_parameters": event.raw_parameters,
                    "parsed_parameters": event.parsed_parameters,
                    "result": event.result,
                    "task_id": event.task_id,
                    "note_id": event.note_id,
                }
                for event in self._events
            ]

    def set_event_sink(self, sink: Callable[[dict[str, Any]], None] | None) -> None:
        """
Зарегистрируйте обратный вызов, чтобы получать немедленные уведомления о событиях инструмента.
        
        Args:
приемник: функция обратного вызова, которая получает словарь событий.
        """
        self._event_sink = sink

    def _build_payload(self, event: ToolCallEvent, step: int | None) -> dict[str, Any]:
        payload = {
            "type": "tool_call",
            "event_id": event.id,
            "agent": event.agent,
            "tool": event.tool,
            "parameters": event.parsed_parameters,
            "result": event.result,
            "task_id": event.task_id,
            "note_id": event.note_id,
        }
        if event.note_id and self._notes_workspace:
            note_path = Path(self._notes_workspace) / f"{event.note_id}.md"
            payload["note_path"] = str(note_path)
        if step is not None:
            payload["step"] = step
        return payload

    # ------------------------------------------------------------------
# Внутренний помощник
    # ------------------------------------------------------------------
    def _attach_note_to_task(self, tasks: list[TodoItem], task_id: int, note_id: str) -> None:
"""Обновить соответствующие элементы TODO, используя метаданные заметки."""
        for task in tasks:
            if task.id != task_id:
                continue

            if task.note_id != note_id:
                task.note_id = note_id
                if self._notes_workspace:
                    task.note_path = str(Path(self._notes_workspace) / f"{note_id}.md")
            elif task.note_path is None and self._notes_workspace:
                task.note_path = str(Path(self._notes_workspace) / f"{note_id}.md")
            break

    def _infer_task_id(self, parameters: dict[str, Any]) -> int | None:
"""Попытка получить идентификатор задачи из параметров инструмента."""
        if not parameters:
            return None

        if "task_id" in parameters:
            try:
                return int(parameters["task_id"])
            except (TypeError, ValueError):
                pass

        tags = parameters.get("tags")
        if isinstance(tags, list):
            for tag in tags:
                match = re.search(r"task_(\d+)", str(tag))
                if match:
                    return int(match.group(1))

        title = parameters.get("title")
        if isinstance(title, str):
            match = re.search(r"任务\s*(\d+)", title)
            if match:
                return int(match.group(1))

        return None

    def _extract_note_id(self, response: str) -> str | None:
        if not response:
            return None

        match = re.search(r"ID:\s*([^\n]+)", response)
        if match:
            return match.group(1).strip()
        return None
