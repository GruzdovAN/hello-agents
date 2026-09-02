from __future__ import annotations

from backend.models import AgentKind, AgentProfile


def default_profiles() -> list[AgentProfile]:
    return [
        AgentProfile(
            agent_id="deep_research",
            name="Поисковик",
            kind=AgentKind.research,
            description="Автоматически ищет в интернете и формирует исследовательский отчёт.",
            system_prompt="Coordinate research tasks and produce a report.",
            tools=["web_search", "notes", "summarizer"],
            enabled=True,
        ),
        AgentProfile(
            agent_id="rss_digest",
            name="Новостник",
            kind=AgentKind.research,
            description="Загружает RSS-ленты и формирует краткую сводку новостей.",
            system_prompt="Collect RSS updates, summarize them in Chinese, and return a daily digest.",
            tools=["rss", "article_extractor", "translator", "html_digest"],
            enabled=True,
        ),
    ]
