"""
Прогрев данных панели мониторинга

При запуске информация об индексе, самостоятельном выборе и горячих точках получается параллельно через три потока MemoryService.
Запишите результат в MXTimedCache, и первый запрос экрана может попасть в кеш.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

DASHBOARD_INDEX_NAMES: tuple[str, ...] = (
«Шанхайский композитный индекс»,
«Индекс компонентов Шэньчжэня»,
«Индекс ГЕМ»,
«CSI 300»,
)


def warm_dashboard_cache() -> None:
"""Параллельная предварительная выборка информационной панели через трехпоточный кеш системы памяти"""
    try:
        from app.services.memory_service import get_memory_service

        mem = get_memory_service()

        if mem.should_refresh():
logger.info("Разминка информационной панели: запустить три потока для параллельного получения данных...")
            mem.parallel_fetch()
            logger.info("仪表盘预热: 完成 (indices=%d, watchlist=%d)",
                         len(mem.get_indices()), mem.get_stats().get("watchlist_count", 0))
        else:
logger.info("Разминка информационной панели: сегодняшний день сохранен в кэше, пропустить обновление")
    except Exception as exc:
        logger.warning("仪表盘预热失败（可忽略）: %s", exc)
