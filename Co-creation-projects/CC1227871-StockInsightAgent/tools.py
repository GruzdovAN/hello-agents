"""Step 2: 股票分析工具 — akshare (Sina/Tencent 源) 真实数据 + 技术指标"""
import time
import numpy as np
import pandas as pd
import akshare as ak
from datetime import datetime, timedelta
from typing import Dict, Any


class ToolExecutor:
    """Центр регистрации и исполнения инструментов"""
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        self.tools[name] = {"description": description, "func": func}
        print(f"🔧 [Инструмент] {name} зарегистрирован")

    def getTool(self, name: str) -> callable:
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])


# ==================== Вспомогательные функции ====================

def _to_sina_code(code: str) -> str:
"""Преобразование чистого числового кода в формат Sina (sh600519 / sz000001)"""
    code = code.strip()
    if code.startswith("6"):
        return f"sh{code}"
    elif code.startswith(("0", "3")):
        return f"sz{code}"
    return code


def _resolve_symbol(query: str) -> str:
"""Разбор биржевых кодов: поддержка поиска по имени и возврат чистых числовых кодов"""
    query = query.strip()
    if query.isdigit() and len(query) == 6:
        return query

# Попробуйте использовать сопоставление akshare stock_info_a_code_name
    try:
        import akshare as ak
        stock_info = ak.stock_info_a_code_name()

# Сопоставить имена
        match = stock_info[stock_info["name"] == query]
        if not match.empty:
            return match["code"].values[0]

# Нечеткое имя совпадения
        fuzzy_match = stock_info[stock_info["name"].str.contains(query, na=False)]
        if not fuzzy_match.empty:
            return fuzzy_match["code"].values[0]
    except Exception:
        pass

# Попробуйте проверить через интерфейс новостей (косвенный метод)
    try:
        time.sleep(1)
        info = ak.stock_individual_info_em(symbol=query) if query.isdigit() else None
        if info is not None and len(info) > 0:
            return query
    except Exception:
        pass
    return query


def _safe_fetch(func, *args, **kwargs):
"""Сбор данных с повторной попыткой"""
    import random
    for attempt in range(3):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < 2:
                time.sleep(4 + random.random() * 2)
            else:
                return None


# ==================== Служебные функции ===================

def get_realtime_quote(query: str) -> str:
    """
Получите последние рыночные условия A-share. Ввод: код акции (например, «600519») или часть имени.
Источник данных: информация об акциях Oriental Fortune + последняя ежедневная линия Sina.
    """
print(f" [запрос рыночных условий в реальном времени] {query}")
    symbol = _resolve_symbol(query)

# Используйте ежедневную линию Sina, чтобы получать последние цены.
    try:
        sina_code = _to_sina_code(symbol)
        df = _safe_fetch(ak.stock_zh_a_daily,
                         symbol=sina_code,
                         start_date=(datetime.now() - timedelta(days=10)).strftime("%Y%m%d"),
                         end_date=datetime.now().strftime("%Y%m%d"),
                         adjust="qfq")
        if df is None or df.empty:
            df = _safe_fetch(ak.stock_zh_a_hist, symbol=symbol, period="daily", start_date=(datetime.now() - timedelta(days=10)).strftime("%Y%m%d"), end_date=datetime.now().strftime("%Y%m%d"), adjust="qfq")

        if df is None or df.empty:
return f"Рыночные данные для {symbol} не найдены"

        if df is not None and not df.empty:
# Унифицировать имена столбцов на английском языке для адаптации к последующей логике
            rename_map = {
                "日期": "date", "开盘": "open", "收盘": "close",
«Самый высокий»: «высокий», «Самый низкий»: «низкий», «Объем торгов»: «объем», «Сумма торгов»: «сумма»
            }
            df = df.rename(columns=rename_map)
    except Exception as e:
        return f"获取行情失败: {e}"

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

# Попытайтесь получить информацию об отдельных акциях (название, PE и т. д.)
    name = symbol
    pe = "N/A"
    try:
        time.sleep(2)
        info = ak.stock_individual_info_em(symbol=symbol)
name_row = info[info["item"] == "Аббревиатура акций"]
        if not name_row.empty:
            name = name_row["value"].values[0]
pe_row = info[info["item"] == "Динамическое соотношение P/E"]
        if not pe_row.empty:
            pe = pe_row["value"].values[0]
    except Exception:
        pass

    chg_pct = (latest["close"] - prev["close"]) / prev["close"] * 100

    return (
        f"{name}({symbol})\n"
        f"  最新价: {latest['close']:.2f}  涨跌幅: {chg_pct:+.2f}%\n"
f" Это открытие: {latest['open']:.2f} Самое высокое: {latest['high']:.2f} Самое низкое: {latest['low']:.2f}\n"
f" Объем торгов: {latest.get('volume', 'N/A')} лотов Сумма торгов: {latest.get('amount', 'N/A')} юаней\n"
f" Соотношение цены и прибыли (динамическое): {pe}"
    )


