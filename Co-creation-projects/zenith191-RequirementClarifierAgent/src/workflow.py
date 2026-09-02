"""Мультиагентный workflow уточнения требований."""

from __future__ import annotations

import json
from dataclasses import dataclass
from html import escape
from pathlib import Path

from hello_agents.tools import ToolRegistry

from .agents import AgentLike, AgentTeam


MAX_REQUIREMENT_LENGTH = 50_000


class WorkflowExecutionError(RuntimeError):
    """Ошибка входа workflow или этапа агента."""


@dataclass(frozen=True)
class WorkflowResult:
    """Сохраняет все промежуточные артефакты для трассировки и тестов."""

    requirement: str
    audit: dict[str, object]
    analysis: str
    architecture: str
    risk_review: str
    report: str
    quality: dict[str, object]


class RequirementClarifierWorkflow:
    """Координирует четыре агента HelloAgents в последовательной кооперации."""

    def __init__(self, team: AgentTeam, tool_registry: ToolRegistry) -> None:
        self.team = team
        self.tool_registry = tool_registry

    def run(self, requirement: str) -> WorkflowResult:
        """Выполняет первичную проверку, три этапа анализа, интеграцию отчёта и проверку структуры."""

        requirement = self._validate_requirement(requirement)
        self._clear_agent_histories()
        try:
            return self._run_validated(requirement)
        finally:
            self._clear_agent_histories()

    def _run_validated(self, requirement: str) -> WorkflowResult:
        """Обрабатывает проверенное требование; очистка истории — на стороне вызывающего."""

        audit = self._run_tool(
            "requirement_audit", {"requirement_text": requirement}, "Первичная проверка"
        )

        analysis = self._run_agent(
            "Анализ требований",
            self.team.analyst,
            "Проанализируй следующее исходное требование с учётом детерминированной первичной проверки.\n\n"
            f"{self._tagged('requirement', requirement)}\n\n"
            f"{self._tagged('audit', json.dumps(audit, ensure_ascii=False, indent=2))}",
        )
        architecture = self._run_agent(
            "Проектирование решения",
            self.team.architect,
            "На основе исходного требования и анализа предложи поставляемое MVP техническое решение.\n\n"
            f"{self._tagged('requirement', requirement)}\n\n"
            f"{self._tagged('analysis', analysis)}",
        )
        risk_review = self._run_agent(
            "Ревью рисков",
            self.team.reviewer,
            "Независимо проверь следующий анализ требований и техническое решение.\n\n"
            f"{self._tagged('requirement', requirement)}\n\n"
            f"{self._tagged('analysis', analysis)}\n\n"
            f"{self._tagged('architecture', architecture)}",
        )
        report = self._run_agent(
            "Интеграция отчёта",
            self.team.synthesizer,
            "Объедини следующие материалы в финальный отчёт уточнения требований и технического решения.\n\n"
            f"{self._tagged('requirement', requirement)}\n\n"
            f"{self._tagged('audit', json.dumps(audit, ensure_ascii=False, indent=2))}\n\n"
            f"{self._tagged('analysis', analysis)}\n\n"
            f"{self._tagged('architecture', architecture)}\n\n"
            f"{self._tagged('risk_review', risk_review)}",
        )

        quality = self._run_tool(
            "report_quality_check", {"report_text": report}, "Проверка отчёта"
        )

        return WorkflowResult(
            requirement=requirement,
            audit=audit,
            analysis=analysis,
            architecture=architecture,
            risk_review=risk_review,
            report=report,
            quality=quality,
        )

    @staticmethod
    def save_report(result: WorkflowResult, output_path: str | Path) -> Path:
        """Сохраняет финальный Markdown-отчёт в UTF-8."""

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(result.report.rstrip() + "\n", encoding="utf-8")
        return path

    @staticmethod
    def _validate_requirement(requirement: str) -> str:
        if not isinstance(requirement, str):
            raise WorkflowExecutionError("Требование должно быть строкой")
        requirement = requirement.strip()
        if not requirement:
            raise WorkflowExecutionError("Требование не может быть пустым")
        if len(requirement) > MAX_REQUIREMENT_LENGTH:
            raise WorkflowExecutionError(
                f"Текст требования не может превышать {MAX_REQUIREMENT_LENGTH} символов"
            )
        return requirement

    @staticmethod
    def _run_agent(stage: str, agent: AgentLike, prompt: str) -> str:
        try:
            response = agent.run(prompt)
        except Exception as exc:
            raise WorkflowExecutionError(f"Этап «{stage}» завершился с ошибкой: {exc}") from exc
        if not isinstance(response, str) or not response.strip():
            raise WorkflowExecutionError(f"Этап «{stage}» вернул пустой результат")
        return response.strip()

    def _run_tool(
        self, name: str, parameters: dict[str, object], stage: str
    ) -> dict[str, object]:
        """Получает инструмент через ToolRegistry и парсит строковый протокол."""

        tool = self.tool_registry.get_tool(name)
        if tool is None:
            raise WorkflowExecutionError(f"{stage}: инструмент {name} не зарегистрирован")
        try:
            raw_result = tool.run(parameters)
        except Exception as exc:
            raise WorkflowExecutionError(f"{stage}: ошибка выполнения инструмента: {exc}") from exc
        try:
            payload = json.loads(raw_result)
        except (TypeError, ValueError) as exc:
            raise WorkflowExecutionError(f"{stage}: инструмент вернул не JSON") from exc
        if not isinstance(payload, dict):
            raise WorkflowExecutionError(f"{stage}: результат инструмента должен быть JSON-объектом")
        if not payload.get("ok"):
            raise WorkflowExecutionError(
                f"{stage}: {payload.get('message', 'неизвестная ошибка инструмента')}"
            )
        return payload

    def _clear_agent_histories(self) -> None:
        """Не переносить предыдущее требование в следующий запуск."""

        for agent in (
            self.team.analyst,
            self.team.architect,
            self.team.reviewer,
            self.team.synthesizer,
        ):
            clear_history = getattr(agent, "clear_history", None)
            if callable(clear_history):
                clear_history()

    @staticmethod
    def _tagged(tag: str, content: str) -> str:
        """Экранирует недоверенный контент, чтобы не подделать границы workflow."""

        return f"<{tag}>\n{escape(content, quote=False)}\n</{tag}>"
