"""
Служба кэширования файлов данных об акциях — сохраняет все данные для каждой акции в локальном файле.

Каждый раз, когда получаются данные, они сначала считываются из локального файла, а интерфейс вызывается только тогда, когда данные не попали или срок их действия истек.
Поддерживает поиск по содержимому файлов в стиле grep.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Any

from app.config import settings

logger = logging.getLogger(__name__)

_cache_lock = threading.Lock()

# Корневой каталог кэша
_STOCK_CACHE_ROOT = settings.DATA_DIR / "stock_cache"

#Имена файлов каждого типа данных
_DATA_TYPE_FILES = {
    "quote": "quote.json",
    "financial": "financial.json",
    "profile": "profile.json",
    "holders": "holders.json",
    "sentiment": "sentiment.json",
    "news": "news.json",
}

# Срок действия кэша в течение дня (одна и та же акция вызывается только один раз в один и тот же день)
_TODAY = date.today().isoformat()


class StockFileCache:
"""Кэш файла стандартных данных"""

    def __init__(self):
        _STOCK_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
        self._index_file = _STOCK_CACHE_ROOT / "_index.json"
        self._index: dict = {}
        self._load_index()

# ---- Управление индексами ----

    def _load_index(self):
"""Загрузить основной индекс"""
        try:
            if self._index_file.exists():
                self._index = json.loads(self._index_file.read_text(encoding="utf-8"))
                logger.debug("文件缓存索引已加载: %d 条", len(self._index))
        except Exception:
            self._index = {}

    def _save_index(self):
"""Сохранить основной индекс"""
        try:
            self._index_file.write_text(json.dumps(self._index, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("保存缓存索引失败: %s", e)

    def _stock_dir(self, stock_code: str) -> Path:
        clean = stock_code.strip().upper()
        d = _STOCK_CACHE_ROOT / clean
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _data_file(self, stock_code: str, data_type: str) -> Path:
        filename = _DATA_TYPE_FILES.get(data_type, f"{data_type}.json")
        return self._stock_dir(stock_code) / filename

    def _update_index(self, stock_code: str, data_type: str):
        code = stock_code.strip().upper()
        if code not in self._index:
            self._index[code] = {"data_types": [], "cached_at": datetime.now().isoformat()}
        if data_type not in self._index[code]["data_types"]:
            self._index[code]["data_types"].append(data_type)
        self._index[code]["cached_at"] = datetime.now().isoformat()

# ---- Операции чтения и записи ----

    def get(self, stock_code: str, data_type: str, max_age_hours: int = 24) -> Optional[dict]:
        """
Чтение данных из файлового кэша

        Args:
stock_code: код акции
data_type: тип данных (цитата/финансы/профиль/держатели/настроения/новости)
max_age_hours: Максимальный срок действия (часы), при превышении он будет считаться истекшим

        Returns:
Словарь данных кэша, возвращает None, если он не попал или срок его действия истек.
        """
        filepath = self._data_file(stock_code, data_type)
        if not filepath.exists():
            return None

#Проверяем возраст файла
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600
        file_date = mtime.strftime("%Y-%m-%d")

# Данные дня возвращаются напрямую (без ограничения количества часов)
        if file_date == _TODAY:
            pass
        elif age_hours > max_age_hours:
logger.debug("Срок действия кэша: %s/%s (%.1f часов назад)", stock_code, data_type, age_hours)
            return None

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            logger.debug("文件缓存命中: %s/%s", stock_code, data_type)
            return data
        except Exception as e:
            logger.warning("读取缓存文件失败 %s: %s", filepath, e)
            return None

    def set(self, stock_code: str, data_type: str, data: dict) -> bool:
        """
Запись данных в файловый кеш

        Args:
