"""ContextBuilder — реализация конвейера GSSC

Конвейер Gather-Select-Structure-Compress:
1. Gather: сбор из истории, памяти, RAG, результатов инструментов
2. Select: отбор по приоритету, релевантности, разнообразию
3. Structure: структурированный шаблон контекста
4. Compress: сжатие в рамках бюджета токенов
"""

from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING, Any as TypingAny
from dataclasses import dataclass, field
from datetime import datetime
import tiktoken
import math

from core.message import Message
from core.llm import HelloAgentsLLM

if TYPE_CHECKING:
    # Optional, only for type checking. Importing tools at runtime may pull in heavy optional deps.
    from tools import MemoryTool, RAGTool
else:
    MemoryTool = TypingAny  # type: ignore[assignment,misc]
    RAGTool = TypingAny  # type: ignore[assignment,misc]


@dataclass
class ContextPacket:
    """Пакет контекстной информации"""
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    relevance_score: float = 0.0  # 0.0-1.0
    
    def __post_init__(self):
        """Автоподсчёт токенов"""
        if self.token_count == 0:
            self.token_count = count_tokens(self.content)


@dataclass
class ContextConfig:
    """Конфигурация построения контекста"""
    max_tokens: int = 8000  # Общий бюджет
    reserve_ratio: float = 0.15  # Резерв на генерацию (10–20%)
    min_relevance: float = 0.3  # Мин. порог релевантности (только расширенный контекст)
    max_history_turns: int = 10  # Макс. раундов диалога в истории
    enable_mmr: bool = True  # MMR для разнообразия
    mmr_lambda: float = 0.7  # Параметр MMR (0=разнообразие, 1=релевантность)
    system_prompt_template: str = ""  # Шаблон системного промпта
    enable_compression: bool = True  # Включить сжатие
    include_output_format: bool = True  # Добавлять фиксированный формат ответа
    # lazy_fetch: memory/rag только по запросу через инструменты
    lazy_fetch: bool = True
    
    def get_available_tokens(self) -> int:
        """Доступный бюджет токенов (минус резерв)"""
        return int(self.max_tokens * (1 - self.reserve_ratio))


