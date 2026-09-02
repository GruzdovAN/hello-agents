import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import get_config

logger = logging.getLogger("game.logic")

class GameSession:
    """Класс управления игровой сессией"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Состояние игры
        self.current_figure: Optional[Dict] = None
        self.hints: List[str] = []  # pre-generated hints by agent
        self.questions_asked = 0
        self.hints_used = 0
        self.is_game_over = False
        self.is_correct = False
        self.guess_history: List[str] = []
        
        # Конфигурация
        _config = get_config()
        self.max_questions = _config.MAX_QUESTIONS
        self.max_hints = _config.MAX_HINTS
        
        # Инициализация состояния игры (current_figure заполняется при инициализации Agent)
        self._reset_state()
    
    def _reset_state(self):
        """Сброс состояния игры (без загрузки персонажа — это делает Agent)"""
        self.current_figure = None
        self.hints = []
        self.questions_asked = 0
        self.hints_used = 0
        self.is_game_over = False
        self.is_correct = False
        self.guess_history = []
        self.updated_at = datetime.now()
    
    def ask_question(self) -> bool:
        """Записать вопрос и вернуть, можно ли продолжать задавать вопросы"""
        self.questions_asked += 1
        self.updated_at = datetime.now()
        
        if self.questions_asked >= self.max_questions:
            self.is_game_over = True
            return False
        return True
    
    def make_guess(self, guess_name: str, semantic_match_fn=None) -> Dict[str, Any]:
        """Сделать догадку и вернуть результат"""
        self.updated_at = datetime.now()
        self.guess_history.append(guess_name)

        actual_name = self.current_figure["name"]

        # First try exact match, then fall back to semantic match via injected fn
        is_correct = guess_name.strip().lower() == actual_name.lower()
        if not is_correct and semantic_match_fn is not None:
            is_correct = semantic_match_fn(guess_name, actual_name)
        
        if is_correct:
            self.is_correct = True
            self.is_game_over = True
            return {
                "correct": True,
                "message": "Поздравляем, вы угадали!",
                "figure_info": self.current_figure
            }
        else:
            # Проверка достижения лимита вопросов
            if self.questions_asked >= self.max_questions:
                self.is_game_over = True
                return {
                    "correct": False,
                    "message": "Игра окончена! Правильный ответ: {}".format(self.current_figure["name"]),
                    "figure_info": self.current_figure
                }
            else:
                return {
                    "correct": False,
                    "message": "Неверно, продолжайте задавать вопросы или угадывать",
                    "remaining_questions": self.max_questions - self.questions_asked
                }
    
    def get_hint(self) -> Optional[Dict[str, Any]]:
        """Получить подсказку (по порядку из предварительно сгенерированного списка hints)"""
        if self.hints_used >= self.max_hints:
            return {
                "available": False,
                "message": "Подсказки исчерпаны"
            }

        hint_index = self.hints_used
        self.hints_used += 1
        self.updated_at = datetime.now()

        hint_text = (
            self.hints[hint_index]
            if self.hints and hint_index < len(self.hints)
            else "Это широко известная личность"
        )

        return {
            "available": True,
            "hint_level": self.hints_used,
            "hint": hint_text,
            "remaining_hints": self.max_hints - self.hints_used
        }
    
    def get_game_status(self) -> Dict[str, Any]:
        """Получить текущее состояние игры"""
        return {
            "session_id": self.session_id,
            "questions_asked": self.questions_asked,
            "hints_used": self.hints_used,
            "remaining_questions": self.max_questions - self.questions_asked,
            "remaining_hints": self.max_hints - self.hints_used,
            "is_game_over": self.is_game_over,
            "is_correct": self.is_correct,
            "guess_history": self.guess_history
        }
    
    def reset_game(self):
        """Сбросить состояние игры (Agent заново генерирует персонажа)"""
        self._reset_state()
    
    def get_figure_for_prompt(self) -> Dict[str, str]:
        """Получить информацию о персонаже для промпта Agent"""
        if not self.current_figure:
            return {}

        return {
            "name": self.current_figure.get("name", ""),
            "bio": self.current_figure.get("bio", ""),
        }


class GameManager:
    """Менеджер игровых сессий"""
    
    def __init__(self):
        self.active_sessions: Dict[str, GameSession] = {}
    
    def create_session(self) -> GameSession:
        """Создать новую игровую сессию"""
        session = GameSession()
        self.active_sessions[session.session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[GameSession]:
        """Получить игровую сессию"""
        return self.active_sessions.get(session_id)
    
    def end_session(self, session_id: str):
        """Завершить игровую сессию"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def cleanup_old_sessions(self, max_age_minutes: int = 60):
        """Очистить просроченные сессии"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            if (now - session.updated_at).total_seconds() > max_age_minutes * 60:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]


# Глобальный экземпляр менеджера игр
game_manager = GameManager()
