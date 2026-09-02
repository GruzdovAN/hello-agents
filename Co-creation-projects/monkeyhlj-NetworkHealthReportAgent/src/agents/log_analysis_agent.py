from __future__ import annotations

from collections import Counter
from typing import Dict, List

from src.agents.base import BaseNetworkAgent


class LogAnalysisAgent(BaseNetworkAgent):
    def __init__(self) -> None:
        prompt = (
            "Ты агент анализа сетевых логов. Вызови network_data для чтения логов; "
            "выдай ключевые алерты, зацепки для root cause и уровень риска."
        )
        super().__init__(name="LogAnalysisAgent", system_prompt=prompt)

    def analyze(self, logs: List[Dict]) -> Dict:
        if not logs:
            return {
                "total_events": 0,
                "critical_events": 0,
                "warning_events": 0,
                "top_event_types": [],
                "summary": "Событий в логах не найдено; проверьте цепочку сбора логов.",
            }

        severity_counter = Counter(log["severity"] for log in logs)
        type_counter = Counter(log["event_type"] for log in logs)
        top_types = [{"event_type": k, "count": v} for k, v in type_counter.most_common(5)]

        risk = "low"
        if severity_counter.get("critical", 0) >= 3:
            risk = "high"
        elif severity_counter.get("warning", 0) >= 3:
            risk = "medium"

        return {
            "total_events": len(logs),
            "critical_events": severity_counter.get("critical", 0),
            "warning_events": severity_counter.get("warning", 0),
            "top_event_types": top_types,
            "risk": risk,
            "summary": (
                f"Недавних записей: {len(logs)}, critical={severity_counter.get('critical', 0)}, "
                f"warning={severity_counter.get('warning', 0)}."
            ),
        }
