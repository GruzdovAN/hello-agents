# -*- coding: utf-8 -*-
"""Функция инструмента игры «Убийство оборотня Троецарствия»"""
import asyncio
import random
from typing import List, Dict, Optional, Any
from collections import Counter

from agentscope.agent import AgentBase
from agentscope.message import Msg

# игровые константы
MAX_GAME_ROUND = 10
MAX_DISCUSSION_ROUND = 3
CHINESE_NAMES = [
    "Лю Бэй", "Гуань Юй", "Чжан Фэй", "Чжугэ Лян", "Чжао Юн",
    "Цао Цао", "Сыма Йи", "Дяньвэй", "Сюй Чу", "Сяхоу Дунь", 
    "Сунь Цюань", "Чжоу Ю", "Лу Синь", "Ган Нин", "Тайши Ци",
    "Лу Бу", "Дяо Чан", "Дун Чжо", "Юань Шао", "Юань Шу"
]


def get_chinese_name(character: str = None) -> str:
    """Получить имя китайского персонажа"""
    if character and character in CHINESE_NAMES:
        return character
    return random.choice(CHINESE_NAMES)


def format_player_list(players: List[AgentBase], show_roles: bool = False) -> str:
    """Форматировать список игроков для отображения на китайском языке"""
    if not players:
        return "Нет игроков"
    
    if show_roles:
        return "、".join([f"{p.name}({getattr(p, 'роль', 'неизвестно')})" for p in players])
    else:
        return "、".join([p.name for p in players])


def majority_vote_cn(votes: Dict[str, str]) -> tuple[str, int]:
    """Статистика большинства голосов в китайской версии"""
    if not votes:
        return "беспилотный", 0
    
    vote_counts = Counter(votes.values())
    most_voted = vote_counts.most_common(1)[0]
    
    return most_voted[0], most_voted[1]


def check_winning_cn(alive_players: List[AgentBase], roles: Dict[str, str]) -> Optional[str]:
    """Проверьте условия победы китайской версии игры"""
    alive_roles = [roles.get(p.name, "сельский житель") for p in alive_players]
    werewolf_count = alive_roles.count("оборотень")
    villager_count = len(alive_roles) - werewolf_count
    
    if werewolf_count == 0:
        return "Хорошие парни побеждают! Все оборотни уничтожены!"
    elif werewolf_count >= villager_count:
        return "Лагерь оборотней побеждает! Оборотни достигли или превзошли численностью хороших парней!"
    
    return None


def analyze_speech_pattern(speech: str) -> Dict[str, Any]:
    """Анализ речевых шаблонов (оптимизировано для китайского языка)"""
    analysis = {
        "word_count": len(speech),
        "confidence_keywords": 0,
        "doubt_keywords": 0,
        "emotion_score": 0
    }
    
    # Анализ китайских ключевых слов
    confidence_words = ["Конечно", "подтверждать", "должен", "абсолютный", "должен", "очевидно"]
    doubt_words = ["возможный", "Может быть", "возможно", "Подозревать", "неопределенный", "Чувствовать"]
    
    for word in confidence_words:
        analysis["confidence_keywords"] += speech.count(word)
    
    for word in doubt_words:
        analysis["doubt_keywords"] += speech.count(word)
    
    # Простой анализ настроений
    positive_words = ["хороший", "Большой", "хвалить", "поддерживать", "соглашаться"]
    negative_words = ["плохой", "Разница", "быть против", "нет", "ошибка"]
    
    for word in positive_words:
        analysis["emotion_score"] += speech.count(word)
    
    for word in negative_words:
        analysis["emotion_score"] -= speech.count(word)
    
    return analysis


class GameModerator(AgentBase):
    """Китайская версия игрового хоста"""
    
    def __init__(self) -> None:
        super().__init__()
        self.name = "ведущий игры"
        self.game_log: List[str] = []
    
    async def announce(self, content: str) -> Msg:
        """Делайте анонсы игр"""
        msg = Msg(
            name=self.name,
            content=f"📢 {content}",
            role="system"
        )
        self.game_log.append(content)
        await self.print(msg)
        return msg
    
    async def night_announcement(self, round_num: int) -> Msg:
        """Объявление ночной фазы"""
        content = f"🌙 {round_num} приближается ночь, пожалуйста, закройте глаза, когда стемнеет..."
        return await self.announce(content)
    
    async def day_announcement(self, round_num: int) -> Msg:
        """Дневное объявление"""
        content = f"☀️ День {round_num} наступил рассвет, пожалуйста, откройте глаза..."
        return await self.announce(content)
    
    async def death_announcement(self, dead_players: List[str]) -> Msg:
        """объявление о смерти"""
        if not dead_players:
            content = "Прошлая ночь прошла без происшествий, никто не умер."
        else:
            content = f"Вчера вечером {format_player_list_str(dead_players)}, к сожалению, был убит."
        return await self.announce(content)
    
    async def vote_result_announcement(self, voted_out: str, vote_count: int) -> Msg:
        """Объявление результатов голосования"""
        content = f"Результаты голосования: {voted_out} выбыл, набрав {vote_count} голосов."
        return await self.announce(content)
    
    async def game_over_announcement(self, winner: str) -> Msg:
        """Объявление об окончании игры"""
        content = f"🎉Игра окончена! {победитель}"
        return await self.announce(content)


def format_player_list_str(players: List[str]) -> str:
    """Форматировать список имен игроков"""
    if not players:
        return "беспилотный"
    return "、".join(players)


def calculate_suspicion_score(player_name: str, game_history: List[Dict]) -> float:
    """Посчитать показатель подозрительности игрока"""
    score = 0.0
    
    for event in game_history:
        if event.get("type") == "vote" and event.get("target") == player_name:
            score += 0.3
        elif event.get("type") == "accusation" and event.get("target") == player_name:
            score += 0.2
        elif event.get("type") == "defense" and event.get("player") == player_name:
            score -= 0.1
    
    return min(max(score, 0.0), 1.0)


async def handle_interrupt(*args: Any, **kwargs: Any) -> Msg:
    """Обработка прерываний игры"""
    return Msg(
        name="система",
        content="игра прервана",
        role="system"
    )