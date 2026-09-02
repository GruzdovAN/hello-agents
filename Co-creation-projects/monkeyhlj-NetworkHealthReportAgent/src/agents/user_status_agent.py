from __future__ import annotations

from typing import Dict, Optional

from src.agents.base import BaseNetworkAgent


class UserStatusAgent(BaseNetworkAgent):
    def __init__(self) -> None:
        prompt = (
            "Ты агент анализа состояния сетевых пользователей. Вызови инструмент network_data для данных "
            "о подключении терминалов и соответствии политикам; оцени риски терминалов и здоровье доступа."
        )
        super().__init__(name="UserStatusAgent", system_prompt=prompt)

    def analyze(self, terminal_row: Optional[Dict]) -> Dict:
        if not terminal_row:
            return {
                "wired_clients": 0,
                "wireless_clients": 0,
                "unknown_clients": 0,
                "compliant_rate": 0.0,
                "high_risk_terminals": 0,
                "status": "unknown",
                "summary": "Нет данных о соответствии терминалов.",
            }

        compliant_rate = terminal_row["compliant_rate"]
        unknown_clients = terminal_row["unknown_clients"]
        high_risk = terminal_row["high_risk_terminals"]

        status = "healthy"
        if compliant_rate < 0.96 or unknown_clients > 20:
            status = "degraded"
        if compliant_rate < 0.94 or high_risk > 25:
            status = "critical"

        return {
            "wired_clients": terminal_row["wired_clients"],
            "wireless_clients": terminal_row["wireless_clients"],
            "unknown_clients": unknown_clients,
            "compliant_rate": compliant_rate,
            "high_risk_terminals": high_risk,
            "guest_network_ratio": terminal_row["guest_network_ratio"],
            "status": status,
            "summary": (
                f"Доля соответствующих терминалов {compliant_rate:.2%}, высокий риск — {high_risk} шт., "
                f"неизвестных терминалов — {unknown_clients}."
            ),
        }
