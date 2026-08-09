"""
CodebaseMaintainer — помощник по обслуживанию кодовой базы

Полная реализация агента дальнего действия, интегрирующая:
1. ContextBuilder — управление контекстом
2. NoteTool — структурированные заметки
3. TerminalTool – мгновенный доступ к файлам
4. MemoryTool — диалоговая память

Ключевое улучшение: используйте агентный метод, чтобы позволить агенту решать, какие инструменты использовать.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from hello_agents import HelloAgentsLLM
from hello_agents.agents import FunctionCallAgent
from hello_agents.context import ContextBuilder, ContextConfig, ContextPacket
from hello_agents.tools import MemoryTool, NoteTool, TerminalTool
from hello_agents.tools.registry import ToolRegistry
from hello_agents.core.message import Message


class CodebaseMaintainer:
    """Помощник по обслуживанию кодовой базы — пример агента дальнего действия

    Интеграция ContextBuilder + NoteTool + TerminalTool + MemoryTool
    Внедрить межсессионное управление задачами по обслуживанию базы кода.
    
    Основные возможности:
    - Агент автономно использует инструменты для изучения кодовой базы.
    - Нет предопределенного рабочего процесса, полностью основанного на принятии решений агентом.
    - Межсессионная память и управление контекстом
    """

    def __init__(
        self,
        project_name: str,
        codebase_path: str,
        llm: Optional[HelloAgentsLLM] = None
    ):
        self.project_name = project_name
        self.codebase_path = codebase_path
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Инициализировать LLM
        self.llm = llm or HelloAgentsLLM()

        # Инструмент инициализации
        self.memory_tool = MemoryTool(
            user_id=project_name,
            memory_types=["working"]
        )
        self.note_tool = NoteTool(workspace=f"./{project_name}_notes")
        self.terminal_tool = TerminalTool(workspace=codebase_path, timeout=60)

        # Инициализировать построитель контекста
        self.context_builder = ContextBuilder(
            memory_tool=self.memory_tool,
            rag_tool=None,  # В этом случае не используется RAG
            config=ContextConfig(
                max_tokens=4000,
                reserve_ratio=0.15,
                min_relevance=0.2,
                enable_compression=True
            )
        )

        # Создайте реестр инструментов и зарегистрируйте инструменты.
        self.tool_registry = ToolRegistry()
        self.tool_registry.register_tool(self.terminal_tool)
        self.tool_registry.register_tool(self.note_tool)
        self.tool_registry.register_tool(self.memory_tool)

        # Создать агента
        self.agent = FunctionCallAgent(
            name="CodebaseMaintainer",
            llm=self.llm,
            system_prompt=self._build_base_system_prompt(),
            tool_registry=self.tool_registry,
            enable_tool_calling=True,
            max_tool_iterations=30
        )

        # История разговоров
        self.conversation_history: List[Message] = []

        # Статистика
        self.stats = {
            "session_start": datetime.now(),
            "commands_executed": 0,
            "notes_created": 0,
            "issues_found": 0,
            "tool_calls": 0
        }

        print(f"✅ Инициализирован помощник по обслуживанию базы кода: {project_name} (агентный режим)")
        print(f"📁 Рабочий каталог: {codebase_path}")
        print(f"🆔 Идентификатор сеанса: {self.session_id}")
        print(f"🔧 Доступные инструменты: {', '.join(self.tool_registry.list_tools())}")

    def run(self, user_input: str, mode: str = "auto") -> str:
        """Запустить Ассистент (Агентный режим)

        Аргументы:
            user_input: пользовательский ввод
            режим: подсказка рабочего режима (предоставление агенту рекомендаций по направлению)
                - «авто»: автоматически решить, использовать ли инструмент.
                - «исследовать»: агенту рекомендуется сосредоточиться на исследовании кода.
                - «анализировать»: агенту рекомендуется сосредоточиться на анализе проблемы.
                - «план»: агенту рекомендуется сосредоточиться на планировании задач.

        Возврат:
            ул: ответ ассистента
        """
        print(f"\n{'='*80}")
        print(f"👤 Пользователь: {user_input}")
        print(f"{'='*80}\n")

        # Шаг 1. Получите соответствующие заметки (предоставьте контекст агенту)
        relevant_notes = self._retrieve_relevant_notes(user_input)
        note_packets = self._notes_to_packets(relevant_notes)

        # Шаг 2. Создайте контекст оптимизации
        context = self.context_builder.build(
            user_query=user_input,
            conversation_history=self.conversation_history,
            system_instructions=self._build_system_instructions(mode),
            additional_packets=note_packets
        )

        # Шаг 3. Позвольте агенту самостоятельно принимать решения и использовать инструменты.
        print("🤖Агент думает и решает, какие инструменты использовать...\n")
        
        # Системное приглашение агента обновления (включая контекст)
        self.agent.system_prompt = context
        
        # Позвоните агенту (агент самостоятельно решит, использовать ли инструмент)
        response = self.agent.run(user_input)

        # Шаг 4: Использование статистических инструментов
        self._track_tool_usage()

        # Шаг 5. Обновите историю разговоров
        self._update_history(user_input, response)

        print(f"\n🤖 Ассистент: {response}\n")
        print(f"{'='*80}\n")

        return response

    def _build_base_system_prompt(self) -> str:
        """Советы по созданию базовой системы"""
        return f"""Вы помощник по обслуживанию кодовой базы проекта {self.project_name}.

