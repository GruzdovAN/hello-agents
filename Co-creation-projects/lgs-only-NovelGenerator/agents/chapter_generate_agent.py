from dotenv import load_dotenv
load_dotenv()
import re
import os
import json
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import NoteTool
from prompt import CHAPTER_PROMPT, CHAPTER_REVIEW_PROMPT, CHAPTER_START_PROMPT


def extract_note_id(output: str) -> str:
    """Извлечь note_id из текста вывода NoteTool"""
    match = re.search(r"ID:\s*(note_[0-9_]+)", output)
    if not match:
        raise ValueError(f"Не удалось разобрать note_id из вывода:\n{output}")
    return match.group(1)


class MemoryItem(BaseModel):
    """Структура элемента памяти"""
    node_id: str
    novel_id: str
    title: str
    content: str
    summary: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    next_chapter_prediction: str = ""


class ChapterGenerateAgent:
    """Агент с учётом контекста"""

    def __init__(self, name: str, llm: HelloAgentsLLM = HelloAgentsLLM(), max_steps: int = 5, chapter_length: int = 3000, **kwargs):

        self.chapter_length = chapter_length
        self.max_steps = max_steps

        self.num_chapter_memories = kwargs.get("num_chapter_memories", 5)
        self.workspace = kwargs.get("workspace", "./outputs")
        self.note_tools: Dict[str, NoteTool] = {}
        
        self.generate_agent = SimpleAgent(
            name="Помощник генерации глав",
            llm=llm,
            system_prompt='Ты профессиональный литературный ассистент, специализирующийся на структуре длинных романов и детализации текста.',
        )
        self.review_agent = SimpleAgent(
            name="Помощник проверки глав",
            llm=llm,
            system_prompt='Ты профессиональный редактор романов, проверяющий соответствие глав структуре и стилю произведения.',
        )

        # Хранилище памяти
        self.memories: Dict[str, List[MemoryItem]] = {}

    @staticmethod
    def extract_json_from_response(response: str) -> dict:
        """Извлечь и разобрать JSON из ответа модели"""
        clean_response = re.sub(r"```json\s*", "", response)
        clean_response = re.sub(r"```\s*$", "", clean_response)
        clean_response = clean_response.strip()
        
        try:
            return json.loads(clean_response)
        except json.JSONDecodeError as e:
            try:
                start = clean_response.find("{")
                end = clean_response.rfind("}")
                if start != -1 and end != -1:
                    json_str = clean_response[start : end + 1]
                    return json.loads(json_str)
            except Exception:
                pass
            raise ValueError(f"Не удалось разобрать JSON-ответ: {response}") from e

    def _ensure_tool(self, novel_id: str, novel_title: str = None):
        if not self.note_tools.get(novel_id):
            if not novel_title:
                raise ValueError(f"Инструмент для novel_id {novel_id} не инициализирован и novel_title не указан.")
            self.note_tools[novel_id] = NoteTool(workspace=os.path.join(self.workspace, f"{novel_title}-{novel_id}", 'chapters'))

    def get_content_from_note(self, content: str) -> str:
        try:
            frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if frontmatter_match:
                content = content[frontmatter_match.end():].strip()
            
            lines = content.split('\n')
            if lines and lines[0].startswith('# '):
                content = '\n'.join(lines[1:]).strip()
            
            return content
        except:
            return content

    def get_memories(self, novel_id: str):
        """Получить память последних глав"""
        if not hasattr(self.note_tools[novel_id], "notes_index"):
            self.note_tools[novel_id]._load_index()

        notes = self.note_tools[novel_id].notes_index.get("notes", [])

        chapter_notes = [
            n for n in notes
            if n.get("note_type") == "chapter" and str(novel_id) in n.get("title", "")
        ]

        recent_notes = chapter_notes[-self.num_chapter_memories:]

        for note in recent_notes:
            note_id = note.get("id")
            file_path = os.path.join(self.workspace, f"{note_id}.md")

            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                content = self.get_content_from_note(content)
                self.memories[novel_id].append(MemoryItem(
                    node_id=str(note_id),
                    title=note.get("title", "Неизвестная глава").strip(),
                    content=content,
                    novel_id=str(novel_id),
                    summary=note['tags'][0] if note.get("tags") and note['tags'] else '',
                    timestamp=datetime.fromisoformat(note.get("created_at", datetime.now().isoformat()))
                ))

    def run(self, user_input: str, **kwargs) -> str:
        """Запустить агента"""
        novel_id = kwargs.pop("novel_id", None)
        assert novel_id, "Укажите ID романа"

        novel_title = kwargs.pop("novel_title", None)
        assert novel_title, "Укажите название романа"

        self._ensure_tool(novel_id, novel_title)

        if not self.memories.get(novel_id):
            self.memories[novel_id] = []
            self.get_memories(novel_id)

        outline = self.get_outline(novel_id)
        prev_chapter = self.get_prev_chapter(novel_id)
        prev_summaries = self.get_prev_summaries(novel_id)
        chapter_length = kwargs.get("chapter_length", self.chapter_length)
        context = self.get_prompt(outline, prev_chapter, prev_summaries, user_input, novel_id, chapter_length=chapter_length)
        
        steps = 0
        while steps < self.max_steps:
            steps += 1

            response = self.generate_agent.run(context)
            try:
                response_data = self.extract_json_from_response(response)
                if 'title' not in response_data or 'content' not in response_data or 'next_chapter_prediction' not in response_data or 'summary' not in response_data:
                    raise ValueError("В JSON-ответе отсутствуют обязательные поля 'title', 'content', 'next_chapter_prediction' или 'summary'")
            except ValueError as e:
                print(f"Ошибка разбора JSON на шаге {steps}: {e}")
                continue
            
            review_context = CHAPTER_REVIEW_PROMPT.format(
                outline=outline,
                prev_chapter=prev_chapter,
                prev_summaries=prev_summaries,
                chapter_content=response_data.get('content', '')
            )
            review_response = self.review_agent.run(review_context)

            if "[ПРОЙДЕНО]" in review_response:
                break
            
            context = self.get_prompt(outline, prev_chapter, prev_summaries, user_input, novel_id, response_data, review_response, chapter_length=chapter_length)

        create_output = self.note_tools[novel_id].run({
            "action": "create",
            "title": f"{response_data.get('title', 'Неизвестная глава')}",
            "content": response_data.get('content', ''),
            "note_type": "chapter",
            "tags": [response_data.get('summary', '')]
        })

        note_id = extract_note_id(create_output)

        self.memories[novel_id].append(MemoryItem(
            node_id=note_id,
            title=response_data.get('title', 'Неизвестная глава'),
            content=response_data.get('content', ''),
            novel_id=novel_id,
            summary=response_data.get('summary', ''),
            timestamp=datetime.now().isoformat(),
            next_chapter_prediction=response_data.get('next_chapter_prediction', '')
        ))

        return response_data, note_id

    def get_prompt(self, outline: str, prev_chapter: str, prev_summaries: str, user_input: str, novel_id: str, response_data: dict = None, review_response: str = None, chapter_length: int = None) -> str:
        """Сформировать промпт для генерации главы"""
        if chapter_length is None:
            chapter_length = self.chapter_length
        is_first_chapter = (prev_chapter == 'нет' and prev_summaries == 'нет')

        if is_first_chapter:
            prompt_template = CHAPTER_START_PROMPT
            context = prompt_template.format(
                outline=outline,
                chapter_history='нет' if response_data is None else response_data.get('content', 'нет'),
                evaluation=review_response or "нет",
                user_input=user_input,
                chapter_length=chapter_length
            )
        else:
            prompt_template = CHAPTER_PROMPT
            context = prompt_template.format(
                outline=outline,
                prev_chapter=prev_chapter,
                prev_summaries=prev_summaries,
                chapter_history='нет' if response_data is None else response_data.get('content', 'нет'),
                evaluation=review_response or "нет",
                user_input=user_input or [self.memories[novel_id][-1].next_chapter_prediction if self.memories[novel_id] else "нет"][0],
                chapter_length=chapter_length
            )
        return context

    def get_outline(self, novel_id: str) -> str:    
        """Получить план"""
        dir_path = f"{os.path.dirname(self.note_tools[novel_id].workspace)}/outline"
        paths = os.listdir(dir_path)
        assert len(paths) >= 1, f"В каталоге {dir_path} должен быть файл плана"
        path = f"{dir_path}/{paths[0]}"
        with open(path, "r", encoding='utf-8') as f:
            outline = f.read()
        return self.get_content_from_note(outline)

    def get_prev_chapter(self, novel_id: str):
        """Получить содержимое предыдущей главы"""
        if self.memories.get(novel_id):
            last_mem = self.memories[novel_id][-1]
            return f"[{last_mem.metadata.get('title', 'неизвестно')}]\n...{last_mem.content[-800:]}"
        return "нет"

    def get_prev_summaries(self, novel_id: str):
        if self.memories.get(novel_id):
            return "\n".join([f"[{mem.title}]\n{mem.summary}" for mem in self.memories[novel_id][-self.num_chapter_memories:]])
        return "нет"
    
    def del_chapter(self, novel_id: str, note_id: str, novel_title: str = None):
        """Удалить главу"""
        if novel_title:
            self._ensure_tool(novel_id, novel_title)
        self.note_tools[novel_id].run({
            "action": "delete",
            "note_id": note_id
        })
        if self.memories.get(novel_id):
            self.memories[novel_id] = [mem for mem in self.memories[novel_id] if mem.node_id != note_id]

    def update_chapter(self, novel_id: str, note_id: str, novel_title: str = None, **kwargs):
        """Обновить главу"""
        if novel_title:
            self._ensure_tool(novel_id, novel_title)
        self.note_tools[novel_id].run({
            "action": "update",
            "note_id": note_id,
            **kwargs
        })
        if self.memories.get(novel_id):
            for mem in self.memories[novel_id]:
                if mem.node_id == note_id:
                    mem.title = kwargs.get('title', mem.title)
                    mem.content = kwargs.get('content', mem.content)
                    mem.summary = kwargs.get('summary', mem.summary)
                    mem.next_chapter_prediction = kwargs.get('next_chapter_prediction', mem.next_chapter_prediction)
                    mem.timestamp = datetime.now().isoformat()
                    break

