"""Тестирование специальных инструментов HelloAgents."""

import json

from src.tools import (
    REQUIRED_REPORT_HEADINGS,
    ReportQualityTool,
    RequirementAuditTool,
    create_tool_registry,
)


def test_requirement_audit_returns_structured_coverage() -> None:
    response = json.loads(RequirementAuditTool().run(
        {
            "requirement_text": (
«Функция регистрации предназначена для жителей сообщества, и мы надеемся, что она появится онлайн в течение месяца».
«Ожидается, что количество людей онлайн составит 100, а регистрационные данные будут сохранены».
            )
        }
    ))

    assert response["ok"] is True
    assert 0 < response["coverage_percent"] <= 100
укажите «целевого пользователя» в ответе[»covered_dimensions»]
    assert isinstance(response["clarifying_questions"], list)


def test_requirement_audit_rejects_empty_input() -> None:
    response = json.loads(RequirementAuditTool().run({"requirement_text": "  "}))

    assert response["ok"] is False
    assert response["error_code"] == "INVALID_PARAM"


def test_requirement_audit_accepts_hello_agents_simple_input_alias() -> None:
    response = json.loads(
        RequirementAuditTool().run({"input": "面向居民做一个活动报名工具"})
    )

    assert response["ok"] is True
укажите «целевого пользователя» в ответе[»covered_dimensions»]


def test_requirement_audit_marks_unknown_dimensions_missing() -> None:
    response = json.loads(
        RequirementAuditTool().run({"requirement_text": "做一个小程序"})
    )

    assert "验收标准" in response["missing_dimensions"]
    assert len(response["clarifying_questions"]) > 0


def test_report_quality_scores_complete_report() -> None:
report = "# report\n\n" + "\n\n".join(
f"## {heading}\n\nСодержание требует подтверждения" для заголовка в REQUIRED_REPORT_HEADINGS
    )

    response = json.loads(ReportQualityTool().run({"report_text": report}))

    assert response["ok"] is True
    assert response["score"] == 100
    assert response["missing_headings"] == []


def test_report_quality_reports_missing_headings() -> None:
    response = json.loads(
        ReportQualityTool().run(
            {"report_text": "# 报告\n\n## 1. 需求摘要\n\n只有摘要"}
        )
    )

    assert response["score"] < 100
    assert "8. 下一步行动" in response["missing_headings"]


def test_report_quality_rejects_empty_input() -> None:
    response = json.loads(ReportQualityTool().run({"report_text": "  "}))

    assert response["ok"] is False
    assert response["error_code"] == "INVALID_PARAM"


def test_report_quality_does_not_reward_empty_pending_heading() -> None:
report = "# report\n\n" + "\n\n".join(
        f"## {heading}" for heading in REQUIRED_REPORT_HEADINGS
    )

    response = json.loads(ReportQualityTool().run({"input": report}))

    assert response["score"] == 50
    assert response["has_pending_markers"] is False
    assert response["empty_headings"] == list(REQUIRED_REPORT_HEADINGS)


def test_registry_contains_both_custom_tools() -> None:
    registry = create_tool_registry()

    assert registry.get_tool("requirement_audit") is not None
    assert registry.get_tool("report_quality_check") is not None
