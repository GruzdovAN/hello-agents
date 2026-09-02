"""Детерминированные проверочные инструменты на протоколе Tool HelloAgents 0.2.9."""

from __future__ import annotations

import io
import json
import re
from contextlib import redirect_stdout
from typing import Any

from hello_agents.tools import Tool, ToolParameter, ToolRegistry


REQUIREMENT_DIMENSIONS: dict[str, tuple[tuple[str, ...], str]] = {
    "Цели и ценность": (
        ("цель", "задача", "решить", "ценность", "ради", "проблема", "goal", "value"),
        "Какую проблему решает это требование и какую ценность создаёт успех?",
    ),
    "Целевая аудитория": (
        ("пользователь", "участник", "клиент", "админ", "администратор", "роль", "user", "audience"),
        "Кто будет использовать систему? Что может делать каждая роль?",
    ),
    "Основной объём": (
        ("функци", "поддерж", "может", "нужно", "просмотр", "опублик", "регистр", "управл", "feature"),
        "Что должно быть в первой версии и что явно исключено?",
    ),
    "Ограничения": (
        ("бюджет", "стоимость", "срок", "запуск", "период", "стек", "платформа", "язык"),
        "Жёсткие ограничения по срокам, бюджету, платформе или технологическому стеку?",
    ),
    "Данные и интеграции": (
        ("данн", "база", "интерфейс", "api", "импорт", "экспорт", "сторонн", "синхрон", "integration"),
        "Какие данные сохранять и с какими системами или сервисами интегрироваться?",
    ),
    "Нефункциональные требования": (
        ("конкур", "производ", "безопас", "приват", "доступн", "время отклика", "число", "ёмкость", "performance"),
        "Требования к производительности, ёмкости, безопасности, приватности и доступности?",
    ),
    "Критерии приёмки": (
        ("приёмк", "успех", "пройти", "метрик", "стандарт заверш", "демо", "acceptance"),
        "Какие наблюдаемые и проверяемые условия означают успешную приёмку?",
    ),
}


REQUIRED_REPORT_HEADINGS = (
    "1. Сводка требований",
    "2. Подтверждённая информация",
    "3. Вопросы для уточнения",
    "4. Объём и приоритеты",
    "5. Техническое решение",
    "6. Риски и меры",
    "7. Критерии приёмки",
    "8. Следующие шаги",
)


class RequirementAuditTool(Tool):
    """Сканирует, какие ключевые аспекты покрыты в исходном требовании."""

    def __init__(self) -> None:
        super().__init__(
            name="requirement_audit",
            description=(
                "Проверяет полноту текста требований: покрытые и пропущенные аспекты, уточняющие вопросы; "
                "параметр requirement_text"
            ),
        )

    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="requirement_text",
                type="string",
                description="Исходный текст требований для проверки",
                required=True,
            )
        ]

    def run(self, parameters: dict[str, Any]) -> str:
        requirement_text = parameters.get(
            "requirement_text", parameters.get("input", "")
        )
        if not isinstance(requirement_text, str) or not requirement_text.strip():
            return json.dumps(
                {
                    "ok": False,
                    "error_code": "INVALID_PARAM",
                    "message": "requirement_text должно быть непустой строкой",
                },
                ensure_ascii=False,
            )

        normalized = requirement_text.casefold()
        covered: list[str] = []
        missing: list[str] = []
        evidence: dict[str, list[str]] = {}
        questions: list[str] = []

        for dimension, (keywords, question) in REQUIREMENT_DIMENSIONS.items():
            hits = [keyword for keyword in keywords if keyword.casefold() in normalized]
            if hits:
                covered.append(dimension)
                evidence[dimension] = hits
            else:
                missing.append(dimension)
                questions.append(question)

        total = len(REQUIREMENT_DIMENSIONS)
        coverage = round(len(covered) / total * 100)
        summary = (
            f"Первичная проверка полноты: {coverage}% ({len(covered)}/{total} аспектов).\n"
            f"Покрыто: {', '.join(covered) if covered else 'нет'}.\n"
            f"Дополнить: {', '.join(missing) if missing else 'нет'}."
        )
        return json.dumps(
            {
                "ok": True,
                "summary": summary,
                "coverage_percent": coverage,
                "covered_dimensions": covered,
                "missing_dimensions": missing,
                "evidence_keywords": evidence,
                "clarifying_questions": questions,
            },
            ensure_ascii=False,
            indent=2,
        )