def get_historical_data(query: str) -> str:
    """
Получите исторические данные K-line. Формат ввода: «символ|период|дни»
    period: daily/weekly/monthly(日/周/月), days: 最近多少个周期(默认60)
Пример: «600519|ежедневно|30»
Источник данных: Сина
    """
print(f" [запрос исторических данных] {query}")

    parts = query.strip().split("|")
    symbol = _resolve_symbol(parts[0].strip())
    period = parts[1].strip() if len(parts) > 1 else "daily"
    try:
        days = int(parts[2]) if len(parts) > 2 else 60
    except ValueError:
        days = 60

    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days * 30)).strftime("%Y%m%d") if period != "daily" else (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

    try:
        sina_code = _to_sina_code(symbol)
        period_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
        ak_period = period_map.get(period, "daily")
        hist = _safe_fetch(ak.stock_zh_a_hist,
                           symbol=symbol, period=ak_period, start_date=start,
                           end_date=end, adjust="qfq")
        if hist is None or hist.empty:
            hist = _safe_fetch(ak.stock_zh_a_daily,
                           symbol=sina_code, start_date=start,
                           end_date=end, adjust="qfq")
        if hist is None or hist.empty:
# Попробуйте источник Tencent
            time.sleep(2)
            hist = ak.stock_zh_a_hist_tx(symbol=sina_code,
                                         start_date=start, end_date=end)
            if hist is None or hist.empty:
return f"Исторические данные для {symbol} не найдены"
# Сопоставление имен столбцов Tencent
            hist = hist.rename(columns={
                "date": "date", "open": "open", "close": "close",
                "high": "high", "low": "low", "amount": "volume"
            })
        elif hist is not None and not hist.empty:
# Унифицировать имена столбцов на английском языке для адаптации к последующей логике
            rename_map = {
                "日期": "date", "开盘": "open", "收盘": "close",
«Самый высокий»: «высокий», «Самый низкий»: «низкий», «Объем торгов»: «объем», «Сумма торгов»: «сумма»
            }
            hist = hist.rename(columns=rename_map)
    except Exception as e:
return f"Не удалось получить исторические данные: {e}"

    if hist is None or hist.empty:
return f"Исторические данные для {symbol} не найдены"

    hist = hist.tail(days)
    latest = hist.iloc[-1]
    first = hist.iloc[0]
    change = (latest["close"] - first["close"]) / first["close"] * 100
    date_col = "date" if "date" in hist.columns else hist.columns[0]
    close_col = "close"

lines = [f"{symbol} ежедневных K строк (рядом с {len(hist)}, {hist.iloc[0][date_col]} ~ {hist.iloc[-1][date_col]})"]
lines.append(f" Изменение диапазона: {change:.2f}%")
lines.append(f" 最新: O={latest['open']:.2f} H={latest['high']:.2f} L={latest['low']:.2f} C={latest[close_col]:.2f}")
lines.append(f" Самый высокий диапазон: {hist['high'].max():.2f} Самый низкий диапазон: {hist['low'].min():.2f}")
    closes = [f"{x:.2f}" for x in hist[close_col].tail(5).tolist()]
    lines.append(f"  近5日收盘: {' -> '.join(closes)}")

    return "\n".join(lines)


def get_financial_data(symbol: str) -> str:
    """
Получите основные финансовые показатели. Ввод: код акции (например, «600519»).
    数据源: akshare stock_financial_abstract (Sina)
Доходность: ключевые показатели, такие как чистая прибыль, выручка, рентабельность собственного капитала, валовая прибыль, темпы роста и т. д.
    """
print(f" [запрос финансовых данных] {symbol}")
    symbol = symbol.strip()

    try:
        df = _safe_fetch(ak.stock_financial_abstract, symbol=symbol)
        if df is None or df.empty:
return f"Финансовые данные для {symbol} не найдены"
    except Exception as e:
return f"Не удалось получить финансовые данные: {e}"

# Получить два последних столбца квартальных данных
    date_cols = [c for c in df.columns if c.isdigit() and len(c) == 8]
    if len(date_cols) < 2:
return f"{symbol} Недостаточно финансовых данных"
    latest_col = date_cols[0]
    prev_col = date_cols[1]

    lines = [f"{symbol} 核心财务数据 (最新: {latest_col} vs 上期: {prev_col})"]

#Сопоставление ключевых показателей
    key_metrics = [
(«Чистая прибыль, приходящаяся на материнскую компанию», «Чистая прибыль, приходящаяся на материнскую компанию», «Юани»),
(«общий операционный доход», «общий операционный доход», «юань»),
(«Чистая прибыль», «Чистая прибыль», «Юань»),
(«Вычет нечистой прибыли», «Вычет нечистой прибыли», «Юани»),
(«Базовая прибыль на акцию», «Базовая прибыль на акцию», «Юани»),
(«Чистые активы на акцию», «Чистые активы на акцию», «Юани»),
(«ROE», «ROE», «%»),
(«Рентабельность совокупных активов», «Рентабельность совокупных активов», «%»),
(«Валовая прибыль от продаж», «Валовая прибыль от продаж», «%»),
(«Чистая прибыль от продаж», «Чистая прибыль от продаж», «%»),
(«Рост выручки в годовом исчислении», «Рост совокупного операционного дохода в годовом исчислении», «%»),
(«Чистая прибыль, причитающаяся акционерам материнской компании, увеличилась по сравнению с аналогичным периодом прошлого года», «Чистая прибыль, приходящаяся на акционеров материнской компании, увеличилась по сравнению с аналогичным периодом прошлого года», «%»),
(«Коэффициент актив-пассив», «Соотношение актив-пассив», «%»),
(«коэффициент текущей ликвидности», «коэффициент текущей ликвидности», «»),
(«коэффициент быстрой ликвидности», «коэффициент быстрой ликвидности», «»),
    ]

    for label, metric_name, unit in key_metrics:
строка = df[df["метрика"] == имя_метрики]
        if row.empty:
            continue
        val = row[latest_col].values[0]
        prev_val = row[prev_col].values[0] if prev_col in row.columns else None

        if pd.isna(val):
            continue

        try:
            if unit == "元" and abs(float(val)) > 1e8:
val_str = f"{float(val)/1e8:.2f} миллиард"
                if prev_val is not None and not pd.isna(prev_val) and abs(float(prev_val)) > 1e8:
                    prev_str = f"{float(prev_val)/1e8:.2f}亿"
                else:
                    prev_str = None
            elif unit == "%":
                val_str = f"{float(val):.2f}%"
                prev_str = f"{float(prev_val):.2f}%" if prev_val is not None and not pd.isna(prev_val) else None
            else:
                val_str = f"{float(val):.4f}"
                prev_str = f"{float(prev_val):.4f}" if prev_val is not None and not pd.isna(prev_val) else None
        except (ValueError, TypeError):
            val_str = str(val)
            prev_str = str(prev_val) if prev_val is not None else None

        line = f"  {label}: {val_str}"
        if prev_str:
            try:
                trend = "[+]" if float(val) > float(prev_val) else "[-]"
                line += f" {trend} (上期: {prev_str})"
            except (ValueError, TypeError):
строка += f" (последний выпуск: {prev_str})"
        lines.append(line)

    return "\n".join(lines)


def calc_indicators(query: str) -> str:
    """
Рассчитать технические индикаторы. Формат ввода: «символ|ежедневно|дни»
    返回: MA5/10/20/60, MACD(DIF/DEA/柱), RSI14, 布林带, 支撑压力位。
Источник данных: Сина
    """
print(f" [расчетные технические индикаторы] {query}")

    parts = query.strip().split("|")
    symbol = parts[0].strip()
    try:
        days = min(int(parts[2]), 365) if len(parts) > 2 else 120
    except ValueError:
        days = 120

    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")

    try:
        sina_code = _to_sina_code(symbol)
        df = _safe_fetch(ak.stock_zh_a_daily,
                         symbol=sina_code, start_date=start,
                         end_date=end, adjust="qfq")
        if df is None or df.empty:
# Попробуйте новый запасной вариант API
            df = _safe_fetch(ak.stock_zh_a_hist, symbol=symbol, period="daily", start_date=start, end_date=end, adjust="qfq")

        if df is None or df.empty:
return f"Для {symbol} данные не найдены"

        if df is not None and not df.empty:
# Унифицировать имена столбцов на английском языке для адаптации к последующей логике
            rename_map = {
                "日期": "date", "开盘": "open", "收盘": "close",
«Самый высокий»: «высокий», «Самый низкий»: «низкий», «Объем торгов»: «объем», «Сумма торгов»: «сумма»
            }
            df = df.rename(columns=rename_map)
    except Exception as e:
return f"Не удалось получить данные: {e}"

    df = df.tail(days).reset_index(drop=True)
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    latest_close = close.iloc[-1]

    lines = [f"{symbol} 技术指标分析 (基于近{len(df)}条日K线)"]
lines.append(f" последняя цена закрытия: {latest_close:.2f}")
    lines.append("")

# --- Скользящее среднее ---
lines.append("--- Скользящее среднее ---")
    ma_signals = []
    for ma in [5, 10, 20, 60]:
        if len(close) >= ma:
            ma_val = close.rolling(window=ma).mean().iloc[-1]
            relation = "[+]多头" if latest_close > ma_val else "[-]空头"
            lines.append(f"  MA{ma:>2}: {ma_val:.2f}  ({relation})")
            ma_signals.append(latest_close > ma_val)
    if ma_signals:
        bullish = sum(ma_signals)
        lines.append(f"  均线综合: {bullish}/{len(ma_signals)} 条支撑  "
f"({'бычий', если бычий >= 3, иначе 'короткий', если бычий <= 1, иначе 'шок'})"))

    # --- MACD ---
    lines.append("")
    lines.append("--- MACD (12,26,9) ---")
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9).mean()
    macd_bar = 2 * (dif - dea)

    lines.append(f"  DIF: {dif.iloc[-1]:.3f}  DEA: {dea.iloc[-1]:.3f}")
    bar_color = "红柱" if macd_bar.iloc[-1] > 0 else "绿柱"
    lines.append(f"  MACD柱: {macd_bar.iloc[-1]:.3f}  ({bar_color})")

    if len(dif) >= 2:
        if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
