"""Лёгкий поиск только через DuckDuckGo без лишних подсказок Tavily/SerpAPI при инициализации SearchTool."""

from __future__ import annotations


def duckduckgo_search_text(
    query: str,
    *,
    max_results: int = 4,
    max_body_chars: int = 600,
) -> str:
    query = (query or "").strip()
    if not query:
        return "【Поиск】Запрос пуст."

    try:
        from ddgs import DDGS
    except ImportError:
        return "【Поиск】Пакет duckduckgo-search не установлен. Выполните: pip install duckduckgo-search"

    try:
        with DDGS(timeout=15) as client:  # type: ignore[call-arg]
            rows = client.text(query, max_results=max_results, backend="duckduckgo")
    except Exception as e:  # pragma: no cover
        return f"【Поиск】Ошибка запроса DuckDuckGo: {e}"

    if not rows:
        return "【Поиск】Результатов нет."

    lines: list[str] = ["【Сводка поиска DuckDuckGo】"]
    for i, entry in enumerate(rows, 1):
        url = entry.get("href") or entry.get("url") or ""
        title = entry.get("title") or url or "(без заголовка)"
        body = entry.get("body") or entry.get("content") or ""
        if len(body) > max_body_chars:
            body = body[:max_body_chars] + "…"
        lines.append(f"{i}. {title}\n   {url}\n   {body}")
    return "\n\n".join(lines)
