"""Пользовательский класс исключений LearningAgent"""


class LearningAgentError(Exception):
"""Базовые классы исключений"""

    pass


class DomainNotFoundError(LearningAgentError):
"""Поле не существует"""

    def __init__(self, domain: str):
        self.domain = domain
super().__init__(f"Домен '{domain}' не существует. Сначала используйте /create, чтобы создать план обучения.")


class FileReadError(LearningAgentError):
"""Не удалось прочитать файл"""

    def __init__(self, message: str):
super().__init__(f"Ошибка чтения файла: {сообщение}")


class FileWriteError(LearningAgentError):
"""Ошибка записи файла"""

    def __init__(self, message: str):
super().__init__(f"Ошибка записи файла: {сообщение}")


class LLMError(LearningAgentError):
"""Вызов LLM не удался"""

    def __init__(self, message: str):
super().__init__(f"Ошибка службы AI: {сообщение}")


class InvalidInputError(LearningAgentError):
"""Неверный ввод"""

    def __init__(self, message: str):
super().__init__(f"Неверный ввод: {сообщение}")