lines.append("[!] Сигнал: Золотой крест (сигнал на покупку)")
        elif dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2]:
lines.append("[!] Сигнал: Крест Смерти (Сигнал продажи)")
        else:
            trend = "多头" if dif.iloc[-1] > dea.iloc[-1] else "空头"
lines.append(f" Тренд: {trend}продолжается")
    else:
        trend = "多头" if dif.iloc[-1] > dea.iloc[-1] else "空头"
lines.append(f" Тренд: {trend}продолжается")

    # --- RSI ---
    lines.append("")
    lines.append("--- RSI (14) ---")
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1/14).mean()
    avg_loss = loss.ewm(alpha=1/14).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]

    if rsi_val > 80:
rsi_status = "Серьезно перекупленность"
    elif rsi_val > 70:
rsi_status = "Область перекупленности"
    elif rsi_val < 20:
rsi_status = "Серьезно перепроданность"
    elif rsi_val < 30:
rsi_status = "область перепроданности"
    else:
rsi_status = "Нейтрально"
    lines.append(f"  RSI: {rsi_val:.1f} ({rsi_status})")

# --- Полосы Боллинджера ---
    lines.append("")
lines.append("--- Полосы Боллинджера (20,2) ---")
    bb_mid = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    lines.append(f"  上轨: {bb_upper.iloc[-1]:.2f}")
