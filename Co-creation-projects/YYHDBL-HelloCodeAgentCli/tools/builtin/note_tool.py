"""NoteTool — инструмент структурированных заметок

Даёт агенту (Agent) структурированные заметки:
- создание/чтение/обновление/удаление заметок
- организация по типам (статус задачи, выводы, блокеры, план действий и т.д.)
- постоянное хранение (Markdown с YAML front matter)
- поиск и фильтрация
- интеграция с MemoryTool (опционально)

Сценарии использования:
- отслеживание статуса долгих задач
- фиксация ключевых выводов и зависимостей
- задачи и план действий
- накопление знаний проекта

Пример формата заметки:
```markdown
---
id: note_20250118_120000_0
title: Прогресс проекта
type: task_state
tags: [milestone, phase1]
created_at: 2025-01-18T12:00:00
updated_at: 2025-01-18T12:00:00
---

# Прогресс проекта

Анализ требований завершён, далее: проектирование

## Ключевые вехи
- [x] Сбор требований
- [ ] Проектирование
```
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json
import os
import re

from ..base import Tool, ToolParameter


class NoteTool(Tool):
    """Инструмент заметок
    
    Структурированное управление заметками для агента (Agent):
    - task_state: статус задачи
    - conclusion: ключевой вывод
    - blocker: блокер
    - action: план действий
    - reference: справочные материалы
    - general: общая заметка
    
    Пример использования:
    ```python
    note_tool = NoteTool(workspace="./project_notes")
    
    # Создание заметки
    note_tool.run({
        "action": "create",
        "title": "Прогресс проекта",
        "content": "Анализ требований завершён, далее: проектирование",
        "note_type": "task_state",
        "tags": ["milestone", "phase1"]
    })
    
    # Чтение заметок
    notes = note_tool.run({"action": "list", "note_type": "task_state"})
    ```
    """
    
    def __init__(
        self,
        workspace: str = "./notes",
        auto_backup: bool = True,
        max_notes: int = 1000
    ):
        super().__init__(
            name="note",
            description="Инструмент заметок — создание, чтение, обновление и удаление структурированных заметок (статус, выводы, блокеры и др.)"
        )
        
        self.workspace = Path(workspace)
        self.auto_backup = auto_backup
        self.max_notes = max_notes
        
        # Создаём рабочую директорию при необходимости
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Файл индекса заметок
        self.index_file = self.workspace / "notes_index.json"
        self._load_index()
    
    def _load_index(self):
        """Загружает индекс заметок"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                self.notes_index = json.load(f)
        else:
            self.notes_index = {
                "notes": [],
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_notes": 0
                }
            }
            self._save_index()
    
    def _save_index(self):
        """Сохраняет индекс заметок"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.notes_index, f, ensure_ascii=False, indent=2)
    
    def _generate_note_id(self) -> str:
        """Генерирует ID заметки"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = len(self.notes_index["notes"])
        return f"note_{timestamp}_{count}"
    
    def _get_note_path(self, note_id: str) -> Path:
        """Возвращает путь к файлу заметки"""
        return self.workspace / f"{note_id}.md"
    
    def _note_to_markdown(self, note: Dict[str, Any]) -> str:
        """Преобразует объект заметки в Markdown"""
        # YAML front matter
        frontmatter = "---\n"
        frontmatter += f"id: {note['id']}\n"
        frontmatter += f"title: {note['title']}\n"
        frontmatter += f"type: {note['type']}\n"
        if note.get('tags'):
            tags_str = json.dumps(note['tags'])
            frontmatter += f"tags: {tags_str}\n"
        frontmatter += f"created_at: {note['created_at']}\n"
        frontmatter += f"updated_at: {note['updated_at']}\n"
        frontmatter += "---\n\n"
        
        # Содержимое Markdown
        content = f"# {note['title']}\n\n"
        content += note['content']
        
        return frontmatter + content
    
    def _markdown_to_note(self, markdown_text: str) -> Dict[str, Any]:
        """Разбирает Markdown в объект заметки"""
        # Извлечение YAML front matter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', markdown_text, re.DOTALL)
        
        if not frontmatter_match:
            raise ValueError("Неверный формат заметки: отсутствует YAML front matter")
        
        frontmatter_text = frontmatter_match.group(1)
        content_start = frontmatter_match.end()
        
        # Упрощённый разбор YAML
        note = {}
        for line in frontmatter_text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Обработка специальных полей
                if key == 'tags':
                    try:
                        note[key] = json.loads(value)
                    except:
                        note[key] = []
                else:
                    note[key] = value
        
        # Извлечение содержимого (без строки заголовка)
        markdown_content = markdown_text[content_start:].strip()
        # Удаление первой строки # заголовка
        lines = markdown_content.split('\n')
        if lines and lines[0].startswith('# '):
            markdown_content = '\n'.join(lines[1:]).strip()
        
        note['content'] = markdown_content
        
        # Добавление метаданных
        note['metadata'] = {
            'word_count': len(markdown_content),
            'status': 'active'
        }
        
        return note
    
    def run(self, parameters: Dict[str, Any]) -> str:
        """Выполняет инструмент"""
        if not self.validate_parameters(parameters):
            return "❌ Ошибка проверки параметров"
        
        action = parameters.get("action")
        
        if action == "create":
            return self._create_note(parameters)
        elif action == "read":
            return self._read_note(parameters)
        elif action == "update":
            return self._update_note(parameters)
        elif action == "delete":
            return self._delete_note(parameters)
        elif action == "list":
            return self._list_notes(parameters)
        elif action == "search":
            return self._search_notes(parameters)
        elif action == "summary":
            return self._get_summary()
        else:
            return f"❌ Неподдерживаемая операция: {action}"
    
    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "Тип операции: create(создать), read(читать), update(обновить), "
                    "delete(удалить), list(список), search(поиск), summary(сводка)"
                ),
                required=True
            ),
            ToolParameter(
                name="title",
                type="string",
                description="Заголовок заметки (обязателен для create/update)",
                required=False
            ),
            ToolParameter(
                name="content",
                type="string",
                description="Содержимое заметки (обязательно для create/update)",
                required=False
            ),
            ToolParameter(
                name="note_type",
                type="string",
                description=(
                    "Тип заметки: task_state(статус задачи), conclusion(вывод), "
                    "blocker(блокер), action(план действий), reference(справка), general(общая)"
                ),
                required=False,
                default="general"
            ),
            ToolParameter(
                name="tags",
                type="array",
                description="Список тегов (опционально)",
                required=False
            ),
            ToolParameter(
                name="note_id",
                type="string",
                description="ID заметки (обязателен для read/update/delete)",
                required=False
            ),
            ToolParameter(
                name="query",
                type="string",
                description="Ключевые слова поиска (обязательны для search)",
                required=False
            ),
            ToolParameter(
                name="limit",
                type="integer",
                description="Лимит результатов (по умолчанию 10)",
                required=False,
                default=10
            ),
        ]
    
    def _create_note(self, params: Dict[str, Any]) -> str:
        """Создаёт заметку"""
        title = params.get("title")
        content = params.get("content")
        note_type = params.get("note_type", "general")
        tags = params.get("tags", [])
        
        if not title or not content:
            return "❌ Для создания заметки нужны title и content"
        
        # Проверка лимита количества заметок
        if len(self.notes_index["notes"]) >= self.max_notes:
            return f"❌ Достигнут лимит заметок ({self.max_notes})"
        
        # Генерация ID заметки
        note_id = self._generate_note_id()
        
        # Создание объекта заметки
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "type": note_type,
            "tags": tags if isinstance(tags, list) else [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": {
                "word_count": len(content),
                "status": "active"
            }
        }
        
        # Сохранение файла заметки (Markdown)
        note_path = self._get_note_path(note_id)
        markdown_content = self._note_to_markdown(note)
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Обновление индекса
        self.notes_index["notes"].append({
            "id": note_id,
            "title": title,
            "type": note_type,
            "tags": tags if isinstance(tags, list) else [],
            "created_at": note["created_at"]
        })
        self.notes_index["metadata"]["total_notes"] = len(self.notes_index["notes"])
        self._save_index()
        
        return f"✅ Заметка создана\nID: {note_id}\nЗаголовок: {title}\nТип: {note_type}"
    
    def _read_note(self, params: Dict[str, Any]) -> str:
        """Читает заметку"""
        note_id = params.get("note_id")
        
        if not note_id:
            return "❌ Для чтения заметки нужен note_id"
        
        note_path = self._get_note_path(note_id)
        if not note_path.exists():
            return f"❌ Заметка не существует: {note_id}"
        
        with open(note_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        
        note = self._markdown_to_note(markdown_text)
        
        return self._format_note(note)
    
    def _update_note(self, params: Dict[str, Any]) -> str:
        """Обновляет заметку"""
        note_id = params.get("note_id")
        
        if not note_id:
            return "❌ Для обновления заметки нужен note_id"
        
        note_path = self._get_note_path(note_id)
        if not note_path.exists():
            return f"❌ Заметка не существует: {note_id}"
        
        # Чтение существующей заметки
        with open(note_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
        note = self._markdown_to_note(markdown_text)
        
        # Обновление полей
        if "title" in params:
            note["title"] = params["title"]
        if "content" in params:
            note["content"] = params["content"]
            note["metadata"]["word_count"] = len(params["content"])
        if "note_type" in params:
            note["type"] = params["note_type"]
        if "tags" in params:
            note["tags"] = params["tags"] if isinstance(params["tags"], list) else []
        
        note["updated_at"] = datetime.now().isoformat()
        
        # Сохранение обновления (Markdown)
        markdown_content = self._note_to_markdown(note)
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Обновление индекса
        for idx_note in self.notes_index["notes"]:
            if idx_note["id"] == note_id:
                idx_note["title"] = note["title"]
                idx_note["type"] = note["type"]
                idx_note["tags"] = note["tags"]
                break
        self._save_index()
        
        return f"✅ Заметка обновлена: {note_id}"
    
    def _delete_note(self, params: Dict[str, Any]) -> str:
        """Удаляет заметку"""
        note_id = params.get("note_id")
        
        if not note_id:
            return "❌ Для удаления заметки нужен note_id"
        
        note_path = self._get_note_path(note_id)
        if not note_path.exists():
            return f"❌ Заметка не существует: {note_id}"
        
        # Удаление файла
        note_path.unlink()
        
        # Обновление индекса
        self.notes_index["notes"] = [
            n for n in self.notes_index["notes"] if n["id"] != note_id
        ]
        self.notes_index["metadata"]["total_notes"] = len(self.notes_index["notes"])
        self._save_index()
        
        return f"✅ Заметка удалена: {note_id}"
    
    def _list_notes(self, params: Dict[str, Any]) -> str:
        """Выводит список заметок"""
        note_type = params.get("note_type")
        limit = params.get("limit", 10)
        
        # Фильтрация заметок
        filtered_notes = self.notes_index["notes"]
        if note_type:
            filtered_notes = [n for n in filtered_notes if n["type"] == note_type]
        
        # Ограничение количества
        filtered_notes = filtered_notes[:limit]
        
        if not filtered_notes:
            return "📝 Заметок пока нет"
        
        result = f"📝 Список заметок (всего {len(filtered_notes)})\n\n"
        for note in filtered_notes:
            result += f"• [{note['type']}] {note['title']}\n"
            result += f"  ID: {note['id']}\n"
            if note.get('tags'):
                result += f"  Теги: {', '.join(note['tags'])}\n"
            result += f"  Создано: {note['created_at']}\n\n"
        
        return result
    
    def _search_notes(self, params: Dict[str, Any]) -> str:
        """Ищет заметки"""
        query = params.get("query", "").lower()
        limit = params.get("limit", 10)
        
        if not query:
            return "❌ Для поиска нужен query"
        
        # Поиск совпадающих заметок
        matched_notes = []
        for idx_note in self.notes_index["notes"]:
            note_path = self._get_note_path(idx_note["id"])
            if note_path.exists():
                with open(note_path, 'r', encoding='utf-8') as f:
                    markdown_text = f.read()
                
                try:
                    note = self._markdown_to_note(markdown_text)
                except Exception as e:
                    print(f"⚠️ Не удалось разобрать заметку {idx_note['id']}: {e}")
                    continue
                
                # Проверка совпадения в заголовке, содержимом и тегах
                if (query in note["title"].lower() or
                    query in note["content"].lower() or
                    any(query in tag.lower() for tag in note.get("tags", []))):
                    matched_notes.append(note)
        
        # Ограничение количества
        matched_notes = matched_notes[:limit]
        
        if not matched_notes:
            return f"📝 Заметки по запросу '{query}' не найдены"
        
        result = f"🔍 Результаты поиска (всего {len(matched_notes)})\n\n"
        for note in matched_notes:
            result += self._format_note(note, compact=True) + "\n"
        
        return result
    
    def _get_summary(self) -> str:
        """Возвращает сводку по заметкам"""
        total = len(self.notes_index["notes"])
        
        # Статистика по типам
        type_counts = {}
        for note in self.notes_index["notes"]:
            note_type = note["type"]
            type_counts[note_type] = type_counts.get(note_type, 0) + 1
        
        result = f"📊 Сводка заметок\n\n"
        result += f"Всего заметок: {total}\n\n"
        result += "По типам:\n"
        for note_type, count in sorted(type_counts.items()):
            result += f"  • {note_type}: {count}\n"
        
        return result
    
    def _format_note(self, note: Dict[str, Any], compact: bool = False) -> str:
        """Форматирует вывод заметки"""
        if compact:
            return (
                f"[{note['type']}] {note['title']}\n"
                f"ID: {note['id']}\n"
                f"Содержимое: {note['content'][:100]}{'...' if len(note['content']) > 100 else ''}"
            )
        else:
            result = f"📝 Детали заметки\n\n"
            result += f"ID: {note['id']}\n"
            result += f"Заголовок: {note['title']}\n"
            result += f"Тип: {note['type']}\n"
            if note.get('tags'):
                result += f"Теги: {', '.join(note['tags'])}\n"
            result += f"Создано: {note['created_at']}\n"
            result += f"Обновлено: {note['updated_at']}\n"
            result += f"\nСодержимое:\n{note['content']}\n"
            return result

