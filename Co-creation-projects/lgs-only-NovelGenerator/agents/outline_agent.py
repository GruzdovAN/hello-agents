from dotenv import load_dotenv
load_dotenv()
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.tools import NoteTool
from prompt import OUTLINE_PROMPT
import re
import os


def extract_note_id(output: str) -> str:
    """Извлечь note_id из текста вывода NoteTool"""
    match = re.search(r"ID:\s*(note_[0-9_]+)", output)
    if not match:
        raise ValueError(f"Не удалось разобрать note_id из вывода:\n{output}")
    return match.group(1)


class OutlineAgent(SimpleAgent):
    """Агент генерации плана романа"""

    def __init__(self, name: str, llm: HelloAgentsLLM = HelloAgentsLLM(), **kwargs):
        self.workspace = kwargs.pop("workspace", "./outputs")
        super().__init__(name=name, llm=llm)
        self.outline_length = 3000
        self.note_tools = {}

    def _ensure_tool(self, novel_id: str, title: str = None):
        if not self.note_tools.get(novel_id):
            if not title:
                raise ValueError(f"Инструмент для novel_id {novel_id} не инициализирован и title не указан.")
            self.note_tools[novel_id] = NoteTool(workspace=os.path.join(self.workspace, f"{title}-{novel_id}", 'outline'))

    def run(self, user_input: str, **kwargs) -> str:
        """Запустить агента"""
        # novel_id отличает романы — названия могут повторяться
        novel_id = kwargs.pop("novel_id", None)
        assert novel_id, "Укажите ID романа"

        title = kwargs.pop("title", None)
        assert title, "Укажите название романа"

        self._ensure_tool(novel_id, title)

        # 1. Сформировать контекст
        target_length = kwargs.pop("target_length", self.outline_length)
        context = OUTLINE_PROMPT.format(
            user_input=user_input,
            title=title or "нет",
            tags=', '.join([str(tag) for tag in kwargs.values() if tag]) or 'нет',
            target_length=target_length
        )

        # 2. Вызвать LLM с контекстом
        messages = [{"role": "user", "content": context}]
        response = self.llm.invoke(messages)

        # 3. Сохранить план в заметку
        create_output = self.note_tools[novel_id].run({
            "action": "create",
            "title": f"{novel_id}-план",
            "content": response,
            "note_type": "outline",
            "tags": ["outline"]
        })
        # Получить ID заметки и связать с ID романа
        note_id = extract_note_id(create_output)

        return response, note_id

    def get_outline(self, novel_id: str, note_id: str, title: str = None) -> str:    
        """Получить план"""
        if title:
            self._ensure_tool(novel_id, title)
        return self.note_tools[novel_id].run({
            "action": "read",
            "note_id": note_id
        })
    
    def del_outline(self, novel_id: str, note_id: str, title: str = None):
        """Удалить план"""
        if title:
            self._ensure_tool(novel_id, title)
        self.note_tools[novel_id].run({
            "action": "delete",
            "note_id": note_id
        })

    def update_outline(self, novel_id: str, note_id: str, title: str = None, **kwargs):
        """Обновить план"""
        if title:
            self._ensure_tool(novel_id, title)
        self.note_tools[novel_id].run({
            "action": "update",
            "note_id": note_id,
            **kwargs
        })

def main():
    print("=" * 80)
    print("Пример Novel OutlineAgent")
    print("=" * 80 + "\n")

    llm = HelloAgentsLLM()
    novel_id = "demo_novel_001"
    title = "Город памяти"

    agent = OutlineAgent(
        name="Помощник по плану романа",
        llm=llm,
        workspace="./outputs",
    )

    user_idea = "Молодой человек, способный разговаривать с памятью города, обнаруживает в волне сноса историю, которую намеренно стёрли."

    # 1. Генерация плана
    print(f"\nГенерация плана...")
    response, note_id = agent.run(
        user_input=user_idea,
        novel_id=novel_id,
        title=title,
        style_tag="городское фэнтези",
        emotional_tone="взросление и примирение",
    )

    print("Сгенерированный план (фрагмент):")
    print(response[:200] + "...\n")
    print(f"План сохранён в NoteTool, note_id: {note_id}")

    # 2. Чтение плана
    print(f"\nЧтение плана (Note ID: {note_id})...")
    stored_outline = agent.get_outline(novel_id, note_id)
    print("План из NoteTool (фрагмент):")
    print(stored_outline[:200] + "...")

    # 3. Обновление плана
    print(f"\nОбновление плана...")
    new_content = stored_outline + "\n\n## Дополнительная канва\nСпособности героя усиливаются в дождь, он слышит «дыхание» зданий."
    agent.update_outline(novel_id, note_id, content=new_content, tags=["outline", "updated"])
    print("План обновлён.")

    # 4. Повторное чтение для проверки
    print(f"\nПроверка обновлённого содержимого...")
    updated_outline = agent.get_outline(novel_id, note_id)
    if "Способности героя усиливаются" in updated_outline:
        print("Проверка успешна: обновлённое содержимое найдено.")
    else:
        print("Проверка не пройдена: обновлённое содержимое не найдено.")


if __name__ == "__main__":
    main()
