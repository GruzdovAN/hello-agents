"""Помощник по согласованию инструкций по использованию инструментов для заметок."""

from __future__ import annotations

import json

from models import TodoItem


def build_note_guidance(task: TodoItem) -> str:
"""Создание инструкций для инструментов заметок для конкретных задач."""
    tags_list = ["deep_research", f"task_{task.id}"]
    tags_literal = json.dumps(tags_list, ensure_ascii=False)

    if task.note_id:
        read_payload = json.dumps({"action": "read", "note_id": task.note_id}, ensure_ascii=False)
# Предоставляйте только шаблон для обновления заметок и позвольте LLM самостоятельно заполнить фактический контент исследования.
        update_template = json.dumps(
            {
                "action": "update",
                "note_id": task.note_id,
                "task_id": task.id,
                "title": f"任务 {task.id}: {task.title}",
                "note_type": "task_state",
                "tags": tags_list,
"content": "<Пожалуйста, заполните здесь обновленный полный контент>",
            },
            ensure_ascii=False,
        )

        return (
"Обратите внимание на правила сотрудничества:\n"
f"-Идентификатор текущей заметки к задаче: {task.note_id}.\n"
            f"- 在书写总结前必须调用：[TOOL_CALL:note:{read_payload}] 获取最新内容。\n"
            f"- 完成分析后更新笔记，参数模板如下（需将 content 替换为实际内容）：\n"
            f"  {update_template}\n"
            "- **重要**：content 字段必须包含原有内容加上本轮新增的研究发现，不要使用占位文本。\n"
«-Сохраняйте исходную структуру абзацев при обновлении. Добавьте новое содержимое в соответствующие абзацы.\n»
            f"- 建议 tags 保持为 {tags_literal}，保证其他 Agent 可快速定位。\n"
"- После успешной синхронизации с заметками вывести сводку для пользователей.\n"
        )

# Предоставляйте только шаблоны для создания заметок и позвольте LLM самостоятельно заполнять фактический контент исследования.
    create_template = json.dumps(
        {
            "action": "create",
            "task_id": task.id,
            "title": f"任务 {task.id}: {task.title}",
            "note_type": "task_state",
            "tags": tags_list,
"content": "<Пожалуйста, заполните здесь содержание сводки задачи>",
        },
        ensure_ascii=False,
    )

    return (
"Обратите внимание на правила сотрудничества:\n"
f"- Для текущей задачи не создано заметок.\n"
f"- Пожалуйста, используйте формат при создании заметок: [TOOL_CALL:note:{{...}}], шаблон параметра следующий (содержимое необходимо заменить фактическим резюме исследования):\n"
        f"  {create_template}\n"
        "- **重要**：content 字段必须填写本次任务的实际研究发现和关键信息，不要使用占位文本。\n"
"- Запишите note_id, возвращенный после успешного создания, и повторно используйте его во всех последующих обновлениях.\n"
"- После синхронизации заметок вывести сводку для пользователей.\n"
    )

