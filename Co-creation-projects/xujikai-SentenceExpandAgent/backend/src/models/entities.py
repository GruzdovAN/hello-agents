"""
Определение объекта данных — агент расширения английского предложения
"""
from pydantic import BaseModel
from typing import Optional, Literal


# Перечисление фаз расширения
Stage = Literal["stage1", "stage2", "stage3", "done"]


# Рекорд одного раунда расширения
class RoundRecord(BaseModel):
"""Запись полной информации об одном раунде расширения"""
    stage: Stage
вопрос: str # Вопрос репортера
user_answer: str # Предложение, введенное пользователем.
оценка: str # Грамматические комментарии
expanded_sentence: str # Результаты этого раунда расширения


# Состояние всего сеанса
class SessionState(BaseModel):
    """会话完整状态管理"""
    session_id: str
    mode: Literal["manual", "auto"]
    seed_sentence: str
    current_stage: Stage
    rounds: list[RoundRecord] = []
    final_polished: Optional[str] = None


# Интерфейс инициирует запрос
class StartRequest(BaseModel):
"""Начать новый сеанс расширения"""
    seed_sentence: str
    mode: Literal["manual", "auto"]


# Пользователь отправляет расширение предложения (ручной режим)
class SubmitRequest(BaseModel):
"""Отправлять расширенные пользователем предложения"""
    session_id: str
    user_sentence: str


#Отдельный ответ агента
class AgentResponse(BaseModel):
"""Данные ответа агента"""
    session_id: str
    stage: Stage
    question: Optional[str] = None
    evaluation: Optional[str] = None
    expanded_sentence: Optional[str] = None
    final_polished: Optional[str] = None
    is_done: bool = False
