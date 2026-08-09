# -*- coding: utf-8 -*-
"""Структурированная выходная модель игры об убийстве оборотней «Троецарствие»"""
from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from agentscope.agent import AgentBase


class DiscussionModelCN(BaseModel):
    """Формат вывода обсуждения китайской версии"""
    
    reach_agreement: bool = Field(
        description="Достигнут ли консенсус?",
    )
    confidence_level: int = Field(
        description="Уровень уверенности в текущих рассуждениях (1-10)",
        ge=1, le=10
    )
    key_evidence: Optional[str] = Field(
        description="Основные доказательства, подтверждающие ваше мнение",
        default=None
    )


def get_vote_model_cn(agents: list[AgentBase]) -> type[BaseModel]:
    """Получите китайскую версию модели голосования"""
    
    class VoteModelCN(BaseModel):
        """Формат вывода голосования в китайской версии"""
        
        vote: Literal[tuple(_.name for _ in agents)] = Field(
            description="Имя игрока, за которого вы хотите проголосовать",
        )
        reason: str = Field(
            description="Причина голосования с кратким описанием того, почему был выбран этот человек.",
        )
        suspicion_level: int = Field(
            description="Подозрение на голосуемого (1-10)",
            ge=1, le=10
        )
    
    return VoteModelCN


class WitchActionModelCN(BaseModel):
    """Китайская версия модели Operation Witch"""
    
    use_antidote: bool = Field(
        description="Стоит ли использовать противоядие для спасения жизней",
        default=False
    )
    use_poison: bool = Field(
        description="Стоит ли использовать яд для убийства людей", 
        default=False
    )
    target_name: Optional[str] = Field(
        description="Имя целевого игрока (человека, которого нужно спасти или отравить)",
        default=None
    )
    action_reason: Optional[str] = Field(
        description="причина для действия",
        default=None
    )


def get_seer_model_cn(agents: list[AgentBase]) -> type[BaseModel]:
    """Получите китайскую версию модели Пророка."""
    
    class SeerModelCN(BaseModel):
        """Формат проверки пророка на китайском языке"""
        
        target: Literal[tuple(_.name for _ in agents)] = Field(
            description="Имя игрока, которое нужно проверить",
        )
        check_reason: str = Field(
            description="Причина проверки этого человека",
        )
        priority_level: int = Field(
            description="Проверить приоритет (1-10)",
            ge=1, le=10
        )
    
    return SeerModelCN


def get_hunter_model_cn(agents: list[AgentBase]) -> type[BaseModel]:
    """Приобретите китайскую версию модели охотника."""
    
    class HunterModelCN(BaseModel):
        """Китайская версия формата охотничьей стрельбы"""
        
        shoot: bool = Field(
            description="Использовать ли навыки стрельбы",
        )
        target: Optional[Literal[tuple(_.name for _ in agents)]] = Field(
            description="Имя игрока, сделавшего бросок",
            default=None
        )
        shoot_reason: Optional[str] = Field(
            description="Причина стрельбы",
            default=None
        )
    
    return HunterModelCN


class WerewolfKillModelCN(BaseModel):
    """Китайская версия модели убийства оборотня"""
    
    target: str = Field(
        description="Имя игрока, которого нужно убить",
    )
    kill_strategy: str = Field(
        description="Описание стратегии убийства",
    )
    team_coordination: Optional[str] = Field(
        description="План сотрудничества с товарищами по команде Wolf",
        default=None
    )


class GameAnalysisModelCN(BaseModel):
    """Модель анализа игры в китайской версии"""
    
    suspected_werewolves: List[str] = Field(
        description="Список подозреваемых оборотней",
        default_factory=list
    )
    trusted_players: List[str] = Field(
        description="Список доверенных игроков", 
        default_factory=list
    )
    key_clues: List[str] = Field(
        description="список ключевых подсказок",
        default_factory=list
    )
    next_strategy: str = Field(
        description="стратегия следующего шага",
    )