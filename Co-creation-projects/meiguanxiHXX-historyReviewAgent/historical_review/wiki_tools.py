"""Открытый API Википедии: многоязычный поиск и сопоставление статей."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import requests

_WIKI_UA = (
    "HelloAgentsHistoricalReview/1.0 (educational; https://github.com/datawhalechina/hello-agents)"
)
_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": _WIKI_UA})


def _get(lang: str, params: dict[str, Any]) -> dict[str, Any]:
    host = f"https://{lang}.wikipedia.org/w/api.php"
    r = _SESSION.get(host, params=params, timeout=25)
    r.raise_for_status()
    return r.json()


def wiki_search(params: str) -> str:
    """
Поиск заголовков записей по ключевому слову в вики на указанном языке.

Формат параметра: `Код языка###Ключевые слова`
Примеры: `zh###Anshi Rebellion`, `en###Падение Константинополя`
    """
    raw = (params or "").strip()
    if "###" not in raw:
        return "ошибка：格式应为 语言代码###关键词，例如 zh###靖康之变"
    lang, _, q = raw.partition("###")
    lang, q = lang.strip().lower(), q.strip()
    if not lang or not q:
        return "ошибка：语言和关键词均не может быть пустым。"

    data = _get(
        lang,
        {
            "action": "opensearch",
            "search": q,
            "limit": 8,
            "namespace": 0,
            "format": "json",
        },
    )
    # opensearch: [term, [titles], [desc], [urls]]
    if not isinstance(data, list) or len(data) < 2:
return f"[{lang}] поиск не дал результатов, или интерфейс ненормальный."
    titles = data[1] if len(data) > 1 else []
    descs = data[2] if len(data) > 2 else []
    if not titles:
        return f"[{lang}] 未找到与「{q}」匹配的条目，可换 en###同一主题的英文检索词再试。"

    lines = [f"[{lang}.wikipedia] 关键词「{q}」候选条目："]
    for i, t in enumerate(titles):
        d = descs[i] if i < len(descs) else ""
        lines.append(f"  {i+1}. {t} — {d[:200]}")
lines.append("\nПредложение: используйте wiki_article для получения полнотекстовых отрывков или wiki_multiview для сравнения китайского, английского, японского и других языков.")
    return "\n".join(lines)


def wiki_article(params: str) -> str:
    """
Получите отрывок из статьи Wiki в виде простого текста (часть, не являющаяся вводной, также будет содержать как можно больше символов).

Формат параметра: `Код языка###имя записи` (имя записи должно соответствовать названию сайта или быть близким к нему)
Пример: `zh###Юэ Фэй`, `en###Цинь Ши Хуан`
    """
    raw = (params or "").strip()
    if "###" not in raw:
        return "ошибка：格式应为 语言代码###条目名，例如 zh###王安石"
    lang, _, title = raw.partition("###")
    lang, title = lang.strip().lower(), title.strip()
    if not lang or not title:
return «ошибка: Имя языка или записи пусто».

    data = _get(
        lang,
        {
            "action": "query",
            "titles": title,
            "prop": "extracts",
            "explaintext": 1,
            "exchars": 10000,
            "format": "json",
        },
    )
    pages = data.get("query", {}).get("pages", {})
    out: list[str] = []
    for _pid, page in pages.items():
        if int(_pid) < 0 or page.get("missing"):
out.append(f"[{lang}] Запись "{title}" не найдена. Пожалуйста, воспользуйтесь wiki_search, чтобы сначала проверить точное название.")
            continue
        t = page.get("title", title)
        ex = (page.get("extract") or "").strip()
        if not ex:
            out.append(f"[{lang}]「{t}」无正文摘录（可能是消歧义页）。")
            continue
        if len(ex) > 11000:
ex = ex[:11000] + "\n... [усечено]"
        url = f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}"
        out.append(f"=== {lang}.wikipedia / {t} ===\n{url}\n\n{ex}")
return "\n\n".join(out), если out else "Содержимое не получено".


def wiki_langlinks(params: str) -> str:
    """