Ваши основные компетенции:
1. Используйте TerminalTool для изучения базы кода.
   - Вы можете выполнить любую команду оболочки: ls, cat, grep, find, git и т. д.
   - Рабочий каталог: {self.codebase_path}
   
2. Используйте NoteTool для записи результатов и задач.
   - Создавайте заметки для записи важных выводов.
   - Типы заметок: блокировщик (проблема блокировки), действие (план действий), Task_state (статус задачи), заключение (заключение)
   
3. Используйте MemoryTool для хранения ключевой информации.
   - Помните важную контекстную информацию
   - Поддерживать преемственность между сеансами.

Идентификатор текущего сеанса: {self.session_id}

Важные принципы:
- Вам придется самостоятельно решать, какие инструменты использовать и какие команды выполнять.
- Изучая кодовую базу, начните с понимания общей структуры, прежде чем углубляться в детали.
- При обнаружении важной информации активно используйте NoteTool для ее записи.
- Держите свои ответы профессиональными и практичными
"""

    def _track_tool_usage(self):
        """Использование статистического инструмента"""
        # Статистика из истории выполнения агента
        if hasattr(self.agent, 'message_history'):
            for msg in self.agent.message_history[-10:]:  # Просмотреть только последние 10 позиций
                if msg.role == "tool":
                    self.stats["tool_calls"] += 1
                    # Статистика по названию инструмента
                    if "terminal" in str(msg.content).lower() or "command" in str(msg.content).lower():
                        self.stats["commands_executed"] += 1
                    elif "note" in str(msg.content).lower():
                        if "create" in str(msg.content).lower():
                            self.stats["notes_created"] += 1

    def _retrieve_relevant_notes(self, query: str, limit: int = 3) -> List[Dict]:
        """Получить связанные заметки"""
        try:
            # Установите приоритет блокировщика поиска
            blockers_raw = self.note_tool.run({
                "action": "list",
                "note_type": "blocker",
                "limit": 2
            })
            blockers = self._normalize_note_results(blockers_raw)

            # Поиск связанных заметок
            search_results_raw = self.note_tool.run({
                "action": "search",
                "query": query,
                "limit": limit
            })
            search_results = self._normalize_note_results(search_results_raw)

            # Объединить и удалить дубликаты
            all_notes = {}
            for note in blockers + search_results:
                if not isinstance(note, dict):
                    continue
                note_id = note.get('note_id') or note.get('id')
                if not note_id:
                    continue
                if note_id not in all_notes:
                    all_notes[note_id] = note

            return list(all_notes.values())[:limit]

        except Exception as e:
            print(f"[ВНИМАНИЕ] Не удалось получить заметку: {e}")
            return []

    def _normalize_note_results(self, result: Any) -> List[Dict]:
        """Преобразование возвращаемого значения инструмента заметок в список словарей заметок."""
        if not result:
            return []

        if isinstance(result, dict):
            return [result]

        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]

        if isinstance(result, str):
            text = result.strip()
            if not text:
                return []
            if text.startswith("{") or text.startswith("["):
                try:
                    parsed = json.loads(text)
                    return self._normalize_note_results(parsed)
                except Exception:
                    return []
            return []

        return []

    def _notes_to_packets(self, notes: List[Dict]) -> List[ContextPacket]:
        """Преобразование заметок в контекстные пакеты"""
        packets = []

        for note in notes:
            if not isinstance(note, dict):
                continue
            # Установите различные показатели релевантности в зависимости от типа заметки
            relevance_map = {
                "blocker": 0.9,
                "action": 0.8,
                "task_state": 0.75,
                "conclusion": 0.7
            }

            note_type = note.get('type', 'general')
            relevance = relevance_map.get(note_type, 0.6)

            content = f"[note:{note.get('title', 'Untitled')}]\nType: {note_type}\n\n{note.get('content', '')}"
            updated_at = note.get('updated_at')
            try:
                note_timestamp = datetime.fromisoformat(updated_at) if updated_at else datetime.now()
            except (ValueError, TypeError):
                note_timestamp = datetime.now()

            packets.append(ContextPacket(
                content=content,
                timestamp=note_timestamp,
                token_count=len(content) // 4,
                relevance_score=relevance,
                metadata={
                    "type": "note",
                    "note_type": note_type,
                    "note_id": note.get('note_id') or note.get('id')
                }
            ))

        return packets

    def _build_system_instructions(self, mode: str) -> str:
        """Инструкции по сборке системы (агентный режим)"""
        base_instructions = self._build_base_system_prompt()

        mode_hints = {
            "explore": """
