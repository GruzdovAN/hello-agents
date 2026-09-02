"""
金融 / 行情 API 冒烟测试（直连 FastAPI，需项目根目录 .env 已配置 MX_APIKEY）

Использование (в корневом каталоге проекта):
  py -3 -m backend.scripts.smoke_financial_api
Или в внутреннем каталоге:
  py -3 scripts/smoke_financial_api.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Путь: бэкэнд/скрипты -> бэкэнд -> корень проекта
_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_BACKEND))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def _short(obj, limit: int = 600) -> str:
    s = json.dumps(obj, ensure_ascii=False, default=str)
    return s if len(s) <= limit else s[:limit] + "…"


def _summarize_tables(data: dict) -> str:
    if not isinstance(data, dict):
вернуть "(не диктовать)"
    tables = data.get("tables") or []
    if not tables:
        return "tables=[]"
    t0 = tables[0]
    names = t0.get("fieldnames") or []
    rows = t0.get("rows") or []
    row0 = rows[0] if rows else None
    return f"fieldnames={names!r}, row0={row0!r}"


def main() -> int:
    client = TestClient(app)
    endpoints = [
        ("GET", "/api/v1/system/health", None),
("GET", "/api/v1/market/index", {"params": {"name": "Шанхайский составной индекс"}}),
("GET", "/api/v1/market/index", {"params": {"name": "CSI 300"}}),
        ("GET", "/api/v1/market/quote/600519", None),
        ("GET", "/api/v1/financial/indicators/600519", None),
        ("GET", "/api/v1/financial/profile/600519", None),
        ("GET", "/api/v1/financial/holders/600519", None),
    ]

print("=== API финансов/котировок Smoke (TestClient)===\n")

    for method, path, kw in endpoints:
        kw = kw or {}
        r = client.request(method, path, **kw)
        body = r.json()
        inner = body.get("data") if isinstance(body, dict) else None
        ok_http = r.status_code == 200
        ok_biz = isinstance(body, dict) and body.get("code") == 0
        mx_ok = isinstance(inner, dict) and inner.get("success") is True

        line1 = f"{method} {path} [{r.status_code}] code={body.get('code') if isinstance(body, dict) else '?'}"
        print(line1)
        if not ok_http or not ok_biz:
print(f" -> Исключение ответа: {_short(body)}")
            print()
            continue

        if inner is None:
            print(f"  -> data=None {_short(body)}")
            print()
            continue

        if isinstance(inner, dict) and "success" in inner:
            print(f"  -> mx success={inner.get('success')} total_rows={inner.get('total_rows')} error={inner.get('error')}")
            print(f"  -> {_summarize_tables(inner)}")
        else:
            print(f"  -> {_short(inner)}")
        print()

print("Объяснение: Когда mx Success=false или таблицы пусты, это в основном проблема с возвратом или синтаксическим анализом интерфейса Wonderful; если HTTP не 200, см. сообщение.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
