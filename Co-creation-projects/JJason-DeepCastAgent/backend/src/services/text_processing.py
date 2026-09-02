"""Практический помощник для стандартизации текста, генерируемого агентом."""

from __future__ import annotations


def strip_tool_calls(text: str) -> str:
"""Удалить маркеры вызова инструментов из текста.

Поддерживаются вложенные квадратные скобки, например:
    [TOOL_CALL:note:{"tags":["deep_research","task_1"]}]
    """
    if not text:
        return text

# Найдите [TOOL_CALL: начальную метку, а затем вручную сопоставьте соответствующее замыкание]
    result: list[str] = []
    i = 0
    marker = "[TOOL_CALL:"
    while i < len(text):
        pos = text.find(marker, i)
        if pos == -1:
            result.append(text[i:])
            break
        result.append(text[i:pos])
# Сканируйте назад от исходного положения маркера, чтобы отслеживать глубину кронштейна.
        depth = 0
        j = pos
        while j < len(text):
            if text[j] == "[":
                depth += 1
            elif text[j] == "]":
                depth -= 1
                if depth == 0:
                    break
            j += 1
i = j + 1 # пропускать закрытые]
    return "".join(result)

