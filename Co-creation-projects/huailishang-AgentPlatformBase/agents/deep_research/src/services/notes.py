"""Helpers for coordinating note tool usage instructions."""

from __future__ import annotations

import json

from models import TodoItem


def build_note_guidance(task: TodoItem) -> str:
    """Generate note tool usage guidance for a specific task."""

    tags_list = ["deep_research", f"task_{task.id}"]
    tags_literal = json.dumps(tags_list, ensure_ascii=False)

    if task.note_id:
        read_payload = json.dumps({"action": "read", "note_id": task.note_id}, ensure_ascii=False)
        update_payload = json.dumps(
            {
                "action": "update",
                "note_id": task.note_id,
                "task_id": task.id,
                "title": f"Задача {task.id}: {task.title}",
                "note_type": "task_state",
                "tags": tags_list,
                "content": "Добавьте новую информацию этого раунда в обзор задачи",
            },
            ensure_ascii=False,
        )

        return (
            "Инструкции по работе с заметками:\n"
            f"- ID заметки текущей задачи: {task.note_id}.\n"
            f"- Перед написанием сводки вызовите: [TOOL_CALL:note:{read_payload}] для получения актуального содержимого.\n"
            f"- После анализа вызовите: [TOOL_CALL:note:{update_payload}] для синхронизации новых данных.\n"
            "- При обновлении сохраняйте структуру абзацев, добавляя новое в соответствующие разделы.\n"
            f"- Рекомендуется оставить tags как {tags_literal}, чтобы другие агенты могли быстро найти заметку.\n"
            "- После успешной синхронизации заметки выведите сводку для пользователя.\n"
        )

    create_payload = json.dumps(
        {
            "action": "create",
            "task_id": task.id,
            "title": f"Задача {task.id}: {task.title}",
            "note_type": "task_state",
            "tags": tags_list,
            "content": "Зафиксируйте обзор задачи и обзор источников",
        },
        ensure_ascii=False,
    )

    return (
        "Инструкции по работе с заметками:\n"
        f"- Для текущей задачи заметка ещё не создана. Сначала вызовите: [TOOL_CALL:note:{create_payload}].\n"
        "- После создания сохраните возвращённый note_id и используйте его во всех последующих обновлениях.\n"
        "- После синхронизации заметки выведите сводку для пользователя.\n"
    )
