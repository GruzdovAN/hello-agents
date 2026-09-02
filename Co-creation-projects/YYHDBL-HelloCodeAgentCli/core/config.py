"""Управление конфигурацией — единая конфигурация Code Agent CLI"""

import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Единый класс конфигурации Code Agent CLI
    
    Централизованное управление параметрами:
    - загрузка из переменных окружения
    - значения по умолчанию
    - проверка типов
    """
    
    # ==================== Базовая конфигурация ====================
    project_name: str = Field(default="code_agent", description="Имя проекта")
    debug: bool = Field(default=False, description="Режим отладки")
    log_level: str = Field(default="INFO", description="Уровень логирования")
    
    # ==================== Конфигурация LLM ====================
    default_model: str = Field(default="gpt-3.5-turbo", description="Модель по умолчанию")
    default_provider: str = Field(default="openai", description="Провайдер по умолчанию")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Параметр temperature")
    max_tokens: Optional[int] = Field(default=None, description="Максимум токенов")
    llm_timeout: int = Field(default=60, gt=0, description="Таймаут запроса LLM (с)")
    
    # ==================== Конфигурация Agent ====================
    max_react_steps: int = Field(default=20, gt=0, le=50, description="Максимум шагов ReAct")
    max_history_turns: int = Field(default=50, gt=0, description="Максимум раундов истории диалога")
    observation_summary_threshold: int = Field(default=2000, gt=0, description="Порог суммаризации вывода инструментов")
    
    # ==================== Конфигурация контекста ====================
    context_max_tokens: int = Field(default=8000, gt=0, description="Максимум токенов контекста")
    context_reserve_ratio: float = Field(default=0.15, ge=0.0, le=0.5, description="Доля резерва под генерацию")
    context_enable_compression: bool = Field(default=True, description="Включить сжатие контекста")
    context_lazy_fetch: bool = Field(default=True, description="Подгружать контекст по запросу")
    
    # ==================== Конфигурация инструментов ====================
    terminal_timeout: int = Field(default=60, gt=0, description="Таймаут команд терминала (с)")
    terminal_max_output_size: int = Field(default=10 * 1024 * 1024, gt=0, description="Максимальный размер вывода терминала")
    terminal_confirm_dangerous: bool = Field(default=True, description="Опасные команды требуют подтверждения")
    terminal_allow_shell_mode: bool = Field(default=True, description="Разрешить режим Shell")
    context_fetch_max_tokens: int = Field(default=800, gt=0, description="Максимум токенов на один источник данных")
    context_fetch_context_lines: int = Field(default=5, ge=0, description="Число строк контекста кода")
    
    # ==================== Конфигурация исполнителя патчей ====================
    patch_max_files: int = Field(default=10, gt=0, description="Максимум файлов в одном патче")
    patch_max_total_lines: int = Field(default=800, gt=0, description="Максимум строк изменений в одном патче")
    patch_allowed_suffixes: List[str] = Field(
        default=[".py", ".md", ".toml", ".json", ".yml", ".yaml", ".txt", ".html", ".css", ".js", ".ts"],
        description="Разрешённые суффиксы изменяемых файлов"
    )
    
    # ==================== Конфигурация хранилища ====================
    helloagents_dir: str = Field(default=".helloagents", description="Каталог хранения состояния")
    
    # ==================== Конфигурация безопасности ====================
    confirm_delete_files: bool = Field(default=True, description="Удаление файлов требует подтверждения")
    confirm_large_changes: bool = Field(default=True, description="Крупные изменения требуют подтверждения")
    large_change_threshold_files: int = Field(default=6, gt=0, description="Порог числа файлов для крупного изменения")
    large_change_threshold_lines: int = Field(default=400, gt=0, description="Порог строк для крупного изменения")
    
    @classmethod
    def from_env(cls, **overrides) -> "Config":
        """Создаёт конфигурацию из переменных окружения
        
        Правила имён:
        - CODE_AGENT_<ИМЯ_ПАРАМЕТРА> или традиционные имена
        
        Args:
            **overrides: ручные переопределения
        """
        env_config = {
            "debug": os.getenv("DEBUG", "false").lower() == "true" or os.getenv("CODE_AGENT_DEBUG", "false").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            "helloagents_dir": os.getenv("HELLOAGENTS_DIR", os.getenv("CODE_AGENT_STATE_DIR", ".helloagents")),
            "max_react_steps": int(os.getenv("CODE_AGENT_MAX_REACT_STEPS", os.getenv("CODE_AGENT_MAX_STEPS", "20"))),
            "llm_timeout": int(os.getenv("LLM_TIMEOUT", "60")),
            "terminal_timeout": int(os.getenv("CODE_AGENT_TERMINAL_TIMEOUT", "60")),
            "patch_max_files": int(os.getenv("CODE_AGENT_PATCH_MAX_FILES", "10")),
            "patch_max_total_lines": int(os.getenv("CODE_AGENT_PATCH_MAX_LINES", "800")),
        }
        
        if os.getenv("MAX_TOKENS"):
            env_config["max_tokens"] = int(os.getenv("MAX_TOKENS"))
        
        # Объединение переопределений
        env_config.update(overrides)
        
        return cls(**env_config)
    
    def get_state_dir(self, repo_root: Path) -> Path:
        """Возвращает абсолютный путь каталога состояния"""
        state_path = Path(self.helloagents_dir)
        if state_path.is_absolute():
            return state_path
        return repo_root / state_path
    
    def get_notes_dir(self, repo_root: Path) -> Path:
        """Возвращает каталог заметок"""
        return self.get_state_dir(repo_root) / "notes"
    
    def get_sessions_dir(self, repo_root: Path) -> Path:
        """Возвращает каталог сессий"""
        return self.get_state_dir(repo_root) / "sessions"
    
    def get_backups_dir(self, repo_root: Path) -> Path:
        """Возвращает каталог резервных копий"""
        return self.get_state_dir(repo_root) / "backups"
    
    def get_todos_dir(self, repo_root: Path) -> Path:
        """Возвращает каталог задач"""
        return self.get_state_dir(repo_root) / "todos"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь"""
        return self.dict()
    
    def print_summary(self):
        """Печатает сводку конфигурации"""
        print("=" * 50)
        print("Конфигурация Code Agent CLI")
        print("=" * 50)
        print(f"Режим отладки: {self.debug}")
        print(f"Шаги ReAct: {self.max_react_steps}")
        print(f"Раундов истории: {self.max_history_turns}")
        print(f"Таймаут терминала: {self.terminal_timeout}s")
        print(f"Лимиты патча: {self.patch_max_files} файлов, {self.patch_max_total_lines} строк")
        print(f"Каталог состояния: {self.helloagents_dir}")
        print("=" * 50)
