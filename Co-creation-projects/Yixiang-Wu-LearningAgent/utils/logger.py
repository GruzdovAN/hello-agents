"""Конфигурация журнала"""

import logging
import sys
from pathlib import Path
from config import Config


def setup_logger(name: str = "learning_agent") -> logging.Logger:
    """
Настроить и вернуть логгер

    Args:
имя: имя регистратора

    Returns:
Настроенный регистратор
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))

# Избегайте повторного добавления обработчиков
    if logger.handlers:
        return logger

# обработчик консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

# обработчик файла
    log_dir = Path.home() / ".learningAgent" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setLevel(logging.DEBUG)

# формат
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
