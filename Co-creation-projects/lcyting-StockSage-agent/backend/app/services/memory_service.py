"""
Система памяти — ежедневное кэширование и управление сроком действия снимков информационной панели.

Каждый день записывайте время и дату первого открытия серверной части; запускать обновление через несколько дней или при изменении количества дополнительных акций.
每天首次启动时三线程并行获取指数、自选、热点资讯，写入 data/memory/dashboard_state.json。
Независимо от ConversationManager/MemoryManager HelloAgents, история разговоров этого приложения управляется интерфейсом и таблицей истории SQLite.
"""

from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from typing import Any, Optional

from app.config import settings
from app.models.memory_models import MemorySnapshot

logger = logging.getLogger(__name__)

_memory_lock = threading.Lock()


class MemoryService:
    """
Основные службы системы памяти

Обязанности:
- Ежедневно записывайте дату первого запуска
- Очистить данные предыдущего дня и восстановить их во время дневной резки.
- Три потока получают данные информационной панели (индекс, самостоятельно выбранный, актуальная информация) параллельно.
- Обнаружение изменений в количестве самостоятельно выбранных акций для запуска обновления
    """

    def __init__(self, storage_dir: Optional[Path] = None):
        self._today: Optional[str] = None
        self._snapshot: Optional[MemorySnapshot] = None
        self._lock = threading.Lock()
        self._watchlist_count: int = 0

        self._storage_dir = storage_dir or (settings.DATA_DIR / "memory")
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._state_file = self._storage_dir / "dashboard_state.json"

        self._load_state()

# ---- Долговечность ----

    def _load_state(self) -> None:
"""Восстановить состояние последнего снимка с диска"""
        try:
            if self._state_file.exists():
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                self._today = data.get("today")
                self._watchlist_count = data.get("watchlist_count", 0)
                snap = data.get("snapshot")
                if snap:
                    self._snapshot = MemorySnapshot.from_dict(snap)
logger.info("Состояние системы памяти загружено: date=%s, watchlist_count=%d", self._today, self._watchlist_count)
        except Exception as exc:
            logger.warning("加载记忆状态失败: %s", exc)

    def _save_state(self) -> None:
"""Сохранение текущего состояния снимка на диск"""
        try:
            data = {
                "today": self._today,
                "watchlist_count": self._watchlist_count,
                "snapshot": self._snapshot.to_dict() if self._snapshot else None,
            }
            self._state_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("保存记忆状态失败: %s", exc)

# ---- Определение даты ----

    def _get_today(self) -> str:
        return date.today().isoformat()

    def is_new_day(self) -> bool:
"""Проверь, новый ли день"""
        return self._today != self._get_today()

    def should_refresh(self) -> bool:
        """
Определите, нужно ли обновлять данные:
1. Новый день
2. Изменение количества дополнительных акций
        """
        if self.is_new_day():
logger.info("Обнаружен новый день, и данные информационной панели необходимо обновить")
            return True

        try:
            from app.services import watchlist_service
            wl = watchlist_service.get_watchlist()
            current_count = wl.get("total", 0) if wl.get("success") else 0
            if current_count != self._watchlist_count and self._watchlist_count > 0:
logger.info("Изменение количества самостоятельно выбранных акций: %d -> %d, необходимо обновить", self._watchlist_count, current_count)
                self._watchlist_count = current_count
                self._save_state()
                return True
        except Exception as exc:
logger.debug("Ошибка проверки количества дополнительных акций: %s", exc)

        return False

# ---- Сбор данных ----

    def _fetch_indices(self) -> list:
"""Получить данные четырех основных индексов"""
        from app.services import market_service

        index_names = ("上证指数", "深证成指", "创业板指", "沪深300")
        results = []
        for name in index_names:
            try:
                data = market_service.get_index_quote(name)
                results.append({"name": name, "data": data})
            except Exception as exc:
                logger.debug("记忆系统获取指数失败 %s: %s", name, exc)
        return results

    def _fetch_watchlist(self) -> dict:
