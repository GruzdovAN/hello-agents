"""Шаг 6: Система памяти для анализа запасов
Постоянное хранилище: список наблюдения, история анализа, настройки пользователя.
"""
import json
import os
from datetime import datetime
from typing import Optional


class StockMemory:
"""Память для анализа акций — постоянство файла JSON"""

    def __init__(self, path: str = "memory/stock_memory.json"):
        import threading
        self.path = path
        self.data = self._load()
        self._lock = threading.Lock()

    def _load(self) -> dict:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"watchlist": {}, "history": [], "preferences": {}}

    def _save(self):
        import tempfile

        with self._lock:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(self.path))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                os.replace(temp_path, self.path)
            except Exception:
                os.remove(temp_path)
                raise

# ===== Список наблюдения =====
    def add_watchlist(self, code: str, name: str = "", notes: str = "") -> str:
        self.data["watchlist"][code] = {
            "name": name or code,
            "notes": notes,
            "added": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self._save()
return f"{имя или код}({код}) добавлено в список наблюдения"

    def remove_watchlist(self, code: str) -> str:
        if code in self.data["watchlist"]:
            name = self.data["watchlist"][code]["name"]
            del self.data["watchlist"][code]
            self._save()
return f"{name}({code}) удалено из списка наблюдения"
return f"{код} не найден в списке наблюдения"

    def get_watchlist(self, query: str = "") -> str:
        wl = self.data["watchlist"]
        if not wl:
return «Список подписчиков пуст. Чтобы добавить, скажите «Следовать 600519».
lines = [f"Список наблюдения (только {len(wl)}):"]
        for code, info in wl.items():
            lines.append(f"  {info['name']}({code})  [{info['added']}]")
            if info.get("notes"):
                lines.append(f"    备注: {info['notes']}")
        return "\n".join(lines)

# ===== История анализа =====
    def save_analysis(self, code: str, question: str, summary: str) -> str:
        record = {
            "code": code,
            "question": question,
            "summary": summary[:500],  # 截取前500字作为摘要
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.data["history"].append(record)
# Сохраняйте только последние 100 элементов
        if len(self.data["history"]) > 100:
            self.data["history"] = self.data["history"][-100:]
        self._save()
        return f"分析记录已保存 ({len(self.data['history'])} 条历史)"

    def get_history(self, query: str = "") -> str:
        code = query.strip() if query else ""
        records = self.data["history"]
        if code:
            records = [r for r in records if r["code"] == code]
        if not records:
            return f"暂无{' ' + code + ' 的' if code else ''}分析历史"
lines = [f"История анализа (недавний {len(records)}):"]
for r in Records[-10:]: # Последние 10 записей
            lines.append(f"  [{r['timestamp']}] {r['code']}: {r['question'][:60]}")
        return "\n".join(lines)

    def get_last_analysis(self, code: str = "") -> Optional[str]:
        records = self.data["history"]
        if code:
            records = [r for r in records if r["code"] == code]
        if records:
            return records[-1].get("summary", "")
        return None

# ===== Настройки пользователя =====
    def set_preference(self, key: str, value: str) -> str:
        self.data["preferences"][key] = value
        self._save()
return f"Набор предпочтений: {ключ} = {значение}"

    def get_preferences(self, query: str = "") -> str:
        prefs = self.data["preferences"]
        if not prefs:
            return "暂无保存的偏好。可以设置如: '偏好 分析风格=深度价值投资'"
линии = ["Настройки пользователя:"]
        for k, v in prefs.items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    def clear(self) -> str:
        self.data = {"watchlist": {}, "history": [], "preferences": {}}
        self._save()
вернуть «Память очищена»


# Глобальный синглтон
_memory_instance = None


def get_memory() -> StockMemory:
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = StockMemory()
    return _memory_instance


# ===== Функция инструмента (может быть зарегистрирована непосредственно в ToolRegistry) =====

def memory_add_watchlist(query: str) -> str:
"""Добавьте акции в список наблюдения. Введите: «Код|Имя», например «600519|Kweichow Moutai»»»»
    parts = query.strip().split("|")
    code = parts[0].strip()
    name = parts[1].strip() if len(parts) > 1 else ""
    return get_memory().add_watchlist(code, name)


def memory_remove_watchlist(code: str) -> str:
"""Удалите акцию из списка наблюдения. Введите: тикер"""
    return get_memory().remove_watchlist(code.strip())


def memory_get_watchlist(query: str = "") -> str:
"""Просмотреть список наблюдения"""
    return get_memory().get_watchlist(query)


def memory_save_analysis(query: str) -> str:
"""Сохраните результаты анализа. Введите: 'Код|Проблема|Сводка' """
    parts = query.strip().split("|")
    code = parts[0].strip() if len(parts) > 0 else ""
    question = parts[1].strip() if len(parts) > 1 else ""
    summary = parts[2].strip() if len(parts) > 2 else ""
    return get_memory().save_analysis(code, question, summary)


def memory_get_history(query: str = "") -> str:
"""Просмотреть историю анализа. Введите: код акции (необязательно, оставьте пустым, чтобы увидеть все)"""
    return get_memory().get_history(query)


def memory_set_preference(query: str) -> str:
"""Установите пользовательские настройки. Ввод: "ключ=значение", например "Стиль=В основном технический анализ""""
    if "=" in query:
        k, v = query.split("=", 1)
        return get_memory().set_preference(k.strip(), v.strip())
вернуть «Формат: ключ = значение»


def memory_get_preferences(query: str = "") -> str:
"""Просмотр настроек пользователя"""
    return get_memory().get_preferences()