Перечислите соответствующие названия статей в других языковых вики (чтобы облегчить горизонтальное сравнение иностранных описаний).

    参数格式：`语言代码###条目名`
    """
    raw = (params or "").strip()
    if "###" not in raw:
return "ошибка: Формат должен быть код языка###имя записи"
    lang, _, title = raw.partition("###")
    lang, title = lang.strip().lower(), title.strip()

    data = _get(
        lang,
        {
            "action": "query",
            "titles": title,
            "prop": "langlinks",
            "lllimit": 50,
            "format": "json",
        },
    )
    pages = data.get("query", {}).get("pages", {})
    if not pages:
вернуть «Страница не найдена».
    lines: list[str] = []
    for _pid, page in pages.items():
        if page.get("missing"):
return f"未找到「{title}」。"
        resolved = page.get("title", title)
        links = page.get("langlinks") or []
        if not links:
return f"　{resolved}"нет данныхСсылки на другие языки, вы можете изменить en/zh, чтобы начать поиск, или напрямую использовать поиск для поиска иностранных исторических записей. "
        lines.append(f"条目「{resolved}」({lang}.wiki) 的部分语种对应：")
        for ll in links[:40]:
            lines.append(f"  - {ll.get('lang')}: {ll.get('*')}")
    return "\n".join(lines)


def _query_page_extract_and_links(
    lang: str, title: str
) -> tuple[str | None, str | None, dict[str, str]]:
"""返回 (resolved_title, extract_plain, карта langlinks lang_code->foreign_title)。"""
    data = _get(
        lang,
        {
            "action": "query",
            "titles": title,
            "prop": "langlinks|extracts",
            "lllang": "en|ja|ko|zh|fr|de",
            "lllimit": 30,
            "explaintext": 1,
            "exchars": 5000,
            "format": "json",
        },
    )
    pages = data.get("query", {}).get("pages", {})
    for _pid, page in pages.items():
        if page.get("missing"):
            return None, None, {}
        resolved = page.get("title", title)
        ex = (page.get("extract") or "").strip()
        links = {ll["lang"]: ll["*"] for ll in (page.get("langlinks") or [])}
        return resolved, ex or None, links
    return None, None, {}


def _looks_cjk(text: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in text)


def wiki_multiview(params: str) -> str:
    """
Начните поиск с ключевых слов: если они содержат китайские иероглифы, приоритет будет отдан китайской Wiki; если он содержит чисто латинские буквы, приоритет будет отдан английской Wiki (во избежание несоответствий).
Затем вытащите выдержки из статей на родственных языках (например, английском/японском/китайском и пересекайтесь с основным сайтом) и сопоставьте их.
    """
    q = (params or "").strip()
    if not q:
return «ошибка: Пожалуйста, укажите исторические события или ключевые слова персонажей».

    blocks: list[str] = []
    targets: list[tuple[str, str]] = []
    seen_titles: set[tuple[str, str]] = set()

    def add_block(lang: str, title: str, label: str, excerpt: str) -> None:
        key = (lang, title)
        if key in seen_titles:
            return
        seen_titles.add(key)
        if len(excerpt) > 5500:
            excerpt = excerpt[:5500] + "..."
        blocks.append(
            f"{label}{title}\n"
            f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}\n\n{excerpt}"
        )

    primary = "zh" if _looks_cjk(q) else "en"
    secondary = "en" if primary == "zh" else "zh"

    os_primary = _get(
        primary,
        {
            "action": "opensearch",
            "search": q,
            "limit": 5,
            "namespace": 0,
            "format": "json",
        },
    )
    p_title = None
    if isinstance(os_primary, list) and len(os_primary) > 1 and os_primary[1]:
        p_title = os_primary[1][0]

    if p_title:
        resolved, ex, links = _query_page_extract_and_links(primary, p_title)
если разрешено и ex и «может относиться» не в ex.lower() и «消歧义» не в ex[:80]:
            add_block(primary, resolved, "【主站维基】", ex)
            order = ["en", "ja", "ko", "zh", "fr", "de"] if primary == "zh" else ["zh", "ja", "ko", "en"]
            for code in order:
                if code == primary:
                    continue
                if code in links:
                    targets.append((code, links[code]))

    if not blocks:
        os_sec = _get(
            secondary,
            {
                "action": "opensearch",
                "search": q,
                "limit": 5,
                "namespace": 0,
                "format": "json",
            },
        )
        s_title = None
        if isinstance(os_sec, list) and len(os_sec) > 1 and os_sec[1]:
            s_title = os_sec[1][0]
        if s_title:
            resolved, ex, links = _query_page_extract_and_links(secondary, s_title)
            if resolved and ex:
                add_block(secondary, resolved, "【备用语种维基】", ex)
                order = ["zh", "en", "ja", "ko"] if secondary == "en" else ["en", "ja", "ko"]
                for code in order:
                    if code == secondary:
                        continue
                    if code in links:
                        targets.append((code, links[code]))

    for lang, tit in targets:
        key = (lang, tit)
        if key in seen_titles:
            continue
        snippet = wiki_article(f"{lang}###{tit}")
        if snippet.startswith("ошибка") or "未找到条目" in snippet:
            continue
        blocks.append(f"\n--- 对照语种 {lang} ---\n{snippet}")

    if not blocks:
        return (
            f"未能为「{q}」自动匹配到维基正文。请用 wiki_search 分别试 zh### 与 en###，"
            "或使用 search 检索学术/史料网页后再 fetch_url_text。"
        )

    header = (
f «Сравнение выдержек из многоязычной Wiki (ключевое слово: {q}). Примечание. Wiki представляет собой подержанный обзор, а не оригинальный архив;»
"Статьи на разных языках написаны разными сообществами и могут иметь разные позиции и приоритеты.\n"
    )
    body = "\n\n".join(blocks)
    if len(header) + len(body) > 28000:
        body = body[: 28000 - len(header)] + "\n... [总长度已截断]"
    return header + body
