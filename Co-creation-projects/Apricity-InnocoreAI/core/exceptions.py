"""
Пользовательский класс исключений InnoCore AI
"""

class InnoCoreException(Exception):
"""Базовый класс исключений InnoCore AI"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class AgentException(InnoCoreException):
"""Исключение, связанное с агентом"""
    pass

class VectorStoreException(InnoCoreException):
"""Исключение векторного хранилища"""
    pass

class DatabaseException(InnoCoreException):
"""Исключение базы данных"""
    pass

class LLMException(InnoCoreException):
"""Исключение вызова LLM"""
    pass

class PDFParsingException(InnoCoreException):
"""Исключение анализа PDF"""
    pass

class ExternalAPIException(InnoCoreException):
"""Исключение вызова внешнего API"""
    pass

class ConfigurationException(InnoCoreException):
"""Исключение конфигурации"""
    pass

class ValidationException(InnoCoreException):
"""Исключение проверки данных"""
    pass

class TimeoutException(InnoCoreException):
"""Исключение тайм-аута"""
    pass

class ResourceExhaustedException(InnoCoreException):
"""Исключение исчерпания ресурсов"""
    pass