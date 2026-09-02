"""
Агент по вопросам здоровья
"""

import json
from typing import Dict, Any, List
from agents.base import BaseAgent
from core.exceptions import AgentException

class AdviceAgent(BaseAgent):
    def __init__(self, task_id=None, llm=None):
        super().__init__(name="AdviceAgent",  task_id=task_id, llm=llm)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        self.set_state("running")

        overall_risk_level = input_data.get("overall_risk_level")
        risk_factors = input_data.get("risk_factors", [])
        potential_conditions = input_data.get("potential_conditions", [])
        confidence = input_data.get("confidence", 0.0)
        if isinstance(input_data.get("risk_assessment"), dict):
            ra = input_data["risk_assessment"]
            overall_risk_level = ra.get("overall_risk_level", overall_risk_level)
            risk_factors = ra.get("risk_factors", risk_factors)
            potential_conditions = ra.get("potential_conditions", potential_conditions)
            confidence = ra.get("confidence", confidence)
извлекаемая_память = str(input_data.get("полученная_память") или "(Пока нет вызванной памяти)")

        prompt = self._build_prompt(
            overall_risk_level,
            risk_factors,
            potential_conditions,
            confidence,
            retrieved_memory,
        )

        response = await self.think(prompt)

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
"summary": "Парсинг не удался, верните исходный результат",
                "raw_response": response
            }

        self.set_state("completed")
        return result

    def _build_prompt(
        self,
        overall_risk_level: str,
        risk_factors: List[str],
        potential_conditions: List[str],
        confidence: float,
        retrieved_memory: str,
    ) -> str:
        return f"""
Вы профессиональный помощник по управлению здравоохранением.
Пожалуйста, сформулируйте разумные и практические рекомендации для пользователей на основе следующих результатов оценки риска для здоровья.

Результаты оценки риска для здоровья:
– Общий уровень риска: {overall_risk_level}.
- 风险因素：{risk_factors}
– Возможные заболевания: {potential_conditions}.
- Оценить уверенность: {confidence}

Восстановление исторической памяти (RAG):
{retrieved_memory}

Пожалуйста, следуйте этим рекомендациям:
- Отсутствие медицинского диагноза.
- Рекомендации должны быть сосредоточены на образе жизни, профилактике, мониторинге и медицинских советах.
- Предложения должны быть конкретными и реализуемыми.
- Настройте приоритет рекомендаций в зависимости от уровня риска.

Пожалуйста, верните его в формате JSON, например:
{{
  "advice": [
    {{
"target": "<соответствующий фактор риска>",
"category": "Образ жизни | Диета | Физические упражнения | Медицинские консультации | Мониторинг",
"suggestion": "<Конкретные предложения по исполняемым файлам>",
      "priority": "high | medium | low"
    }}
  ],
"overall_tone": "<Общий стиль предложения, например: консервативное/активное вмешательство>"
}}
"""

    def get_required_fields(self) -> list[str]:
        return [
            "risk_level",
            "risk_factors"
        ]
        