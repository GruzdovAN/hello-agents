"""
Пример интеграции NoteTool и ContextBuilder

Показывает, как интегрировать NoteTool с ContextBuilder для достижения:
1. Долгосрочное отслеживание проекта
2. Извлечение заметок и внедрение контекста
3. Последовательные рекомендации, основанные на исторических заметках.
"""
from dotenv import load_dotenv
load_dotenv()
from hello_agents import SimpleAgent, HelloAgentsLLM
from hello_agents.context import ContextBuilder, ContextConfig, ContextPacket
from hello_agents.tools import MemoryTool, RAGTool, NoteTool
from hello_agents.core.message import Message
from datetime import datetime
from typing import List, Dict


class ProjectAssistant(SimpleAgent):
    """Долгосрочный помощник по проектам, интегрирующий NoteTool и ContextBuilder"""

    def __init__(self, name: str, project_name: str, **kwargs):
        # Настроить LLM
        from hello_agents.core.llm import HelloAgentsLLM
        llm = HelloAgentsLLM()

        super().__init__(name=name, llm=llm, **kwargs)

        self.project_name = project_name

        # Инструмент инициализации
        # self.memory_tool = MemoryTool(user_id=project_name)
        # self.rag_tool = RAGTool(knowledge_base_path=f"./{project_name}_kb")
        self.note_tool = NoteTool(workspace=f"./{project_name}_notes")

        # Инициализировать построитель контекста
        self.context_builder = ContextBuilder(
            # memory_tool=self.memory_tool,
            # rag_tool=self.rag_tool,
            config=ContextConfig(max_tokens=4000)
        )

        self.conversation_history = []

    def run(self, user_input: str, note_as_action: bool = False) -> str:
        """Запустите помощник, автоматически интегрируйте заметки"""

        # 1. Получите связанные заметки из NoteTool.
        relevant_notes = self._retrieve_relevant_notes(user_input)

        # 2. Преобразование заметок в ContextPacket
        note_packets = self._notes_to_packets(relevant_notes)

        # 3. Создайте контекст для оптимизации
        optimized_context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self._build_system_instructions(),
            additional_packets=note_packets
        )

        # 4. Вызов LLM (передача массива сообщений)
        messages = [
            {"role": "system", "content": optimized_context},
            {"role": "user", "content": user_input}
        ]
        response = self.llm.invoke(messages)

        # 5. При желании запишите взаимодействие в виде заметки.
        if note_as_action:
            self._save_as_note(user_input, response)

        # 6. Обновить историю разговоров
        self._update_history(user_input, response)

        return response

    def _retrieve_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """Получить связанные заметки"""
        try:
            # Установите приоритет получения примечаний о блокировщиках и типах действий.
            blockers_raw = self.note_tool.run({
                "action": "list",
                "note_type": "blocker",
                "limit": 2
            })

            # Универсальный поиск
            search_results_raw = self.note_tool.run({
                "action": "search",
                "query": query,
                "limit": limit
            })

            blockers = self._ensure_list_of_dicts(blockers_raw)
            search_results = self._ensure_list_of_dicts(search_results_raw)

            # Объединить и удалить дубликаты
            all_notes = {}
            for note in blockers + search_results:
                if not isinstance(note, dict):
                    continue
                note_id = (
                    note.get("note_id")
                    or note.get("id")
                    or note.get("uuid")
                    or note.get("title")
                    or str(hash(str(note)))
                )
                all_notes[note_id] = note
            return list(all_notes.values())[:limit]

        except Exception as e:
            print(f"[ВНИМАНИЕ] Не удалось получить заметку: {e}")
            return []

    def _ensure_list_of_dicts(self, data) -> List[Dict]:
        """Нормализовать возврат NoteTool в список словарей"""
        import json
        if data is None:
            return []
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                return []
        if isinstance(data, dict):
            # Совместимо с {"items": [...]} или одной записью.
            if "items" in data and isinstance(data["items"], list):
                return [item for item in data["items"] if isinstance(item, dict)]
            return [data]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        return []

    def _notes_to_packets(self, notes: List[Dict]) -> List[ContextPacket]:
        """Преобразование заметок в контекстные пакеты"""
        packets = []

        for note in notes:
            title = note.get("title", "")
            body = note.get("content", "")
            content = f"[примечание:{title}]\n{body}"

            # Безопасный анализ временных меток
            ts = None
            for key in ("updated_at", "updatedAt", "time", "timestamp"):
                if key in note:
                    ts = note.get(key)
                    break
            parsed_ts = None
            if isinstance(ts, (int, float)):
                try:
                    parsed_ts = datetime.fromtimestamp(ts)
                except Exception:
                    parsed_ts = None
            elif isinstance(ts, str):
                try:
                    parsed_ts = datetime.fromisoformat(ts)
                except Exception:
                    parsed_ts = None
            if parsed_ts is None:
                parsed_ts = datetime.now()

            note_type = note.get("type") or note.get("note_type") or "note"
            note_id = (
                note.get("note_id")
                or note.get("id")
                or note.get("uuid")
                or title
                or str(hash(str(note)))
            )

            packets.append(ContextPacket(
                content=content,
                timestamp=parsed_ts,
                token_count=len(content) // 4,  # Простая оценка
                relevance_score=0.75,  # Заметки очень актуальны
                metadata={
                    "type": "note",
                    "note_type": note_type,
                    "note_id": note_id
                }
            ))

        return packets

    def _save_as_note(self, user_input: str, response: str):
        """Сохранить взаимодействие как заметку"""
        try:
            # Определите, какой тип заметок следует сохранять
            if "вопрос" in user_input or "блокировать" in user_input:
                note_type = "blocker"
            elif "план" in user_input or "Следующий шаг" in user_input:
                note_type = "action"
            else:
                note_type = "conclusion"

            self.note_tool.run({
                "action": "create",
                "title": f"{user_input[:30]}...",
                "content": f"## Вопрос\n{user_input}\n\n## Анализ\n{ответ}",
                "note_type": note_type,
                "tags": [self.project_name, "auto_generated"]
            })

        except Exception as e:
            print(f"[ВНИМАНИЕ] Не удалось сохранить заметку: {e}")

    def _build_system_instructions(self) -> str:
        """Инструкции по сборке системы"""
        return f"""Вы являетесь постоянным помощником в проекте {self.project_name}.

Ваши обязанности:
1. Предоставьте последовательные советы, основанные на исторических заметках.
2. Отслеживайте ход проекта и нерешенные проблемы.
3. При ответе цитируйте соответствующие исторические заметки.
4. Предоставьте конкретные и действенные предложения по следующим шагам.

Примечание:
- Приоритизировать проблемы, помеченные как блокирующие.
- Укажите в предложении источник поддержки (заметки, воспоминания или база знаний)
- Поддерживать осведомленность об общем ходе проекта."""

    def _update_history(self, user_input: str, response: str):
        """Обновить историю разговоров"""
        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # Ограничить длину истории
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]


