from __future__ import annotations

import json
import os
from typing import Dict, List

from src.agents.base import BaseNetworkAgent


class NetworkHealthReportAgent(BaseNetworkAgent):
    def __init__(self) -> None:
        prompt = (
            "Ты агент отчёта о здоровье сети. Суммируй анализ логов, состояние устройств и терминалов; "
            "дай оценку здоровья, уровень риска и практические рекомендации."
        )
        super().__init__(name="NetworkHealthReportAgent", system_prompt=prompt)

    def synthesize(
        self,
        site: Dict,
        log_result: Dict,
        device_result: Dict,
        user_result: Dict,
        start_date: str,
        end_date: str,
    ) -> Dict:
        score = 100.0

        score -= min(20.0, log_result.get("critical_events", 0) * 3.0)
        score -= min(10.0, log_result.get("warning_events", 0) * 1.0)
        score -= max(0.0, (1.0 - device_result.get("online_rate", 1.0)) * 200)
        score -= max(0.0, device_result.get("avg_packet_loss", 0.0) * 800)
        score -= max(0.0, (1.0 - user_result.get("compliant_rate", 1.0)) * 150)
        score -= min(10.0, user_result.get("high_risk_terminals", 0) * 0.3)

        score = max(0.0, min(100.0, round(score, 1)))

        if score >= 85:
            level = "healthy"
        elif score >= 70:
            level = "warning"
        else:
            level = "critical"

        recommendations: List[str] = []
        if log_result.get("critical_events", 0) > 0:
            recommendations.append(
                "В приоритете разбор critical-логов по цепочкам и устройствам, root cause и проверка отката изменений."
            )
        if device_result.get("avg_latency_ms", 0) > 18:
            recommendations.append(
                "Для площадок с высокой задержкой — нагрузочные тесты линков и пересмотр QoS для критичных очередей."
            )
        if device_result.get("avg_packet_loss", 0) > 0.01:
            recommendations.append(
                "На портах с потерями — проверка BER и оптики, при необходимости замена кабеля или модуля."
            )
        if user_result.get("compliant_rate", 1.0) < 0.96:
            recommendations.append(
                "Повысить долю compliant-терминалов, ограничить доступ неизвестных и высокорисковых клиентов."
            )
        if not recommendations:
            recommendations.append(
                "Сохранять текущие политики, наблюдать пиковую ёмкость; рекомендуется еженедельный разбор."
            )

        llm_insight = None
        llm_insight_enabled = os.getenv("ENABLE_REPORT_LLM_INSIGHT", "false").lower() in {"1", "true", "yes"}
        if llm_insight_enabled:
            llm_prompt = (
                "Как эксперт по отчётам о здоровье сети, резюмируй состояние площадки. "
                "Три блока: общая оценка, главные риски, приоритеты на неделю."
                "\n\nВходной JSON:\n"
                + json.dumps(
                    {
                        "site": site,
                        "window": {"start_date": start_date, "end_date": end_date},
                        "score": score,
                        "level": level,
                        "log_analysis": log_result,
                        "device_status": device_result,
                        "user_status": user_result,
                        "recommendations": recommendations,
                    },
                    ensure_ascii=False,
                )
            )
            llm_result = self.run_llm(llm_prompt)
            if llm_result:
                llm_insight = llm_result

        return {
            "site": site,
            "window": {"start_date": start_date, "end_date": end_date},
            "health_score": score,
            "health_level": level,
            "summary": (
                f"За период оценка здоровья сети площадки {site['site_name']}: {score}, уровень {level}."
            ),
            "llm_insight": llm_insight,
            "debug": {
                "llm_enabled": self.llm_enabled,
                "mcp_enabled": self.mcp_enabled,
                "tools": self.list_tool_names(),
                "llm_insight_enabled": llm_insight_enabled,
                "llm_insight_used": llm_insight is not None,
            },
            "sections": {
                "log_analysis": log_result,
                "device_status": device_result,
                "user_status": user_result,
            },
            "recommendations": recommendations,
        }
