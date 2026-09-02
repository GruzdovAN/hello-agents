"""Инструмент памяти

Реализация памяти для фреймворка HelloAgents.
Может быть добавлен как инструмент к любому агенту (Agent).
"""

from typing import Dict, Any, List
from datetime import datetime

from ..base import Tool, ToolParameter
from memory import MemoryManager, MemoryConfig

class MemoryTool(Tool):
    """Инструмент памяти

    Даёт агенту (Agent) возможности памяти:
    - добавление воспоминаний
    - поиск релевантных воспоминаний
    - сводка по памяти
    - управление жизненным циклом памяти
    """

    def __init__(
        self,
        user_id: str = "default_user",
        memory_config: MemoryConfig = None,
        memory_types: List[str] = None
    ):
        super().__init__(
            name="memory",
            description="Инструмент памяти — хранение и поиск истории диалогов, знаний и опыта"
        )

        self.memory_config = memory_config or MemoryConfig()
        self.memory_types = memory_types or ["working", "episodic", "semantic"]

        self.memory_manager = MemoryManager(
            config=self.memory_config,
            user_id=user_id,
            enable_working="working" in self.memory_types,
            enable_episodic="episodic" in self.memory_types,
            enable_semantic="semantic" in self.memory_types,
            enable_perceptual="perceptual" in self.memory_types
        )

        self.current_session_id = None
        self.conversation_count = 0

    def run(self, parameters: Dict[str, Any]) -> str:
        """Выполняет инструмент — интерфейс базового класса Tool

        Args:
            parameters: словарь параметров, обязателен action

        Returns:
            Строка с результатом выполнения
        """
        if not self.validate_parameters(parameters):
            return "❌ Ошибка проверки параметров: отсутствуют обязательные параметры"

        action = parameters.get("action")
        kwargs = {k: v for k, v in parameters.items() if k != "action"}

        return self.execute(action, **kwargs)

    def get_parameters(self) -> List[ToolParameter]:
        """Возвращает определения параметров инструмента"""
        return [
            ToolParameter(
                name="action",
                type="string",
                description=(
                    "Операция: "
                    "add(добавить), search(поиск), summary(сводка), stats(статистика), "
                    "update(обновить), remove(удалить), forget(забыть), consolidate(консолидация), clear_all(очистить всё)"
                ),
                required=True
            ),
            ToolParameter(name="content", type="string", description="Содержимое памяти (для add/update; для perceptual — описание)", required=False),
            ToolParameter(name="query", type="string", description="Поисковый запрос (для search)", required=False),
            ToolParameter(name="memory_type", type="string", description="Тип памяти: working, episodic, semantic, perceptual (по умолчанию: working)", required=False, default="working"),
            ToolParameter(name="importance", type="number", description="Важность 0.0–1.0 (для add/update)", required=False),
            ToolParameter(name="limit", type="integer", description="Лимит результатов поиска (по умолчанию: 5)", required=False, default=5),
            ToolParameter(name="memory_id", type="string", description="ID целевой записи (обязателен для update/remove)", required=False),
            ToolParameter(name="file_path", type="string", description="Perceptual: путь к локальному файлу (image/audio)", required=False),
            ToolParameter(name="modality", type="string", description="Perceptual: text/image/audio (если не указано — по расширению)", required=False),
            ToolParameter(name="strategy", type="string", description="Стратегия забывания: importance_based/time_based/capacity_based (для forget)", required=False, default="importance_based"),
            ToolParameter(name="threshold", type="number", description="Порог забывания (для forget, по умолчанию 0.1)", required=False, default=0.1),
            ToolParameter(name="max_age_days", type="integer", description="Макс. возраст в днях (для time_based forget)", required=False, default=30),
            ToolParameter(name="from_type", type="string", description="Исходный тип при consolidate (по умолчанию working)", required=False, default="working"),
            ToolParameter(name="to_type", type="string", description="Целевой тип при consolidate (по умолчанию episodic)", required=False, default="episodic"),
            ToolParameter(name="importance_threshold", type="number", description="Порог важности при consolidate (по умолчанию 0.7)", required=False, default=0.7),
        ]

    def execute(self, action: str, **kwargs) -> str:
        """Выполняет операцию с памятью

        Поддерживаемые операции:
        - add: добавить
        - search: поиск
        - summary: сводка
        - stats: статистика
        """

        if action == "add":
            return self._add_memory(**kwargs)
        elif action == "search":
            return self._search_memory(**kwargs)
        elif action == "summary":
            return self._get_summary(**kwargs)
        elif action == "stats":
            return self._get_stats()
        elif action == "update":
            return self._update_memory(**kwargs)
        elif action == "remove":
            return self._remove_memory(**kwargs)
        elif action == "forget":
            return self._forget(**kwargs)
        elif action == "consolidate":
            return self._consolidate(**kwargs)
        elif action == "clear_all":
            return self._clear_all()
        else:
            return f"Неподдерживаемая операция: {action}. Доступны: add, search, summary, stats, update, remove, forget, consolidate, clear_all"

    def _add_memory(
        self,
        content: str = "",
        memory_type: str = "working",
        importance: float = 0.5,
        file_path: str = None,
        modality: str = None,
        **metadata
    ) -> str:
        """Добавляет воспоминание"""
        try:
            if self.current_session_id is None:
                self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if memory_type == "perceptual" and file_path:
                inferred = modality or self._infer_modality(file_path)
                metadata.setdefault("modality", inferred)
                metadata.setdefault("raw_data", file_path)

            metadata.update({
                "session_id": self.current_session_id,
                "timestamp": datetime.now().isoformat()
            })

            memory_id = self.memory_manager.add_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                metadata=metadata,
                auto_classify=False
            )

            return f"✅ Воспоминание добавлено (ID: {memory_id[:8]}...)"

        except Exception as e:
            return f"❌ Не удалось добавить воспоминание: {str(e)}"

    def _infer_modality(self, path: str) -> str:
        """Определяет модальность по расширению (image/audio/text)"""
        try:
            ext = (path.rsplit('.', 1)[-1] or '').lower()
            if ext in {"png", "jpg", "jpeg", "bmp", "gif", "webp"}:
                return "image"
            if ext in {"mp3", "wav", "flac", "m4a", "ogg"}:
                return "audio"
            return "text"
        except Exception:
            return "text"

    def _search_memory(
        self,
        query: str,
        limit: int = 5,
        memory_types: List[str] = None,
        memory_type: str = None,
        min_importance: float = 0.1
    ) -> str:
        """Ищет воспоминания"""
        try:
            if memory_type and not memory_types:
                memory_types = [memory_type]

            results = self.memory_manager.retrieve_memories(
                query=query,
                limit=limit,
                memory_types=memory_types,
                min_importance=min_importance
            )

            if not results:
                return f"🔍 Не найдено воспоминаний, связанных с '{query}'"

            formatted_results = []
            formatted_results.append(f"🔍 Найдено {len(results)} релевантных воспоминаний:")

            for i, memory in enumerate(results, 1):
                memory_type_label = {
                    "working": "рабочая память",
                    "episodic": "эпизодическая память",
                    "semantic": "семантическая память",
                    "perceptual": "перцептивная память"
                }.get(memory.memory_type, memory.memory_type)

                content_preview = memory.content[:80] + "..." if len(memory.content) > 80 else memory.content
                formatted_results.append(
                    f"{i}. [{memory_type_label}] {content_preview} (важность: {memory.importance:.2f})"
                )

            return "\n".join(formatted_results)

        except Exception as e:
            return f"❌ Ошибка поиска воспоминаний: {str(e)}"

    def _get_summary(self, limit: int = 10) -> str:
        """Возвращает сводку по памяти"""
        try:
            stats = self.memory_manager.get_memory_stats()

            summary_parts = [
                f"📊 Сводка системы памяти",
                f"Всего воспоминаний: {stats['total_memories']}",
                f"Текущая сессия: {self.current_session_id or 'не начата'}",
                f"Раундов диалога: {self.conversation_count}"
            ]

            if stats['memories_by_type']:
                summary_parts.append("\n📋 Распределение по типам:")
                for memory_type, type_stats in stats['memories_by_type'].items():
                    count = type_stats.get('count', 0)
                    avg_importance = type_stats.get('avg_importance', 0)
                    type_label = {
                        "working": "рабочая память",
                        "episodic": "эпизодическая память",
                        "semantic": "семантическая память",
                        "perceptual": "перцептивная память"
                    }.get(memory_type, memory_type)

                    summary_parts.append(f"  • {type_label}: {count} (средняя важность: {avg_importance:.2f})")

            important_memories = self.memory_manager.retrieve_memories(
                query="",
                memory_types=None,
                limit=limit * 3,
                min_importance=0.5
            )

            if important_memories:
                seen_ids = set()
                seen_contents = set()
                unique_memories = []
                
                for memory in important_memories:
                    if memory.id in seen_ids:
                        continue
                    
                    content_key = memory.content.strip().lower()
                    if content_key in seen_contents:
                        continue
                    
                    seen_ids.add(memory.id)
                    seen_contents.add(content_key)
                    unique_memories.append(memory)
                
                unique_memories.sort(key=lambda x: x.importance, reverse=True)
                summary_parts.append(f"\n⭐ Важные воспоминания (топ {min(limit, len(unique_memories))}):")

                for i, memory in enumerate(unique_memories[:limit], 1):
                    content_preview = memory.content[:60] + "..." if len(memory.content) > 60 else memory.content
                    summary_parts.append(f"  {i}. {content_preview} (важность: {memory.importance:.2f})")

            return "\n".join(summary_parts)

        except Exception as e:
            return f"❌ Не удалось получить сводку: {str(e)}"

    def _get_stats(self) -> str:
        """Возвращает статистику"""
        try:
            stats = self.memory_manager.get_memory_stats()

            stats_info = [
                f"📈 Статистика системы памяти",
                f"Всего воспоминаний: {stats['total_memories']}",
                f"Включённые типы: {', '.join(stats['enabled_types'])}",
                f"ID сессии: {self.current_session_id or 'не начата'}",
                f"Раундов диалога: {self.conversation_count}"
            ]

            return "\n".join(stats_info)

        except Exception as e:
            return f"❌ Не удалось получить статистику: {str(e)}"

    def auto_record_conversation(self, user_input: str, agent_response: str):
        """Автоматически записывает диалог

        Может вызываться агентом для автоматической фиксации истории
        """
        self.conversation_count += 1
        self._add_memory(
            content=f"Пользователь: {user_input}",
            memory_type="working",
            importance=0.6,
            type="user_input",
            conversation_id=self.conversation_count
        )

        self._add_memory(
            content=f"Ассистент: {agent_response}",
            memory_type="working",
            importance=0.7,
            type="agent_response",
            conversation_id=self.conversation_count
        )

        # Важный диалог — в эпизодическую память (паттерны на китайском для входа пользователя)
        if len(agent_response) > 100 or "重要" in user_input or "记住" in user_input:
            interaction_content = f"Диалог — пользователь: {user_input}\nАссистент: {agent_response}"
            self._add_memory(
                content=interaction_content,
                memory_type="episodic",
                importance=0.8,
                type="interaction",
                conversation_id=self.conversation_count
            )

    def _update_memory(self, memory_id: str, content: str = None, importance: float = None, **metadata) -> str:
        """Обновляет воспоминание"""
        try:
            success = self.memory_manager.update_memory(
                memory_id=memory_id,
                content=content,
                importance=importance,
                metadata=metadata or None
            )
            return "✅ Воспоминание обновлено" if success else "⚠️ Воспоминание для обновления не найдено"
        except Exception as e:
            return f"❌ Не удалось обновить воспоминание: {str(e)}"

    def _remove_memory(self, memory_id: str) -> str:
        """Удаляет воспоминание"""
        try:
            success = self.memory_manager.remove_memory(memory_id)
            return "✅ Воспоминание удалено" if success else "⚠️ Воспоминание для удаления не найдено"
        except Exception as e:
            return f"❌ Не удалось удалить воспоминание: {str(e)}"

    def _forget(self, strategy: str = "importance_based", threshold: float = 0.1, max_age_days: int = 30) -> str:
        """Забывает воспоминания (несколько стратегий)"""
        try:
            count = self.memory_manager.forget_memories(
                strategy=strategy,
                threshold=threshold,
                max_age_days=max_age_days
            )
            return f"🧹 Забыто {count} воспоминаний (стратегия: {strategy})"
        except Exception as e:
            return f"❌ Ошибка забывания: {str(e)}"

    def _consolidate(self, from_type: str = "working", to_type: str = "episodic", importance_threshold: float = 0.7) -> str:
        """Консолидирует память (важные краткосрочные → долгосрочные)"""
        try:
            count = self.memory_manager.consolidate_memories(
                from_type=from_type,
                to_type=to_type,
                importance_threshold=importance_threshold,
            )
            return f"🔄 Консолидировано {count} воспоминаний в долгосрочную память ({from_type} → {to_type}, порог={importance_threshold})"
        except Exception as e:
            return f"❌ Ошибка консолидации: {str(e)}"

    def _clear_all(self) -> str:
        """Очищает всю память"""
        try:
            self.memory_manager.clear_all_memories()
            return "🧽 Вся память очищена"
        except Exception as e:
            return f"❌ Не удалось очистить память: {str(e)}"

    def add_knowledge(self, content: str, importance: float = 0.9):
        """Добавляет знание в семантическую память"""
        return self._add_memory(
            content=content,
            memory_type="semantic",
            importance=importance,
            knowledge_type="factual",
            source="manual"
        )

    def get_context_for_query(self, query: str, limit: int = 3) -> str:
        """Возвращает релевантный контекст для запроса"""
        results = self.memory_manager.retrieve_memories(
            query=query,
            limit=limit,
            min_importance=0.3
        )

        if not results:
            return ""

        context_parts = ["Релевантные воспоминания:"]
        for memory in results:
            context_parts.append(f"- {memory.content}")

        return "\n".join(context_parts)

    def clear_session(self):
        """Сбрасывает текущую сессию"""
        self.current_session_id = None
        self.conversation_count = 0

        wm = self.memory_manager.memory_types.get('working') if hasattr(self.memory_manager, 'memory_types') else None
        if wm:
            wm.clear()

    def consolidate_memories(self):
        """Консолидирует воспоминания"""
        return self.memory_manager.consolidate_memories()

    def forget_old_memories(self, max_age_days: int = 30):
        """Забывает старые воспоминания"""
        return self.memory_manager.forget_memories(
            strategy="time_based",
            max_age_days=max_age_days
        )
