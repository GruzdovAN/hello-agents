"""Единое бизнес-исключение: после создания оно будет преобразовано в фиксированный JSON глобальным обработчиком."""

from __future__ import annotations


class AppError(Exception):
"""Ожидаемый базовый класс исключения."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "APP_ERROR",
        status_code: int = 400,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class BadRequestError(AppError):
    def __init__(self, message: str = "请求参数错误") -> None:
        super().__init__(message, code="BAD_REQUEST", status_code=400)


class NotFoundError(AppError):
    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404)


class ExternalServiceError(AppError):
def __init__(self, message: str = «Ошибка вызова внешней службы», *, status_code: int = 502) -> Нет:
        super().__init__(message, code="EXTERNAL_SERVICE", status_code=status_code)


class MovieServiceError(ExternalServiceError):
"""Ошибки, связанные с TMDB/MovieService."""

    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message, status_code=status_code)
        self.code = "TMDB_ERROR"