В настоящее время пользователи сосредоточены на: Исследовании базы кода.

Предлагаемые стратегии:
- Рассмотрите возможность использования TerminalTool для понимания структуры кода (например, find, ls, Tree).
- Просмотр ключевых файлов (таких как README, основные модули)
- Записывать архитектурную информацию в примечания для последующего использования.
""",
            "analyze": """
В настоящее время пользователи сосредоточены на: Анализе качества кода.

Предлагаемые стратегии:
– Рассмотрите возможность использования grep для поиска потенциальных проблем (TODO, FIXME, BUG).
- Анализ сложности и структуры кода.
- Записывайте обнаруженные проблемы в виде блокировщиков или заметок о действиях.
""",
            "plan": """
В настоящее время пользователи сосредоточены на: Планировании миссий.

Предлагаемые стратегии:
- Просмотрите исторические заметки, чтобы понять текущий прогресс
- Разработать план действий на основе имеющейся информации.
- Создание или обновление заметок типа Task_state.
""",
            "auto": """
В настоящее время пользователи сосредоточены на: Свободном общении.

Предлагаемые стратегии:
- Гибкое принятие решений на основе потребностей пользователей
- Активно использовать инструменты для получения информации, когда это необходимо.
- Могу ответить прямо, когда это не нужно
"""
        }

        return base_instructions + "\n" + mode_hints.get(mode, mode_hints["auto"])


    def _update_history(self, user_input: str, response: str):
        """Обновить историю разговоров"""
        self.conversation_history.append(
            Message(content=user_input, role="user", timestamp=datetime.now())
        )
        self.conversation_history.append(
            Message(content=response, role="assistant", timestamp=datetime.now())
        )

        # Ограничить длину истории (сохранить последние 10 раундов разговоров)
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

    # === Удобный метод ===

    def explore(self, target: str = ".") -> str:
        """Изучите базу кода (агентский способ)
        
        Агент самостоятельно решает, какие команды использовать для исследования базы кода.
        """
        return self.run(f"Пожалуйста, изучите структуру кода {target}, чтобы понять, как организован проект.", mode="explore")

    def analyze(self, focus: str = "") -> str:
        """Анализ качества кода (агентный способ)
        
        Агент самостоятельно решит, как анализировать качество кода
        """
        query = f"Пожалуйста, проанализируйте качество кода" + (f", сосредоточься на {focus}" if focus else "")
        return self.run(query, mode="analyze")

    def plan_next_steps(self) -> str:
        """Планируйте следующую задачу (Агентный метод)
        
        Агент просмотрит исторические записи и спланирует следующие шаги.
        """
        return self.run("Планируйте следующие задачи на основе нашего предыдущего анализа и текущего прогресса.", mode="plan")

    def execute_command(self, command: str) -> str:
        """Выполнить команду терминала"""
        result = self.terminal_tool.run({"command": command})
        self.stats["commands_executed"] += 1
        return result

    def create_note(
        self,
        title: str,
        content: str,
        note_type: str = "general",
        tags: List[str] = None
    ) -> str:
        """Создать заметку"""
        result = self.note_tool.run({
            "action": "create",
            "title": title,
            "content": content,
            "note_type": note_type,
            "tags": tags or [self.project_name]
        })
        self.stats["notes_created"] += 1
        return result

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        duration = (datetime.now() - self.stats["session_start"]).total_seconds()

        # Получить сводку заметки
        try:
            note_summary = self.note_tool.run({"action": "summary"})
        except:
            note_summary = {}

        return {
            "session_info": {
                "session_id": self.session_id,
                "project": self.project_name,
                "duration_seconds": duration
            },
            "activity": {
                "commands_executed": self.stats["commands_executed"],
                "notes_created": self.stats["notes_created"],
                "issues_found": self.stats["issues_found"]
            },
            "notes": note_summary
        }

    def generate_report(self, save_to_file: bool = True) -> Dict[str, Any]:
        """Создать отчет о сеансе"""
        report = self.get_stats()

        if save_to_file:
            report_file = f"maintainer_report_{self.session_id}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            report["report_file"] = report_file
            print(f"📄 Отчет сохранен: {report_file}")

        return report


def main():
    """Основная функция — демонстрирует использование CodebaseMaintainer (агентская версия).
    
    В этой версии:
    - Агент самостоятельно решает, какие инструменты использовать
    - Нет предопределенных рабочих процессов
    - Агент гибко исследует кодовую базу в соответствии с потребностями
    """
    print("=" * 80)
    print("Демо-версия CodebaseMaintainer (агентская версия)")
    print("=" * 80 + "\n")

    # Помощник по инициализации
    maintainer = CodebaseMaintainer(
        project_name="my_flask_app",
        codebase_path="./my_flask_app",
        llm=HelloAgentsLLM()
    )

    # Исследуйте базу кода (агент решает, как исследовать)
    print("\n### Исследование базы кода (автономное исследование агента)###")
    response = maintainer.explore()

    # Анализировать качество кода (Агент самостоятельно определяет метод анализа)
    print("\n### Анализ качества кода (независимый от агента анализ)###")
    response = maintainer.analyze()

    # Планируйте следующий шаг (планы агента основаны на исторической информации)
    print("\n### Планирование следующей задачи (независимое планирование от агента)###")
    response = maintainer.plan_next_steps()

    # Создать отчет
    print("\n### Создать отчет о сеансе ###")
    report = maintainer.generate_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("Демонстрация завершена!")
    print("=" * 80)


if __name__ == "__main__":
    main()
