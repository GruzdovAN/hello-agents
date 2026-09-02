"""Утилиты логирования"""

import logging
import sys
from typing import Optional

def setup_logger(
    name: str = "hello_agents",
    level: str = "INFO",
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Настраивает логгер
    
    Args:
        name: Имя логгера
        level: Уровень логирования
        format_string: Формат сообщений
        
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            format_string or 
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_logger(name: str = "hello_agents") -> logging.Logger:
    """Возвращает логгер"""
    return logging.getLogger(name)