class ReportQualityTool(Tool):
    """Проверяет, что финальный отчёт содержит восемь обязательных разделов шаблона."""

    def __init__(self) -> None:
        super().__init__(
            name="report_quality_check",
            description=(
                "Проверяет структуру отчёта уточнения требований, содержание разделов и маркеры уточнения; "
                "параметр report_text"
            ),
        )

    def get_parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="report_text",
                type="string",
                description="Отчёт уточнения требований в формате Markdown",
                required=True,
            )
        ]

    def run(self, parameters: dict[str, Any]) -> str:
        report_text = parameters.get("report_text", parameters.get("input", ""))
        if not isinstance(report_text, str) or not report_text.strip():
            return json.dumps(
                {
                    "ok": False,
                    "error_code": "INVALID_PARAM",
                    "message": "report_text должно быть непустой строкой",
                },
                ensure_ascii=False,
            )

        heading_matches = list(
            re.finditer(r"^##\s+(.+?)\s*$", report_text, flags=re.MULTILINE)
        )
        headings = {match.group(1).strip() for match in heading_matches}
        missing = [heading for heading in REQUIRED_REPORT_HEADINGS if heading not in headings]

        section_content: dict[str, str] = {}
        for index, match in enumerate(heading_matches):
            heading = match.group(1).strip()
            content_end = (
                heading_matches[index + 1].start()
                if index + 1 < len(heading_matches)
                else len(report_text)
            )
            section_content[heading] = report_text[match.end() : content_end].strip()
        empty = [
            heading
            for heading in REQUIRED_REPORT_HEADINGS
            if heading in headings and not section_content.get(heading)
        ]

        body_without_headings = re.sub(
            r"^#{1,6}\s+.*$", "", report_text, flags=re.MULTILINE
        )
        has_pending_markers = any(
            marker in body_without_headings.casefold()
            for marker in ("требует уточнения", "предположение", "рекомендация", "предполага")
        )

        total = len(REQUIRED_REPORT_HEADINGS)
        heading_score = (total - len(missing)) / total * 50
        content_score = (total - len(missing) - len(empty)) / total * 40
        score = round(
            heading_score + content_score + (10 if has_pending_markers else 0)
        )
        summary = (
            f"Оценка структуры отчёта: {score}/100."
            + (f" Отсутствуют разделы: {', '.join(missing)}." if missing else " Все восемь разделов присутствуют.")
            + (f" Пустые разделы: {', '.join(empty)}." if empty else " Все разделы содержат текст.")
            + (" Маркеры уточнения выделены." if has_pending_markers else " Маркеры уточнения/предположения/рекомендации не найдены.")
        )
        return json.dumps(
            {
                "ok": True,
                "summary": summary,
                "score": score,
                "missing_headings": missing,
                "empty_headings": empty,
                "has_pending_markers": has_pending_markers,
            },
            ensure_ascii=False,
            indent=2,
        )


def create_tool_registry() -> ToolRegistry:
    """Создаёт и регистрирует инструменты HelloAgents для проекта."""

    registry = ToolRegistry()
    # При регистрации 0.2.9 печатает лог с emoji; терминал Windows GBK может не справиться с кодировкой.
    with redirect_stdout(io.StringIO()):
        registry.register_tool(RequirementAuditTool())
        registry.register_tool(ReportQualityTool())
    return registry
