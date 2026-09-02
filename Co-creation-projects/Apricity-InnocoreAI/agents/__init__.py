"""Модуль агента InnoCore AI"""

from .base import BaseAgent
from .hunter import HunterAgent
from .miner import MinerAgent
from .coach import CoachAgent
from .validator import ValidatorAgent
from .controller import AgentController

__all__ = [
    "BaseAgent",
    "HunterAgent",
    "MinerAgent", 
    "CoachAgent",
    "ValidatorAgent",
    "AgentController"
]