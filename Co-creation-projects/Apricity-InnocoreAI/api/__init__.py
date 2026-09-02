"""Модуль InnoCore AI API"""

try:
    from .main import app
    from .routes import *
    __all__ = ["app"]
except ImportError:
    # Избегайте ошибок относительного импорта при прямом импорте
    pass