"""TodoTool — лёгкая доска задач

Цели MVP:
- только add / list / update
- статусы: pending | in_progress | completed (строго: не более 1 in_progress одновременно)
- хранение: .helloagents/todos/todos.json, атомарная запись + простой бэкап
- вывод: сгруппированный список по статусам для удобства LLM
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Tool, ToolParameter


STATUSES = ("pending", "in_progress", "completed")


@dataclass
class TodoItem:
    id: int
    title: str
    desc: str = ""
    status: str = "pending"
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoItem":
        return cls(
            id=int(data["id"]),
            title=data.get("title", ""),
            desc=data.get("desc", ""),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class TodoTool(Tool):
    def __init__(self, workspace: str):
        super().__init__(
            name="todo",
            description="Инструмент задач: add/list/update; статусы pending|in_progress|completed (одновременно только 1 in_progress)",
        )
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.data_file = self.workspace / "todos.json"
        self.backup_file = self.workspace / "todos.json.bak"
        if not self.data_file.exists():
            self._save({"items": []})

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(name="action", type="string", description="add | list | update", required=True),
            ToolParameter(name="title", type="string", description="Заголовок задачи (обязателен для add, опционален для update)", required=False),
            ToolParameter(name="desc", type="string", description="Описание задачи (опционально)", required=False),
            ToolParameter(name="status", type="string", description="pending|in_progress|completed (опционально для update)", required=False),
            ToolParameter(name="id", type="integer", description="ID задачи для обновления (обязателен для update)", required=False),
        ]

    # ---------------- core ops ----------------
    def run(self, parameters: Dict[str, Any]) -> str:
        if not self.validate_parameters(parameters):
            return "Отсутствуют параметры: требуется action (add/list/update)."
        action = str(parameters.get("action", "")).strip().lower().rstrip("]")
        if action == "add":
            return self._add(title=parameters.get("title", ""), desc=parameters.get("desc", ""), status=parameters.get("status", "pending"))
        if action == "list":
            return self._list(status_filter=parameters.get("status"))
        if action == "update":
            return self._update(
                todo_id=parameters.get("id"),
                title=parameters.get("title"),
                desc=parameters.get("desc"),
                status=parameters.get("status"),
            )
        return "Неподдерживаемый action, ожидается add/list/update."

    # ---------------- storage ----------------
    def _load(self) -> Dict[str, Any]:
        with open(self.data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self, data: Dict[str, Any]) -> None:
        tmp = self.data_file.with_suffix(".tmp")
        if self.data_file.exists():
            try:
                self.backup_file.write_text(self.data_file.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.data_file)

    # ---------------- helpers ----------------
    def _next_id(self, items: List[TodoItem]) -> int:
        return (max([i.id for i in items], default=0) + 1) if items else 1

    def _now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")

    def _enforce_single_in_progress(self, items: List[TodoItem], incoming_status: str, incoming_id: Optional[int]) -> Optional[str]:
        if incoming_status != "in_progress":
            return None
        for it in items:
            if it.status == "in_progress" and (incoming_id is None or it.id != incoming_id):
                return f"Уже есть задача в работе #{it.id} «{it.title}». Сначала завершите или обновите её."
        return None

    # ---------------- actions ----------------
    def _add(self, title: str, desc: str, status: str) -> str:
        title = (title or "").strip()
        if not title:
            return "❌ add не выполнен: title не может быть пустым."
        status = status if status in STATUSES else "pending"
        data = self._load()
        items = [TodoItem.from_dict(i) for i in data.get("items", [])]
        conflict = self._enforce_single_in_progress(items, status, None)
        if conflict:
            return f"❌ add не выполнен: {conflict}"
        now = self._now()
        new_item = TodoItem(id=self._next_id(items), title=title, desc=desc or "", status=status, created_at=now, updated_at=now)
        items.append(new_item)
        self._save({"items": [asdict(i) for i in items]})
        return f"✅ Добавлено #{new_item.id} [{new_item.status}] {new_item.title}"

    def _update(self, todo_id: Any, title: Optional[str], desc: Optional[str], status: Optional[str]) -> str:
        try:
            tid = int(todo_id)
        except Exception:
            return "❌ update не выполнен: требуется корректный id."
        if status and status not in STATUSES:
            return "❌ update не выполнен: status должен быть pending|in_progress|completed."

        data = self._load()
        items = [TodoItem.from_dict(i) for i in data.get("items", [])]
        target = next((i for i in items if i.id == tid), None)
        if not target:
            return f"❌ update не выполнен: задача с id={tid} не найдена."

        conflict = self._enforce_single_in_progress(items, status or target.status, tid)
        if conflict:
            return f"❌ update не выполнен: {conflict}"

        changed = []
        if title is not None:
            target.title = title.strip()
            changed.append("title")
        if desc is not None:
            target.desc = desc
            changed.append("desc")
        if status is not None:
            target.status = status
            changed.append("status")
        target.updated_at = self._now()

        self._save({"items": [asdict(i) for i in items]})
        if not changed:
            return f"⚠️ Поля не изменены #{tid}"
        return f"✅ Обновлено #{tid} ({', '.join(changed)}) -> [{target.status}] {target.title}"

    def _list(self, status_filter: Optional[str]) -> str:
        data = self._load()
        items = [TodoItem.from_dict(i) for i in data.get("items", [])]
        if status_filter and status_filter in STATUSES:
            items = [i for i in items if i.status == status_filter]

        groups = {"in_progress": [], "pending": [], "completed": []}
        for it in items:
            groups.setdefault(it.status, []).append(it)

        # ANSI colors similar to v2_todo_agent
        COLOR_PENDING = "\x1b[38;2;176;176;176m"
        COLOR_PROGRESS = "\x1b[38;2;120;200;255m"
        COLOR_DONE = "\x1b[38;2;34;139;34m"
        RESET = "\x1b[0m"

        def fmt(group_name: str, arr: List[TodoItem]) -> str:
            if not arr:
                return ""
            lines = [f"[{group_name.upper()}]"]
            for it in sorted(arr, key=lambda x: x.id):
                mark = "☒" if it.status == "completed" else "☐"
                color = COLOR_PENDING
                if it.status == "in_progress":
                    color = COLOR_PROGRESS
                elif it.status == "completed":
                    color = COLOR_DONE
                line_main = f"- {mark} #{it.id} {it.title} (updated {it.updated_at})"
                line_desc = f"    {it.desc}" if it.desc else None

                if it.status == "completed":
                    line_main = f"{color}\x1b[9m{line_main}{RESET}"
                    if line_desc:
                        line_desc = f"{color}\x1b[9m{line_desc}{RESET}"
                else:
                    line_main = f"{color}{line_main}{RESET}"
                    if line_desc:
                        line_desc = f"{color}{line_desc}{RESET}"

                lines.append(line_main)
                if line_desc:
                    lines.append(line_desc)
            return "\n".join(lines)

        parts = [fmt("in_progress", groups["in_progress"]), fmt("pending", groups["pending"]), fmt("completed", groups["completed"])]
        out = "\n\n".join([p for p in parts if p])
        return out or "Нет задач."
