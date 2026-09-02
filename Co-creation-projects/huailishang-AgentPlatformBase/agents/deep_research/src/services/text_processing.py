"""Utility helpers for normalizing agent generated text."""

from __future__ import annotations

import re


def strip_tool_calls(text: str) -> str:
    """Удаляет маркеры вызова инструментов из текста."""

    if not text:
        return text

    pattern = re.compile(r"\[TOOL_CALL:[^\]]+\]")
    return pattern.sub("", text)

