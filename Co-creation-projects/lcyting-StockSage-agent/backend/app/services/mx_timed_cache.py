"""
Замечательный кэш синхронизации интерфейса (в процессе)

— Тот же запрос будет напрямую возвращен в кеш в течение TTL по умолчанию, равного 10 минутам, что сокращает количество повторных вызовов.
- При исчерпании квоты кэш с истекшим сроком действия можно понизить (см. каждый пакет услуг).
"""

from __future__ import annotations

import copy
import hashlib
import threading
import time
from typing import Any, Optional

from app.config import settings


class MXTimedCache:
"""Потокобезопасная строка запроса -> кэш снимков результатов"""

    def __init__(self, max_entries: int = 400):
        self._max = max_entries
        self._lock = threading.Lock()
        # key -> (monotonic_ts, payload)
        self._data: dict[str, tuple[float, Any]] = {}
        self._order: list[str] = []

    @staticmethod
    def normalize_query(q: str) -> str:
        return " ".join((q or "").split())

    def make_key(self, channel: str, query: str) -> str:
        n = self.normalize_query(query)
        digest = hashlib.sha256(n.encode("utf-8")).hexdigest()[:32]
        return f"{channel}:{digest}"

    def get_fresh(self, key: str, ttl_seconds: float) -> Optional[Any]:
        if ttl_seconds <= 0:
            return None
        with self._lock:
            ent = self._data.get(key)
            if not ent:
                return None
            ts, payload = ent
            if time.monotonic() - ts > ttl_seconds:
                return None
            return copy.deepcopy(payload)

    def get_stale(self, key: str) -> Optional[Any]:
"""Не нажимайте TTL, возвращайтесь, пока есть снимок (используется для исчерпания квоты и понижения версии)"""
        with self._lock:
            ent = self._data.get(key)
            if not ent:
                return None
            return copy.deepcopy(ent[1])

    def set(self, key: str, payload: Any) -> None:
        snap = copy.deepcopy(payload)
        with self._lock:
            self._data[key] = (time.monotonic(), snap)
            if key in self._order:
                self._order.remove(key)
            self._order.append(key)
            while len(self._order) > self._max:
                old = self._order.pop(0)
                self._data.pop(old, None)

    def delete(self, key: str) -> None:
"""Активная аннулация (например, не использовать старый снимок списка в течение длительного времени после добавления или удаления дополнительных акций)"""
        with self._lock:
            self._data.pop(key, None)
            if key in self._order:
                self._order.remove(key)


_mx_cache_singleton: Optional[MXTimedCache] = None


def get_mx_timed_cache() -> MXTimedCache:
    global _mx_cache_singleton
    if _mx_cache_singleton is None:
        _mx_cache_singleton = MXTimedCache()
    return _mx_cache_singleton


def mx_cache_ttl_seconds() -> float:
    return float(getattr(settings, "MX_CACHE_TTL_SECONDS", 600))