lines.append(f" посередине рельса: {bb_mid.iloc[-1]:.2f}")
lines.append(f" нижняя направляющая: {bb_lower.iloc[-1]:.2f}")
    bb_pos = (latest_close - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1])
    if bb_pos > 0.9:
lines.append(f"Цена находится вблизи верхней границы полос Боллинджера, обратите внимание на давление")
    elif bb_pos < 0.1:
lines.append(f"Цена находится вблизи нижней границы полос Боллинджера, обратите внимание на поддержку")
    else:
lines.append(f"Цена находится вблизи средней линии полос Боллинджера")

# --- Уровень поддержки/давления ---
    lines.append("")
lines.append("---Ключевая цена ---")
    recent_high = high.tail(20).max()
    recent_low = low.tail(20).min()
    lines.append(f"  近20日最高: {recent_high:.2f} (压力位)")
    lines.append(f"  近20日最低: {recent_low:.2f} (支撑位)")
    if len(close) >= 60:
        ma60 = close.rolling(60).mean().iloc[-1]
        lines.append(f"  MA60: {ma60:.2f} (长期支撑/压力)")

    return "\n".join(lines)


def get_news(symbol: str) -> str:
    """
Получите последние новости. Ввод: код акции (например, «600519»).
Возвращает последние 5 заголовков новостей.
    """
print(f" [новости запроса] {symbol}")
    symbol = symbol.strip()

    try:
        news_df = _safe_fetch(ak.stock_news_em, symbol=symbol)
        if news_df is None or news_df.empty:
return f"Новостей, связанных с {symbol}, не найдено"
    except Exception as e:
return f"Не удалось получить новости: {e}"

    recent = news_df.head(5)
lines = [f"{symbol} Последние новости:"]
    for i, (_, row) in enumerate(recent.iterrows(), 1):
title = row.get("Заголовок новости", "Н/Д")
dt = row.get("Время публикации", "")
content = row.get("Содержание новостей", "")
        summary = content[:80] + "..." if isinstance(content, str) and len(content) > 80 else str(content or "")
        lines.append(f"  {i}. [{dt}] {title}")
        if summary:
            lines.append(f"     {summary}")

    return "\n".join(lines)