class ContextBuilder:
    """Построитель контекста — конвейер GSSC
    
    Идея (по аналогии с Claude Code):
    - Базовый контекст: системный промпт + история + сводка инструментов
    - Расширенный: memory/rag/notes через инструменты по запросу
    
    Пример использования:
    ```python
    # Рекомендуется: только базовый контекст
    builder = ContextBuilder(config=ContextConfig(lazy_fetch=True))
    context = builder.build_base(
        user_query="вопрос пользователя",
        conversation_history=[...],
        system_instructions="системные инструкции",
        tool_summaries=[...]  # Сводка последних вызовов инструментов
    )
    
    # Классический режим: сбор всего контекста
    builder = ContextBuilder(
        memory_tool=memory_tool,
        rag_tool=rag_tool,
        config=ContextConfig(lazy_fetch=False)
    )
    context = builder.build(user_query="вопрос пользователя", ...)
    ```
    """
    
    def __init__(
        self,
        memory_tool: Optional[MemoryTool] = None,
        rag_tool: Optional[RAGTool] = None,
        config: Optional[ContextConfig] = None,
        llm: Optional[HelloAgentsLLM] = None,
    ):
        self.memory_tool = memory_tool
        self.rag_tool = rag_tool
        self.config = config or ContextConfig()
        self.llm = llm
        self._encoding = tiktoken.get_encoding("cl100k_base")
    
    def build_base(
        self,
        user_query: str,
        conversation_history: Optional[List[Message]] = None,
        system_instructions: Optional[str] = None,
        tool_summaries: Optional[List[str]] = None,
        pending_state: Optional[str] = None,
    ) -> str:
        """Строит базовый контекст (рекомендуется)
        
        Только обязательный контекст, без активного memory/rag.
        Расширение — через context_fetch по запросу модели.
        
        Базовый контекст включает:
        - Системные инструкции и ограничения
        - Последние N раундов диалога
        - Сводка последних вызовов инструментов
        - Ожидающий подтверждения патч/план
        
        Args:
            user_query: Запрос пользователя
            conversation_history: История диалога
            system_instructions: Системные инструкции
            tool_summaries: Список сводок инструментов
            pending_state: Состояние, ожидающее подтверждения
            
        Returns:
            Структурированная строка контекста
        """
        packets = []
        
        # P0: системные инструкции (обязательно)
        if system_instructions:
            packets.append(ContextPacket(
                content=system_instructions,
                metadata={"type": "instructions"}
            ))
        
        # P1: история диалога (обязательно)
        if conversation_history:
            recent_history = conversation_history[-self.config.max_history_turns:]
            history_text = "\n".join([
                f"[{msg.role}] {msg.content}"
                for msg in recent_history
            ])
            packets.append(ContextPacket(
                content=history_text,
                metadata={"type": "history", "count": len(recent_history)}
            ))
        
        # P2: сводка инструментов (если есть)
        if tool_summaries:
            summary_text = "\n".join(tool_summaries[-3:])  # не более 3 последних
            packets.append(ContextPacket(
                content=f"[Сводка последних результатов инструментов]\n{summary_text}",
                metadata={"type": "tool_summary"}
            ))
        
        # P3: ожидающее состояние (если есть)
        if pending_state:
            packets.append(ContextPacket(
                content=f"[Ожидает подтверждения]\n{pending_state}",
                metadata={"type": "pending_state"}
            ))
        
        # Без фильтра релевантности — весь базовый контекст
        structured_context = self._structure_base(packets, user_query)
        
        # Сжатие при превышении бюджета
        return self._compress(structured_context)
    
    def _structure_base(
        self,
        packets: List[ContextPacket],
        user_query: str,
    ) -> str:
        """Структурирует базовый контекст"""
        sections = []
        
        # [Role & Policies]
        instructions = [p for p in packets if p.metadata.get("type") == "instructions"]
        if instructions:
            sections.append("[Role & Policies]\n" + "\n".join([p.content for p in instructions]))
        
        # [Context] — история диалога
        history = [p for p in packets if p.metadata.get("type") == "history"]
        if history:
            sections.append("[Context]\nНедавний диалог:\n" + "\n".join([p.content for p in history]))
        
        # [Evidence] — сводка инструментов
        tool_summary = [p for p in packets if p.metadata.get("type") == "tool_summary"]
        if tool_summary:
            sections.append("[Evidence]\n" + "\n".join([p.content for p in tool_summary]))
        
        # [State] — ожидающее состояние
        pending = [p for p in packets if p.metadata.get("type") == "pending_state"]
        if pending:
            sections.append("[State]\n" + "\n".join([p.content for p in pending]))
        
        # [Task]
        sections.append(f"[Task]\n{user_query}")
        
        return "\n\n".join(sections)
    
    def build(
        self,
        user_query: str,
        conversation_history: Optional[List[Message]] = None,
        system_instructions: Optional[str] = None,
        additional_packets: Optional[List[ContextPacket]] = None
    ) -> str:
        """Строит полный контекст
        
        Args:
            user_query: Запрос пользователя
            conversation_history: История диалога
            system_instructions: Системные инструкции
            additional_packets: Дополнительные пакеты контекста
            
        Returns:
            Структурированная строка контекста
        """
        # 1. Gather
        packets = self._gather(
            user_query=user_query,
            conversation_history=conversation_history or [],
            system_instructions=system_instructions,
            additional_packets=additional_packets or []
        )
        
        # 2. Select
        selected_packets = self._select(packets, user_query)
        
        # 3. Structure
        structured_context = self._structure(
            selected_packets=selected_packets,
            user_query=user_query,
            system_instructions=system_instructions
        )
        
        # 4. Compress
        final_context = self._compress(structured_context)
        
        return final_context
    
    def _gather(
        self,
        user_query: str,
        conversation_history: List[Message],
        system_instructions: Optional[str],
        additional_packets: List[ContextPacket]
    ) -> List[ContextPacket]:
        """Gather: сбор кандидатов
        
        При lazy_fetch=True — только базовый контекст.
        При lazy_fetch=False — активный memory/rag.
        """
        packets = []
        
        # P0: системные инструкции (всегда)
        if system_instructions:
            packets.append(ContextPacket(
                content=system_instructions,
                metadata={"type": "instructions"}
            ))
        
        # P1: история (всегда)
        if conversation_history:
            recent_history = conversation_history[-self.config.max_history_turns:]
            history_text = "\n".join([
                f"[{msg.role}] {msg.content}"
                for msg in recent_history
            ])
            packets.append(ContextPacket(
                content=history_text,
                metadata={"type": "history", "count": len(recent_history)}
            ))
        
        # Расширенный контекст только при lazy_fetch=False
        if not self.config.lazy_fetch:
            # P2: память — статус и выводы
            if self.memory_tool:
                try:
                    # Поиск статуса задачи
                    state_results = self.memory_tool.execute(
                        "search",
                        query="(статус задачи OR подцель OR вывод OR блокер)",
                        min_importance=0.7,
                        limit=5
                    )
                    if state_results and "не найдено" not in state_results:
                        packets.append(ContextPacket(
                            content=state_results,
                            metadata={"type": "task_state", "importance": "high"}
                        ))
                    
                    # Поиск по текущему запросу
                    related_results = self.memory_tool.execute(
                        "search",
                        query=user_query,
                        limit=5
                    )
                    if related_results and "не найдено" not in related_results:
                        packets.append(ContextPacket(
                            content=related_results,
                            metadata={"type": "related_memory"}
                        ))
                except Exception as e:
                    print(f"⚠️ Ошибка поиска в памяти: {e}")
            
            # P3: RAG — факты
            if self.rag_tool:
                try:
                    rag_results = self.rag_tool.run({
                        "action": "search",
                        "query": user_query,
                        "top_k": 5
                    })
                    if rag_results and "не найдено" not in rag_results and "Ошибка" not in rag_results:
                        packets.append(ContextPacket(
                            content=rag_results,
                            metadata={"type": "knowledge_base"}
                        ))
                except Exception as e:
                    print(f"⚠️ Ошибка RAG-поиска: {e}")
        
        # Дополнительные пакеты
        packets.extend(additional_packets)
        
        return packets
    
    def _select(
        self,
        packets: List[ContextPacket],
        user_query: str
    ) -> List[ContextPacket]:
        """Select: отбор по score и бюджету"""
        # 1) Релевантность (пересечение слов)
        query_tokens = set(user_query.lower().split())
        for packet in packets:
            content_tokens = set(packet.content.lower().split())
            if len(query_tokens) > 0:
                overlap = len(query_tokens & content_tokens)
                packet.relevance_score = overlap / len(query_tokens)
            else:
                packet.relevance_score = 0.0
        
        # 2) Свежесть (экспоненциальный спад)
        def recency_score(ts: datetime) -> float:
            delta = max((datetime.now() - ts).total_seconds(), 0)
            tau = 3600  # шкала 1 час, можно вынести в конфиг
            return math.exp(-delta / tau)
        
        # 3) Итоговый score: 0.7*релевантность + 0.3*свежесть
        scored_packets: List[Tuple[float, ContextPacket]] = []
        for p in packets:
            rec = recency_score(p.timestamp)
            score = 0.7 * p.relevance_score + 0.3 * rec
            scored_packets.append((score, p))
        
        # 4) instructions+history всегда включаются
        must_keep_types = {"instructions", "history"}
        must_keep_packets = [p for (_, p) in scored_packets if p.metadata.get("type") in must_keep_types]
        remaining = [p for (s, p) in sorted(scored_packets, key=lambda x: x[0], reverse=True)
                     if p.metadata.get("type") not in must_keep_types]
        
        # 5) min_relevance только для расширенного контекста
        filtered = [p for p in remaining if p.relevance_score >= self.config.min_relevance]
        
        # 6) Заполнение по бюджету
        available_tokens = self.config.get_available_tokens()
        selected: List[ContextPacket] = []
        used_tokens = 0
        
        # Сначала обязательный контекст
        for p in must_keep_packets:
            if used_tokens + p.token_count <= available_tokens:
                selected.append(p)
                used_tokens += p.token_count
        
        # Затем остальное по score
        for p in filtered:
            if used_tokens + p.token_count > available_tokens:
                continue
            selected.append(p)
            used_tokens += p.token_count
        
        return selected
    
    def _structure(
        self,
        selected_packets: List[ContextPacket],
        user_query: str,
        system_instructions: Optional[str]
    ) -> str:
        """Structure: шаблон контекста"""
        sections = []
        
        # [Role & Policies]
        p0_packets = [p for p in selected_packets if p.metadata.get("type") == "instructions"]
        if p0_packets:
            role_section = "[Role & Policies]\n"
            role_section += "\n".join([p.content for p in p0_packets])
            sections.append(role_section)
        
        # [Task]
        sections.append(f"[Task]\nВопрос пользователя: {user_query}")
        
        # [State]
        p1_packets = [p for p in selected_packets if p.metadata.get("type") == "task_state"]
        if p1_packets:
            state_section = "[State]\nКлючевой прогресс и открытые вопросы:\n"
            state_section += "\n".join([p.content for p in p1_packets])
            sections.append(state_section)
        
        # [Evidence]
        p2_packets = [
            p for p in selected_packets
            if p.metadata.get("type") in {"related_memory", "knowledge_base", "retrieval", "tool_result"}
        ]
        if p2_packets:
            evidence_section = "[Evidence]\nФакты и ссылки:\n"
            for p in p2_packets:
                evidence_section += f"\n{p.content}\n"
            sections.append(evidence_section)
        
        # [Recent Conversation]
        p3_packets = [p for p in selected_packets if p.metadata.get("type") == "history"]
        if p3_packets:
            context_section = "[Recent Conversation]\nНедавний диалог. При вопросах о прошлом — опирайтесь на этот раздел:\n"
            context_section += "\n".join([p.content for p in p3_packets])
            sections.append(context_section)
        
        # [Output] (опционально)
        if self.config.include_output_format:
            output_section = """[Output]
Формат ответа:
1. Вывод (кратко)
2. Обоснование (факты и источники)
3. Риски и допущения (если есть)
4. Следующие шаги (если уместно)"""
            sections.append(output_section)
        
        return "\n\n".join(sections)
    
    def _compress(self, context: str) -> str:
        """Compress: сжатие и нормализация"""
        if not self.config.enable_compression:
            return context
        
        current_tokens = count_tokens(context)
        available_tokens = self.config.get_available_tokens()
        
        if current_tokens <= available_tokens:
            return context

        # LLM-сжатие при наличии llm
        if self.llm is not None:
            try:
                target = available_tokens
                # Сохранять Role/Task, сжимать Evidence/Context
                sys = (
                    "Вы — компрессор контекста. Сожмите текст до целевого бюджета токенов, "
                    "сохраняя цель, ограничения, ключевые факты (пути, команды, ошибки, выводы)."
                    "Не выдумывайте. Сохраняйте заголовки секций, "
                    "сильно сокращая [Evidence]/[Context]. Ответ короткий."
                )
                user = f"Целевой бюджет (~): {target} tokens\n\nИсходный контекст:\n{context}"
                compressed = self.llm.invoke(
                    [
                        {"role": "system", "content": sys},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=min(1200, int(self.config.max_tokens * 0.4)),
                )
                if compressed and isinstance(compressed, str) and count_tokens(compressed) <= target:
                    return compressed
            except Exception:
                pass
        
        # Простое обрезание
        # В проде — LLM-сводка
        print(f"⚠️ Контекст превышает бюджет ({current_tokens} > {available_tokens}), обрезка")
        
        # Обрезка по абзацам
        lines = context.split("\n")
        compressed_lines = []
        used_tokens = 0
        
        for line in lines:
            line_tokens = count_tokens(line)
            if used_tokens + line_tokens > available_tokens:
                break
            compressed_lines.append(line)
            used_tokens += line_tokens
        
        return "\n".join(compressed_lines)


def count_tokens(text: str) -> int:
    """Подсчёт токенов (tiktoken)"""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception:
        # Запасной вариант: ~1 token на 4 символа
        return len(text) // 4

