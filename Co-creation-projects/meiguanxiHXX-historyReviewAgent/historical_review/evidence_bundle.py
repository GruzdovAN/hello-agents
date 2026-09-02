"""Опционально: краткая сводка из открытой сети как «историческое приложение» (модель опирается на свои знания)."""

from __future__ import annotations

from .ddg_search import duckduckgo_search_text
from .wiki_tools import wiki_multiview


def build_evidence_bundle(topic: str, *, max_chars: int = 5500) -> str:
    """
    Собирает многоязычные выдержки из Википедии и немного результатов поиска;
    при ошибке возвращает короткое пояснение.
    """
    chunks: list[str] = []
    try:
        w = wiki_multiview(topic.strip())
        if len(w) > 4000:
            w = w[:4000] + "\n... [часть Википедии обрезана]"
        chunks.append("【Многоязычные выдержки Википедии】\n" + w)
    except Exception as e:  # pragma: no cover
        chunks.append(f"【Википедия】Ошибка загрузки: {e}")

    try:
        q = f"{topic.strip()} история заметки легенды споры исследование"
        chunks.append(duckduckgo_search_text(q, max_results=4, max_body_chars=600))
    except Exception as e:  # pragma: no cover
        chunks.append(f"【Поиск】Ошибка: {e}")

    text = "\n\n---\n\n".join(chunks)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n... [общее приложение обрезано]"
    return text
