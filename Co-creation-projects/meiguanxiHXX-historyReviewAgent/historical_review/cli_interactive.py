"""CLI: тема, сетевое приложение, подтверждение перед запуском."""

from __future__ import annotations

import sys


def prompt_yes_no(question: str, *, default: bool = True) -> bool:
    """
    Спрашивает Y/n или y/N; Enter принимает значение default.
    Вне TTY сразу возвращает default, чтобы не зависнуть в pipe.
    """
    if not sys.stdin.isatty():
        return default

    hint = " [Y/n] " if default else " [y/N] "
    try:
        raw = input(question + hint).strip().lower()
    except EOFError:
        return default

    if raw == "":
        return default
    if raw in ("y", "yes", "да", "д", "1"):
        return True
    if raw in ("n", "no", "нет", "н", "0"):
        return False
    return default


def prompt_topic(default_topic: str) -> str:
    if not sys.stdin.isatty():
        return default_topic

    try:
        raw = input(
            "Введите историческую тему (Enter — использовать пример):\n> ",
        ).strip()
    except EOFError:
        return default_topic

    return raw if raw else default_topic
