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
                "content": "Пожалуйста, добавьте новую информацию в этом раунде в обзор задачи.",
            },
            ensure_ascii=False,
        )

        return (
            "Обратите внимание на правила сотрудничества:\n"
            f"– Идентификатор текущей заметки к задаче: {task.note_id}. \п"
            f"– Прежде чем писать резюме, вы должны позвонить: [TOOL_CALL:note:{read_payload}], чтобы получить последний контент. \п"
            f"- После завершения анализа вызовите: [TOOL_CALL:note:{update_payload}] для синхронизации дополнительной информации. \п"
            "– При обновлении сохраняйте исходную структуру абзацев и добавляйте новое содержимое в соответствующие абзацы. \п"
            f"- Рекомендуется сохранять теги как {tags_literal}, чтобы другие агенты могли быстро их найти. \п"
            "- После успешной синхронизации с заметками выводится ориентированная на пользователя сводка. \п"
        )

    create_payload = json.dumps(
        {
            "action": "create",
            "task_id": task.id,
            "title": f"Задача {task.id}: {task.title}",
            "note_type": "task_state",
            "tags": tags_list,
            "content": "Пожалуйста, запишите обзор задачи и обзор источника.",
        },
        ensure_ascii=False,
    )

    return (
        "Обратите внимание на правила сотрудничества:\n"
        f"- Текущая задача не создала заметку, сначала позвоните: [TOOL_CALL:note:{create_payload}]. \п"
        "- Запишите note_id, возвращенный после успешного создания, и повторно используйте его во всех последующих обновлениях. \п"
        "- После синхронизации заметок выведите сводку для пользователей. \п"
    )

