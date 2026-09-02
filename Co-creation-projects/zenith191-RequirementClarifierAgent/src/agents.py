"""Сборка командной группы на официальных SimpleAgent HelloAgents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hello_agents import Config, HelloAgentsLLM, SimpleAgent
from hello_agents.tools import ToolRegistry

from .config import LLMSettings
from .prompts import (
    REPORT_SYNTHESIZER_PROMPT,
    REQUIREMENT_ANALYST_PROMPT,
    RISK_REVIEWER_PROMPT,
    SOLUTION_ARCHITECT_PROMPT,
)


class AgentLike(Protocol):
    """Для подмены в офлайн-тестах; в продакшене всегда SimpleAgent."""

    def run(self, input_text: str, **kwargs: object) -> str:
        """Обрабатывает ввод этапа и возвращает текст."""

        ...


@dataclass(frozen=True)
class AgentTeam:
    """Четыре роли в последовательной кооперации."""

    analyst: AgentLike
    architect: AgentLike
    reviewer: AgentLike
    synthesizer: AgentLike


def build_agent_team(settings: LLMSettings, tool_registry: ToolRegistry) -> AgentTeam:
    """Создаёт четыре официальные SimpleAgent с одним экземпляром HelloAgentsLLM."""

    settings.validate()
    llm = HelloAgentsLLM(
        model=settings.model,
        api_key=settings.api_key,
        base_url=settings.base_url,
        temperature=settings.temperature,
        timeout=settings.timeout,
    )
    config = Config(debug=False, max_history_length=20)

    return AgentTeam(
        analyst=SimpleAgent(
            name="Аналитик требований",
            llm=llm,
            system_prompt=REQUIREMENT_ANALYST_PROMPT,
            config=config,
            tool_registry=tool_registry,
        ),
        architect=SimpleAgent(
            name="Архитектор решений",
            llm=llm,
            system_prompt=SOLUTION_ARCHITECT_PROMPT,
            config=config,
        ),
        reviewer=SimpleAgent(
            name="Ревьюер рисков",
            llm=llm,
            system_prompt=RISK_REVIEWER_PROMPT,
            config=config,
        ),
        synthesizer=SimpleAgent(
            name="Интегратор отчёта",
            llm=llm,
            system_prompt=REPORT_SYNTHESIZER_PROMPT,
            config=config,
            tool_registry=tool_registry,
        ),
    )
