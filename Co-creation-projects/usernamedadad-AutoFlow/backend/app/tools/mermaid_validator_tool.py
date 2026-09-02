import re
from typing import Any, Dict, List

from hello_agents.tools.base import Tool, ToolParameter
from hello_agents.tools.response import ToolResponse
from hello_agents.tools.errors import ToolErrorCode


MERMAID_PREFIXES = (
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "erDiagram",
    "journey",
    "gantt",
    "pie",
    "gitGraph",
    "mindmap",
    "timeline",
)


class MermaidValidatorTool(Tool):
    def __init__(self):
        super().__init__(
            name="MermaidValidatorTool",
            description="Проверяет и исправляет код Mermaid, возвращает код для рендеринга",
        )

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="Код Mermaid для проверки",
                required=True,
            )
        ]

    def run(self, parameters: Dict[str, Any]) -> ToolResponse:
        code = str(parameters.get("code", "")).strip()
        if not code:
            return ToolResponse.error(
                code=ToolErrorCode.INVALID_PARAM,
                message="Параметр code не может быть пустым",
            )

        normalized = self._normalize(code)
        valid, errors = self._validate_structure(normalized)

        if valid:
            return ToolResponse.success(
                text=f"VALID\n{normalized}",
                data={"valid": True, "fixed_code": normalized, "errors": []},
            )

        return ToolResponse.partial(
            text=f"INVALID\n{normalized}\nОшибка: {'; '.join(errors)}",
            data={"valid": False, "fixed_code": normalized, "errors": errors},
        )

    def _normalize(self, code: str) -> str:
        code = code.strip()
        code = code.replace("```mermaid", "").replace("```", "").strip()
        code = code.replace("→", "-->")

        lines = [ln.rstrip() for ln in code.splitlines() if ln.strip()]
        if not lines:
            return "flowchart TD\n    A[пустая диаграмма]"

        first = lines[0].strip()
        if not first.startswith(MERMAID_PREFIXES):
            # Запасной вариант — flowchart
            lines.insert(0, "flowchart TD")

        return "\n".join(lines)

    def _validate_structure(self, code: str):
        errors = []
        lines = code.splitlines()

        if not lines:
            return False, ["Код пуст"]

        first = lines[0].strip()
        if not first.startswith(MERMAID_PREFIXES):
            errors.append("Отсутствует объявление типа диаграммы Mermaid")

        bracket_pairs = [("(", ")"), ("[", "]"), ("{", "}")]
        for left, right in bracket_pairs:
            if code.count(left) != code.count(right):
                errors.append(f"Несовпадение скобок: {left}{right}")

        # Типичная ошибка flowchart: только объявление без узлов
        if first.startswith(("flowchart", "graph")):
            has_node = any(re.search(r"\w+\s*-->|\w+\[|\w+\(|\w+\{", ln) for ln in lines[1:])
            if not has_node:
                errors.append("В flowchart нет узлов или связей")

        return len(errors) == 0, errors
