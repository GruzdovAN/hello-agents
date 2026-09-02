#!/usr/bin/env python3
"""
Сохраните исходный JSON, возвращенный интерфейсом Miaoxiang, в backend/fixtures/mx_raw/,
Впоследствии установите MX_REPLAY_FIXTURES=1 для локального воспроизведения того же запроса без использования кредита.

在项目根目录执行（需已配置 MX_APIKEY）:

  set PYTHONPATH=backend
  py backend/scripts/capture_mx_fixture.py mx_data "600519 最新价 涨跌幅"
py backend/scripts/capture_mx_fixture.py mx_search «Сегодняшние горячие точки рынка акций А, динамика рынка, фонды, ориентированные на север»
  py backend/scripts/capture_mx_fixture.py mx_xuangu "市盈率小于20"

Примечание. Запрос, сгенерированный сервером во время воспроизведения, должен быть точно таким же, как строка во время захвата (включая пробелы).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent

sys.path.insert(0, str(_BACKEND))
for p in (
    _ROOT / "agents",
_ROOT/"навыки"/"Финансовые данные"/"mx-данные",
_ROOT/"навыки"/"Поиск информации"/"mx-поиск",
_ROOT/"навыки"/"Умный выбор акций"/"mx-xuangu",
    _ROOT,
):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)


def main() -> None:
parser = argparse.ArgumentParser(description="Сохранить исходный ответ Wonderful Ideas как локальное приспособление")
    parser.add_argument(
        "channel",
        choices=("mx_data", "mx_search", "mx_xuangu"),
help="То же, что и навык, используемый на маршруте",
    )
    parser.add_argument("query", help="自然语言查询（须与线上一致）")
    args = parser.parse_args()

    from app.config import settings
    from app.utils.mx_fixture import fixture_path, save_raw_fixture

    if not settings.MX_APIKEY or settings.MX_APIKEY == "your-mx-apikey-here":
        print("错误：请在 .env 中配置 MX_APIKEY 后再抓取 fixture")
        sys.exit(1)

    if args.channel == "mx_data":
        import mx_data as _mx

        raw = _mx.MXData(api_key=settings.MX_APIKEY).query(args.query)
    elif args.channel == "mx_search":
        import mx_search as _mx

        raw = _mx.MXSearch(api_key=settings.MX_APIKEY).search(args.query)
    else:
        import mx_xuangu as _mx

        raw = _mx.MXSelectStock(api_key=settings.MX_APIKEY).search(args.query)

    path = save_raw_fixture(args.channel, args.query, raw)
print(f"Написано: {путь}")
print(f"Имя хэш-файла соответствует запросу: {args.query!r}")
print("Воспроизведение: переменная среды MX_REPLAY_FIXTURES=1 (необязательный MX_FIXTURE_DIR указывает на каталог), перезапустите серверную часть")


if __name__ == "__main__":
    main()
