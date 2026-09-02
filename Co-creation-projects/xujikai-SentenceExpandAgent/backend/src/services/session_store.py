"""
Управление сеансами памяти - агент расширения английских предложений
"""
import uuid
from typing import Optional
from models.entities import SessionState


class SessionStore:
"""Хранилище сеансов в памяти (поддерживает параллелизм)"""
    
    def __init__(self):
"""Инициализировать хранилище сеансов"""
        self._sessions: dict[str, SessionState] = {}
    
    def create_session(
        self,
        seed_sentence: str,
        mode: str = "manual"
    ) -> SessionState:
        """
Создать новый сеанс
        
        Args:
seed_sentence: начальное предложение
режим: режим (ручной/авто)
            
        Returns:
SessionState: новое созданное состояние сеанса.
        """
        session_id = str(uuid.uuid4())
        session = SessionState(
            session_id=session_id,
            mode=mode,
            seed_sentence=seed_sentence,
            current_stage="stage1",
            rounds=[]
        )
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """
Получить сеанс
        
        Args:
session_id: идентификатор сеанса
            
        Returns:
            Optional[SessionState]: 会话状态，不存在则返回 None
        """
        return self._sessions.get(session_id)
    
    def update_session(self, session: SessionState) -> None:
        """
обновить сеанс
        
        Args:
сеанс: обновленное состояние сеанса
        """
        self._sessions[session.session_id] = session
    
    def delete_session(self, session_id: str) -> bool:
        """
Удалить сеанс
        
        Args:
session_id: идентификатор сеанса
            
        Returns:
bool: возвращает True, если удаление прошло успешно, возвращает False, если сеанс не существует.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> list[SessionState]:
        """
Список всех сессий
        
        Returns:
list[SessionState]: список всех состояний сеанса
        """
        return list(self._sessions.values())
    
    def session_exists(self, session_id: str) -> bool:
        """
Проверьте, существует ли сессия
        
        Args:
session_id: идентификатор сеанса
            
        Returns:
bool: Возвращает True, если существует, в противном случае возвращает False.
        """
        return session_id in self._sessions


# Экземпляр хранилища глобальных сеансов (единичный случай)
_session_store_instance = None


def get_session_store() -> SessionStore:
    """
Получить экземпляр глобального хранилища сеансов (одиночный режим)
    
    Returns:
SessionStore: экземпляр хранилища сеансов.
    """
    global _session_store_instance
    if _session_store_instance is None:
        _session_store_instance = SessionStore()
    return _session_store_instance


def reset_session_store():
"""Сбросить хранилище сеанса (для тестирования)"""
    global _session_store_instance
    _session_store_instance = None