def main():
    print("=" * 80)
    print("Пример Novel ChapterGenerateAgent")
    print("=" * 80 + "\n")

    llm = HelloAgentsLLM(provider='qwen')
    novel_id = "demo_novel_001"
    novel_title = "Город памяти"

    workspace_root = "./outputs"
    outline_dir = os.path.join(workspace_root, f"{novel_title}-{novel_id}", "outline")
    if not os.path.exists(outline_dir):
        os.makedirs(outline_dir)
    
    for f in os.listdir(outline_dir):
        try:
            os.remove(os.path.join(outline_dir, f))
        except Exception:
            pass
        
    dummy_outline_content = """---
tags: [outline]
created_at: 2025-01-27T10:00:00
---
# Город памяти — план

## Основной синопсис
Молодой человек, способный разговаривать с памятью города, обнаруживает в волне сноса историю, которую намеренно стёрли.

## Главные персонажи
- Ли Сюнь: герой, умеет «читать» память предметов.
- Дядя Чэнь: владелец антикварной лавки, кажется, знает тайну происхождения героя.

## Ход сюжета
1. Пробуждение способности, втягивание в конфликт сноса.
2. Находка загадочного предмета, открывающая прошлое.
3. ...
"""
    dummy_outline_path = os.path.join(outline_dir, f"{novel_id}-outline.md")
    with open(dummy_outline_path, "w", encoding="utf-8") as f:
        f.write(dummy_outline_content)

    print(f"Создан тестовый файл плана: {dummy_outline_path}")
    
    chapter_agent = ChapterGenerateAgent(
        name="Помощник по главам романа",
        llm=llm,
        workspace=workspace_root,
        chapter_length=1000
    )

    print(f"\nГенерация первой главы...")
    try:
        chapter_data_1, note_id_1 = chapter_agent.run(
            user_input="В первой главе через конкретную сцену сноса показать способность героя. Ли Сюнь пытается защитить старую лавку от сноса и случайно слышит «мысли» бульдозера.",
            novel_id=novel_id,
            novel_title=novel_title 
        )
        print(f"Первая глава готова, Note ID: {note_id_1}")
        print(f"Название: {chapter_data_1.get('title')}")
        print(f"Краткое содержание: {chapter_data_1.get('summary')}")
        print(f"Прогноз следующей главы: {chapter_data_1.get('next_chapter_prediction')}")

        print(f"\nГенерация второй главы...")
        chapter_data_2, note_id_2 = chapter_agent.run(
            user_input="Герой находит в руинах странный предмет, который вызывает воспоминания и словно зовёт его.",
            novel_id=novel_id,
            novel_title=novel_title
        )
        print(f"Вторая глава готова, Note ID: {note_id_2}")
        print(f"Название: {chapter_data_2.get('title')}")
        print(f"Краткое содержание: {chapter_data_2.get('summary')}")
        
    except Exception as e:
        print(f"Ошибка в процессе генерации: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