def main():
    print("=" * 80)
    print("Пример интеграции NoteTool и ContextBuilder")
    print("=" * 80 + "\n")

    # Пример использования
    assistant = ProjectAssistant(
        name="Ассистент проекта",
        project_name="data_pipeline_refactoring"
    )

    # Первое взаимодействие: запись статуса проекта
    print("Первое взаимодействие: запись статуса проекта")
    response = assistant.run(
        "Мы завершили реконструкцию слоя модели данных, и уровень покрытия тестами достиг 85%. Следующим шагом является реконструкция уровня бизнес-логики.",
        note_as_action=True
    )
    print(f"Ассистент отвечает: {response}\n")

    # Второе взаимодействие: задать вопрос
    print("Второе взаимодействие: задать вопрос")
    response = assistant.run(
        "При рефакторинге уровня бизнес-логики я столкнулся с проблемой конфликта версий зависимостей. Как мне решить эту проблему?"
    )
    print(f"Ассистент отвечает: {response}\n")

    # Посмотреть сводку заметки
    print("Посмотреть сводку заметки:")
    summary = assistant.note_tool.run({"action": "summary"})
    import json
    print(json.dumps(summary, indent=2, ensure_ascii=False).replace("\\n", "\n"))

    print("\n" + "=" * 80)
    print("Демонстрация завершена!")
    print("=" * 80)


if __name__ == "__main__":
    main()
