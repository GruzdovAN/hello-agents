"""Ошибка обработки декораторов и служебных функций"""

import logging
from functools import wraps
from typing import Callable, Any
from utils.exceptions import (
    LearningAgentError,
    DomainNotFoundError,
    FileReadError,
    FileWriteError,
    LLMError,
)

logger = logging.getLogger(__name__)


def handle_errors(func: Callable) -> Callable:
    """
Единый декоратор обработки ошибок

Перехват исключений и возврат дружественных сообщений об ошибках
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)

        except DomainNotFoundError as e:
            return f"❌ 错误：{e}\n请先使用 /create 创建学习计划。"

        except FileReadError as e:
return f"❌ {e}\nПожалуйста, проверьте путь к файлу и разрешения."

        except FileWriteError as e:
return f"❌ {e}\nПожалуйста, проверьте место на диске и разрешения."

        except LLMError as e:
return f"❌ {e}\nПовторите попытку позже или проверьте конфигурацию."

        except KeyboardInterrupt:
return "\n\n👋 Операция отменена"

        except LearningAgentError as e:
            logger.error(f"LearningAgent error in {func.__name__}: {e}")
            return f"❌ {e}"

        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            return f"❌ 发生未知错误：{e}\n请查看日志或联系开发者。"

    return wrapper
