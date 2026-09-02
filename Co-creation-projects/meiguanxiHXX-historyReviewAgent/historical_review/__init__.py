"""Глава 16: многоролевые исторические дебаты + лёгкое сетевое приложение + итоговый синтез."""

from .config import create_llm
from .debate_orchestrator import run_historical_debate

__all__ = ["create_llm", "run_historical_debate"]
