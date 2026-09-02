from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from agents.react_agent import ReActAgent
from core.config import Config
from core.llm import HelloAgentsLLM
from core.message import Message
from context.builder import ContextBuilder, ContextConfig, ContextPacket
from tools.registry import ToolRegistry
from tools.builtin.note_tool import NoteTool
from tools.builtin.terminal_tool import TerminalTool
from tools.builtin.plan_tool import PlanTool
from tools.builtin.todo_tool import TodoTool
from tools.builtin.context_fetch_tool import ContextFetchTool



@dataclass
class CodeAgentPaths:
    """Конфигурация путей CodeAgent"""
    repo_root: Path
    notes_dir: Path
    memory_dir: Path
    sessions_dir: Path
    logs_dir: Path

    @property
    def helloagents_dir(self) -> Path:
        """Путь к каталогу .helloagents"""
        return self.repo_root / ".helloagents"

    @property
    def prompts_dir(self) -> Path:
        """Путь к каталогу prompts"""
        return self.repo_root / "code_agent" / "prompts"


class CodeAgent:
    """
    CLI-агент в стиле Claude Code/Codex:
    - основной цикл на ReActAgent;
    - ContextBuilder собирает системный промпт + диалог + заметки + эпизодическую память;
    - планирование — опциональный инструмент `plan`, вызываемый моделью по необходимости.
    """

    def __init__(self, repo_root: Path, llm: Optional[HelloAgentsLLM] = None, config: Optional[Config] = None):
        """
        Инициализирует CodeAgent

        Args:
            repo_root: корень репозитория
            llm: экземпляр LLM
            config: конфигурация
        """
        repo_root = repo_root.resolve()
        self.config = config or Config.from_env()

        helloagents_dir = Path(self.config.helloagents_dir)
        state_root = helloagents_dir if helloagents_dir.is_absolute() else (repo_root / helloagents_dir)
        self.paths = CodeAgentPaths(
            repo_root=repo_root,
            notes_dir=state_root / "notes",
            memory_dir=state_root / "memory",
            sessions_dir=state_root / "sessions",
            logs_dir=state_root / "logs",
        )
        self.paths.helloagents_dir.mkdir(parents=True, exist_ok=True)
        self.paths.notes_dir.mkdir(parents=True, exist_ok=True)
        self.paths.sessions_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.llm = llm or HelloAgentsLLM()

        self.note_tool = NoteTool(workspace=str(self.paths.notes_dir))
        self.terminal_tool = TerminalTool(
            workspace=str(self.paths.repo_root),
            timeout=60,
            confirm_dangerous=True,
            default_shell_mode=True,
        )
        self.todo_tool = TodoTool(workspace=str(self.paths.helloagents_dir / "todos"))

        self.registry = ToolRegistry()
        self.registry.register_tool(self.terminal_tool)
        self.registry.register_tool(self.note_tool)
        self.registry.register_tool(PlanTool(self.llm, prompt_path=str(self.paths.prompts_dir / "plan.md")))
        self.registry.register_tool(self.todo_tool)
        
        self.context_fetch_tool = ContextFetchTool(
            workspace=str(self.paths.repo_root),
            note_tool=self.note_tool,
            memory_tool=None,
            max_tokens_per_source=800,
            context_lines=5,
        )
        self.registry.register_tool(self.context_fetch_tool)

        self.context_builder = ContextBuilder(
            memory_tool=None,
            rag_tool=None,
            config=ContextConfig(
                max_tokens=8000,
                reserve_ratio=0.15,
                max_history_turns=10,
                enable_compression=True,
                include_output_format=False,
                lazy_fetch=True,
            ),
            llm=self.llm,
        )

        react_prompt = (self.paths.prompts_dir / "react.md").read_text(encoding="utf-8")
        summarize_prompt = (self.paths.prompts_dir / "summarize_observation.md").read_text(encoding="utf-8")

        def _summarize_observation(tool_name: str, tool_input: str, observation: str) -> str:
            """Сжимает вывод инструмента через LLM (чтобы не класть огромный raw в промпт)"""
            truncated = observation
            if len(truncated) > 8000:
                truncated = truncated[:8000] + "\n...truncated...\n"
            user_msg = (
                f"Tool: {tool_name}\n"
                f"Input: {tool_input}\n\n"
                f"Output:\n{truncated}"
            )
            return self.llm.invoke(
                [
                    {"role": "system", "content": summarize_prompt},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=400,
            ) or ""

        self.react = ReActAgent(
            name="code_agent",
            llm=self.llm,
            tool_registry=self.registry,
            max_steps=20,
            custom_prompt=react_prompt,
            observation_summarizer=_summarize_observation,
            summarize_threshold_chars=1800,
        )

        base_system = (self.paths.prompts_dir / "system.md").read_text(encoding="utf-8")
        self.tools_reference_path = self.paths.prompts_dir / "tools.md"
        self.system_prompt = base_system
        self.history: List[Message] = []
        self.recent_tool_packets: List[ContextPacket] = []
        self.last_direct_reply: bool = False

    def _is_chitchat(self, text: str) -> bool:
        """Определяет светскую беседу, чтобы не вызывать инструменты зря"""
        t = (text or "").strip().lower()
        return t in {"hi", "hello", "hey", "yo", "你好", "您好", "在吗", "嗨", "哈喽"}

    def _is_history_query(self, text: str) -> bool:
        """Запрос «что мы говорили»"""
        t = (text or "").strip().lower()
        patterns = [
            "说了什么",
            "刚才说了什么",
            "之前说了什么",
            "what did i say",
            "what did we say",
            "recap",
            "summary of conversation",
        ]
        return any(p in t for p in patterns)

    def _reply_with_recent_history(self, limit: int = 6) -> str:
        """Краткий обзор недавнего диалога"""
        items = [m for m in self.history if m.role in {"user", "assistant"}][-limit * 2 :]
        if not items:
            return "Пока нет истории диалога для обзора."
        lines = []
        for m in items:
            role = "вы" if m.role == "user" else "ассистент"
            lines.append(f"- {role}: {m.content}")
        return "Недавний диалог:\n" + "\n".join(lines)

    def _note_packets(self, query: str) -> List[ContextPacket]:
        """Ищет заметки и упаковывает в ContextPacket"""
        packets: List[ContextPacket] = []
        if self._is_chitchat(query):
            return packets
        try:
            blockers = self.note_tool.run({"action": "list", "note_type": "blocker", "limit": 2})
            if blockers and isinstance(blockers, str) and "пока нет" not in blockers:
                packets.append(ContextPacket(content=f"[Notes:blocker]\n{blockers}", metadata={"source": "note"}))
            hits = self.note_tool.run({"action": "search", "query": query, "limit": 3})
            if hits and isinstance(hits, str) and "не найдено" not in hits:
                packets.append(ContextPacket(content=f"[Notes:search]\n{hits}", metadata={"source": "note"}))
        except Exception:
            pass
        return packets

    def _memory_packets(self, query: str) -> List[ContextPacket]:
        """Ищет память и упаковывает в ContextPacket"""
        packets: List[ContextPacket] = []
        if self._is_chitchat(query):
            return packets
        try:
            hits = self.memory_tool.run(
                {"action": "search", "query": query, "memory_types": self.memory_tool.memory_types, "limit": 5, "min_importance": 0.0}
            )
            if hits and isinstance(hits, str) and "не найдено" not in hits:
                packets.append(ContextPacket(content=f"[Memory]\n{hits}", metadata={"source": "memory"}))
        except Exception:
            pass
        return packets

    def _persist_session(self) -> None:
        """Сохраняет сессию в JSON"""
        p = self.paths.sessions_dir / f"{self.session_id}.json"
        data = {
            "session_id": self.session_id,
            "updated_at": datetime.now().isoformat(),
            "history": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()} for m in self.history[-50:]
            ],
        }
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def run_turn(self, user_input: str) -> str:
        """
        Один раунд диалога:
        1. сбор контекста (заметки, память, вывод инструментов)
        2. сборка промпта
        3. цикл ReAct
        4. обновление истории и сохранение
        """
        if not user_input.strip():
            return "Укажите конкретную инструкцию или вопрос."

        if self._is_chitchat(user_input):
            self.last_direct_reply = True
            reply = "Привет! Я Code Agent: могу исследовать репозиторий, генерировать патчи и применять их после подтверждения. Чем помочь? (например: структура проекта / поиск класса / исправление ошибки)"
            self.history.append(Message(content=user_input, role="user", timestamp=datetime.now()))
            self.history.append(Message(content=reply, role="assistant", timestamp=datetime.now()))
            if len(self.history) > 50:
                self.history = self.history[-50:]
            self._persist_session()
            return reply
        self.last_direct_reply = False

        if self._is_history_query(user_input):
            self.last_direct_reply = True
            reply = self._reply_with_recent_history(limit=6)
            self.history.append(Message(content=user_input, role="user", timestamp=datetime.now()))
            self.history.append(Message(content=reply, role="assistant", timestamp=datetime.now()))
            if len(self.history) > 50:
                self.history = self.history[-50:]
            self._persist_session()
            return reply

        multistep_hint = ""
        multi_patterns = ["分步", "步骤", "三步", "计划", "改造", "完成后", "多步", "多步骤"]
        if any(p in user_input for p in multi_patterns):
            multistep_hint = "Подсказка: задача многошаговая — сначала todo add/update, в конце todo list."

        tool_summaries = []
        for packet in self.recent_tool_packets[-3:]:
            tool_summaries.append(packet.content)
        
        context_text = self.context_builder.build_base(
            user_query=user_input,
            conversation_history=self.history,
            system_instructions=self.system_prompt + ("\n" + multistep_hint if multistep_hint else ""),
            tool_summaries=tool_summaries if tool_summaries else None,
        )
        
        response = self.react.run(context_text, max_tokens=8000)

        try:
            tool_summaries: List[str] = []
            todo_used = False
            todo_listed = False
            for item in getattr(self.react, "last_trace", [])[-6:]:
                summary = item.get("observation_summary")
                tname = item.get("tool_name")
                if tname == "todo":
                    todo_used = True
                    if "list" in str(item.get("tool_input", "")):
                        todo_listed = True
                if summary:
                    tool_summaries.append(
                        f"[{item.get('tool_name')}] {item.get('tool_input')}\n{summary}"
                    )
            if tool_summaries:
                self.recent_tool_packets.append(
                    ContextPacket(
                        content="[Tool Evidence]\n" + "\n\n".join(tool_summaries),
                        metadata={"type": "tool_result", "source": "react"},
                    )
                )
                if len(self.recent_tool_packets) > 8:
                    self.recent_tool_packets = self.recent_tool_packets[-8:]
        except Exception:
            pass

        self.history.append(Message(content=user_input, role="user", timestamp=datetime.now()))
        self.history.append(Message(content=response, role="assistant", timestamp=datetime.now()))
        if len(self.history) > 50:
            self.history = self.history[-50:]
        self._persist_session()
        try:
            if todo_used and not todo_listed:
                todo_snapshot = self.registry.execute_tool("todo", {"action": "list"})
                response = f"{response}\n\nTodo board:\n{todo_snapshot}"
        except Exception:
            pass
        return response
