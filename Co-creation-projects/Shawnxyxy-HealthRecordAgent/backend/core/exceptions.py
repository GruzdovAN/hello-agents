"""
Система исключений проекта HealthRecordAgent
"""

class HealthAgentException(Exception):
"""Базовые классы исключений"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class AgentException(HealthAgentException):
"""Исключение выполнения агента"""
    pass


class ValidationException(HealthAgentException):
"""Исключение проверки ввода/вывода"""
    pass


class LLMException(HealthAgentException):
"""Исключение вызова LLM"""
    pass


class TimeoutException(HealthAgentException):
"""Исключение тайм-аута"""
    pass