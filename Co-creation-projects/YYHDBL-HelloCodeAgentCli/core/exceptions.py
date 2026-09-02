"""Иерархия исключений"""

class HelloAgentsException(Exception):
    """Базовое исключение HelloAgents"""
    pass

class LLMException(HelloAgentsException):
    """Исключения, связанные с LLM"""
    pass

class AgentException(HelloAgentsException):
    """Исключения, связанные с агентом (Agent)"""
    pass

class ConfigException(HelloAgentsException):
    """Исключения, связанные с конфигурацией"""
    pass

class ToolException(HelloAgentsException):
    """Исключения, связанные с инструментами"""
    pass