stock_code: код акции
data_type: тип данных
данные: словарь данных

        Returns:
            是否写入成功
        """
        filepath = self._data_file(stock_code, data_type)
        try:
            wrapper = {
                "stock_code": stock_code,
                "data_type": data_type,
                "cached_at": datetime.now().isoformat(),
                "cache_date": _TODAY,
                "data": data,
            }
            filepath.write_text(json.dumps(wrapper, ensure_ascii=False, indent=2), encoding="utf-8")
            self._update_index(stock_code, data_type)
            self._save_index()
            logger.debug("文件缓存写入: %s/%s", stock_code, data_type)
            return True
        except Exception as e:
            logger.warning("写入缓存文件失败 %s: %s", filepath, e)
            return False

    def has(self, stock_code: str, data_type: str) -> bool:
"""Проверьте наличие действующего кэша"""
        filepath = self._data_file(stock_code, data_type)
        if not filepath.exists():
            return False
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        return mtime.strftime("%Y-%m-%d") == _TODAY

# ---- поиск в стиле grep ----

    def grep_search(self, keyword: str, data_type: Optional[str] = None) -> list[dict]:
        """
Искать все кэшированные файлы по ключевым словам (аналогично grep)

        Args:
ключевое слово: ключевое слово поиска
data_type: ограниченный тип данных, None означает все

        Returns:
Список результатов сопоставления [{stock_code, data_type, file_path, line: str, ...}]
        """
        results = []
        keyword_lower = keyword.lower()

# Сначала проверьте индекс, чтобы быстро найти акции-кандидаты
        candidates = []
        for code, info in self._index.items():
            if keyword_lower in code.lower():
                candidates.append(code)
                continue
            types = info.get("data_types", [])
            if data_type and data_type not in types:
                continue
            candidates.append(code)

# Создайте grep содержимого для каталога-кандидата на складе
        for code in candidates:
            stock_dir = self._stock_dir(code)
            if not stock_dir.exists():
                continue

            for fname in stock_dir.glob("*.json"):
                dtype = fname.stem
                if data_type and dtype != data_type:
                    continue

                try:
                    content = fname.read_text(encoding="utf-8")
                    if keyword_lower in content.lower():
# Извлечь совпадающие строки
                        lines = content.split("\n")
                        matched_lines = [l.strip() for l in lines if keyword_lower in l.lower()]
                        results.append({
                            "stock_code": code,
                            "data_type": dtype,
                            "file_path": str(fname),
                            "matched_lines": matched_lines[:10],
                            "match_count": len(matched_lines),
                            "cached_at": datetime.fromtimestamp(fname.stat().st_mtime).isoformat(),
                        })
                except Exception:
                    continue

        return results

    def get_stock_codes(self) -> list[str]:
"""Получить все кэшированные биржевые символы"""
        return list(self._index.keys())

    def get_stock_data_types(self, stock_code: str) -> list[str]:
"""Получить тип кэшированных данных акции"""
        info = self._index.get(stock_code.upper(), {})
        return info.get("data_types", [])

    def clear_stock_cache(self, stock_code: Optional[str] = None):
"""Очистить кеш"""
        if stock_code:
            stock_dir = self._stock_dir(stock_code)
            for f in stock_dir.glob("*.json"):
                try:
                    f.unlink()
                except Exception:
                    pass
            code = stock_code.upper()
            self._index.pop(code, None)
            self._save_index()
        else:
            for f in _STOCK_CACHE_ROOT.glob("**/*.json"):
                try:
                    f.unlink()
                except Exception:
                    pass
            self._index.clear()
            self._save_index()

    def get_stats(self) -> dict:
"""Получить статистику кэша"""
        total_files = sum(1 for _ in _STOCK_CACHE_ROOT.glob("**/*.json"))
        total_size = sum(f.stat().st_size for f in _STOCK_CACHE_ROOT.glob("**/*.json") if f.is_file())
        return {
            "stock_count": len(self._index),
            "total_files": total_files,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "cache_root": str(_STOCK_CACHE_ROOT),
        }


_stock_cache_instance: Optional[StockFileCache] = None


def get_stock_file_cache() -> StockFileCache:
"""Получить глобальный синглтон StockFileCache"""
    global _stock_cache_instance
    if _stock_cache_instance is None:
        with _cache_lock:
            if _stock_cache_instance is None:
                _stock_cache_instance = StockFileCache()
    return _stock_cache_instance
