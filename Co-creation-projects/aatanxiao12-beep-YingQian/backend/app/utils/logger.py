"""Глобальный журнал: единый формат и уровень для каждого модуля get_logger."""

from __future__ import annotations

import logging
import sys

from ..config import get_settings

_configured = False


def setup_logging() -> None:
"""Инициализируйте корневой журнал с помощью Settings.log_level (идемпотент)."""
    global _configured
    if _configured:
        return

    level = getattr(logging, get_settings().log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
    _configured = True


def get_logger(name: str = "app") -> logging.Logger:
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
