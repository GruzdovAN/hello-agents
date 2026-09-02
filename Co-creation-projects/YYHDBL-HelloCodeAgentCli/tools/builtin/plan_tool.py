from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional

from core.llm import HelloAgentsLLM
from tools.base import Tool, ToolParameter


class PlanTool(Tool):
    """Инструмент планирования (опциональный)

    Используется, когда пользователь явно просит или задача явно требует
    многошагового выполнения. В ReAct вызывайте по необходимости:
    plan[{"goal":"..."}] или plan[текст цели]
    """

    def __init__(self, llm: HelloAgentsLLM, prompt_path: Optional[str] = None):
        super().__init__(name="plan", description="Генерирует исполнимый план (вызывать только при необходимости)")
        self.llm = llm
        self.prompt_path = Path(prompt_path).resolve() if prompt_path else None

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="goal",
                type="string",
                description="Цель плана (например: проанализировать структуру проекта и описать роли модулей)",
                required=True,
            ),
            ToolParameter(
                name="constraints",
                type="string",
                description="Дополнительные ограничения (опционально)",
                required=False,
            ),
            ToolParameter(
                name="output",
                type="string",
                description="Формат вывода: markdown|json (по умолчанию markdown)",
                required=False,
                default="markdown",
            ),
        ]

    def run(self, parameters: Dict[str, Any]) -> str:
        if not self.validate_parameters(parameters):
            return "❌ Ошибка проверки параметров: отсутствует goal"

        goal = str(parameters.get("goal", "")).strip()
        constraints = parameters.get("constraints")
        output = str(parameters.get("output", "markdown")).strip() or "markdown"

        if not goal:
            return "❌ goal не может быть пустым"

        prompt = ""
        if self.prompt_path and self.prompt_path.exists():
            prompt = self.prompt_path.read_text(encoding="utf-8")
        else:
            prompt = (
                "Вы — помощник по планированию. Выведите исполнимый план (5–12 шагов) "
                "с разделами Risks и Validation."
            )

        user_msg = f"Цель: {goal}\nОжидаемый формат вывода: {output}"
        if constraints:
            user_msg += f"\nОграничения: {constraints}"

        resp = self.llm.invoke(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=800,
        )
        return resp or ""