"""Получить список выбранных вами акций (включая рыночные данные)"""
        from app.services import watchlist_service

        try:
            wl = watchlist_service.get_watchlist()
            if wl.get("success"):
                self._watchlist_count = wl.get("total", 0)
            return wl
        except Exception as exc:
            logger.debug("记忆系统获取自选股失败: %s", exc)
            return {"success": False, "stocks": [], "total": 0}

    def _fetch_hot_news(self) -> dict:
"""Получите горячую информацию"""
        from app.services import news_service

        try:
            return news_service.search_market_news() or {}
        except Exception as exc:
            logger.debug("记忆系统获取热点资讯失败: %s", exc)
            return {}

    def parallel_fetch(self) -> MemorySnapshot:
        """
Три потока получают данные информационной панели параллельно: индекс, самостоятельно выбранный и горячую информацию.
        """
logger.info("Система памяти: запустите три потока для параллельного получения данных информационной панели...")

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_indices = executor.submit(self._fetch_indices)
            future_watchlist = executor.submit(self._fetch_watchlist)
            future_news = executor.submit(self._fetch_hot_news)

            results: dict[str, Any] = {}
            for future in as_completed([future_indices, future_watchlist, future_news]):
                try:
                    value = future.result()
                except Exception as exc:
                    logger.warning("并行获取任务失败: %s", exc)
                    value = None

                if future == future_indices:
                    results["indices"] = value or []
                elif future == future_watchlist:
                    results["watchlist"] = value or {}
                elif future == future_news:
                    results["hot_news"] = value or {}

        today = self._get_today()
        snapshot = MemorySnapshot(
            date_str=today,
            indices=results.get("indices", []),
            watchlist=results.get("watchlist", {}),
            hot_news=results.get("hot_news", {}),
            watchlist_count=self._watchlist_count,
        )

        with self._lock:
            self._today = today
            self._snapshot = snapshot
            self._save_state()

logger.info("Система памяти: сбор данных информационной панели завершен (дата=%s, индексы=%d, список наблюдения=%d)",
                     today, len(snapshot.indices), snapshot.watchlist_count)
        return snapshot

    # ---- 公共接口 ----

    def get_snapshot(self) -> Optional[MemorySnapshot]:
"""Получить текущий кэшированный снимок панели мониторинга"""
        with self._lock:
            return self._snapshot

    def get_indices(self) -> list:
"""Получить данные кэшированного индекса"""
        snap = self.get_snapshot()
        return snap.indices if snap else []

    def get_watchlist(self) -> dict:
"""Получить кэшированные данные выбора акций"""
        snap = self.get_snapshot()
        return snap.watchlist if snap else {}

    def get_hot_news(self) -> dict:
        """获取缓存的热点资讯数据"""
        snap = self.get_snapshot()
        return snap.hot_news if snap else {}

    def clear(self) -> None:
"""Очистить все данные памяти"""
        with self._lock:
            self._today = None
            self._snapshot = None
            self._watchlist_count = 0
            try:
                if self._state_file.exists():
                    self._state_file.unlink()
            except Exception:
                pass

    def get_stats(self) -> dict:
"""Получить состояние системы памяти"""
        with self._lock:
            return {
                "today": self._today,
                "has_snapshot": self._snapshot is not None,
                "watchlist_count": self._watchlist_count,
                "indices_count": len(self._snapshot.indices) if self._snapshot else 0,
                "storage_dir": str(self._storage_dir),
            }


_memory_svc: Optional[MemoryService] = None


def get_memory_service() -> MemoryService:
"""Получить глобальный синглтон MemoryService"""
    global _memory_svc
    if _memory_svc is None:
        with _memory_lock:
            if _memory_svc is None:
                _memory_svc = MemoryService()
    return _memory_svc
