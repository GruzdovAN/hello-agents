"""Модуль инженерии контекста

Обеспечивает инженерию контекста для фреймворка HelloAgents:
- ContextBuilder: конвейер GSSC (Gather-Select-Structure-Compress)
"""

from .builder import ContextBuilder, ContextConfig, ContextPacket

__all__ = ["ContextBuilder", "ContextConfig", "ContextPacket"]

