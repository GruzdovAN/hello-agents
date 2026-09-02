"""Шаг 8. Разработка контекста — сжатие диалогов, управление токенами, многораундовая согласованность"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class ContextManager:
"""Менеджер контекста разговора: сжимает историю, контролирует использование токенов, поддерживает непрерывность"""

    def __init__(self, max_tokens: int = 4000, summary_trigger: int = 3000):
        self.max_tokens = max_tokens        # 上下文最大 token 数
        self.summary_trigger = summary_trigger  # 触发压缩的阈值
self.turns: List[Dict] = [] # Повороты диалога
        self.summary: str = ""               # 压缩后的摘要
        self.total_turns = 0

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """简单 Token 估算：中文 ~1.5 字/token，英文 ~4 字/token"""
        chinese = sum(1 for c in text if '一' <= c <= '鿿')
        other = len(text) - chinese
        return int(chinese / 1.5 + other / 4)

    def add_turn(self, role: str, content: str):
"""Добавить раунд диалога"""
        self.total_turns += 1
        turn = {
            "id": self.total_turns,
            "role": role,
            "content": content,
            "tokens": self._estimate_tokens(content),
            "time": datetime.now().strftime("%H:%M:%S"),
        }
        self.turns.append(turn)

# Проверьте, требуется ли сжатие
        total = sum(t["tokens"] for t in self.turns)
        if total > self.summary_trigger:
            self._compress()

    def _compress(self):
"""Сжимайте ранние разговоры в сводки"""
        if len(self.turns) <= 4:
return # сохранить последние 4 раунда

# Берем самые ранние 60% раундов для сжатия
        split = max(1, int(len(self.turns) * 0.6))
        old_turns = self.turns[:split]
        recent = self.turns[split:]

# Создать сводку
        lines = []
        for t in old_turns:
            role_label = "用户" if t["role"] == "user" else "助手"
            snippet = t["content"][:200].replace("\n", " ")
            lines.append(f"[{role_label}]: {snippet}")

        new_summary = "对话历史摘要:\n" + "\n".join(lines)
        if self.summary:
            self.summary = self.summary[:500] + "\n...\n" + new_summary
        else:
            self.summary = new_summary

# Ограничить длину сводки
        while self._estimate_tokens(self.summary) > 1500:
            # Drop the earliest part of the summary string by splitting on lines
            lines = self.summary.split('\n')
            if len(lines) <= 2:
                # If there are only a couple lines left, we must chop strings carefully or discard
                self.summary = ""
                break
            else:
                self.summary = "对话历史摘要:\n" + "\n".join(lines[2:])

        self.turns = recent

    def get_context(self, system_prompt: str = "",
                    current_query: str = "") -> str:
"""Построить текущую контекстную строку"""
        parts = []

#Сжать сводку
        if self.summary:
            parts.append(f"## 历史对话摘要\n{self.summary[:2000]}")

# недавних разговоров
        if self.turns:
parts.append("## Последние разговоры")
for t in self.turns[-8:]: # Последние 8 раундов
                role_label = "用户" if t["role"] == "user" else "助手"
                content = t["content"]
                if self._estimate_tokens(content) > 500:
                    content = content[:500] + "..."
                parts.append(f"### {role_label}\n{content}")

        return "\n\n".join(parts)

    def get_stats(self) -> str:
"""Получить статистику использования контекста"""
        total = sum(t["tokens"] for t in self.turns)
        summary_tokens = self._estimate_tokens(self.summary) if self.summary else 0
return (f"Контекст: {len(self.turns)} активные ходы, "
                f"约 {total} tokens 活跃 + {summary_tokens} tokens 摘要, "
f"Всего разговоров: {self.total_turns}")

    def clear(self):
        self.turns = []
        self.summary = ""
        self.total_turns = 0


# ===== Контекстно-зависимый конструктор системных подсказок =====

def build_context_aware_prompt(
    ctx: ContextManager,
    base_prompt: str,
    user_query: str,
    memory_context: str = "",
    kb_context: str = "",
) -> str:
"""Создание полных контекстно-зависимых системных сообщений"""

    parts = [base_prompt]

#Контекст разговора
    context_str = ctx.get_context()
    if context_str:
parts.append(f"\n## Текущий контекст разговора\n{context_str}")

#Контекст памяти
    if memory_context:
        parts.append(f"\n## 用户记忆\n{memory_context}")

#Контекст базы знаний
    if kb_context:
        parts.append(f"\n## 相关知识\n{kb_context}")

    return "\n".join(parts)


# Глобальный синглтон
_ctx_instance: Optional[ContextManager] = None


def get_context() -> ContextManager:
    global _ctx_instance
    if _ctx_instance is None:
        _ctx_instance = ContextManager()
    return _ctx_instance


# ===== Вспомогательные функции =====

def context_stats(query: str = "") -> str:
    """查看当前上下文使用统计"""
    return get_context().get_stats()


def context_clear(query: str = "") -> str:
"""Очистить контекст (начать новый сеанс)"""
    get_context().clear()
return «Контекст очищен, начните новый сеанс».


def context_summarize(query: str = "") -> str:
"""Вручную активировать сжатие контекста"""
    ctx = get_context()
    ctx._compress()
    return ctx.get_stats()
