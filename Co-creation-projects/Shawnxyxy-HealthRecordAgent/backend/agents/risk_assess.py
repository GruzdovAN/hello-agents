"""
Агент по оценке рисков для здоровья
"""
import json
from typing import Dict, Any, List
from agents.base import BaseAgent
from core.exceptions import AgentException

class RiskAssessmentAgent(BaseAgent):
    def __init__(self, task_id=None, llm=None):
        super().__init__(name="RiskAssessment", task_id=task_id, llm=llm)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            indicator_results = input_data["indicator_results"]
            if not indicator_results:
поднять AgentException("Отсутствуют результаты анализа индикаторов работоспособности")
            self.set_state("running")

            result = await self._assess_risk(indicator_results)

            self.set_state("completed")
            return result
        except Exception as e:
            self.set_state("error")
поднять AgentException(f"Ошибка выполнения RiskAssessmentAgent: {str(e)}")

    async def _assess_risk(self, indicator_results: Dict[str, Any]) -> Dict[str, Any]:
        risk_prompt = f"""
Вы профессиональный эксперт по оценке рисков для здоровья.

Ниже приведены результаты анализа показателей здоровья пользователя (анализ выполнен другими агентами):
{indicator_results}

Пожалуйста, выполните следующие задания:
1. Комплексная оценка общего уровня риска для здоровья пользователя (низкий/средний/высокий)
2. Перечислите основные факторы риска (не более 5).
3. Предположите возможные потенциальные риски для здоровья или направления заболевания.
4. 给出你评估的置信度（0~1 之间的小数）

Пожалуйста, верните его в формате JSON, например:
{{
  "overall_risk_level": "medium",
"risk_factors": ["Высокий уровень холестерина", "Недостаток сна"],
"potential_conditions": ["Риск сердечно-сосудистых заболеваний"],
  "confidence": 0.78
}}
"""
        response = await self.think(risk_prompt)

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            result = {
"summary": "Парсинг не удался, верните исходный результат",
                "raw_response": response
            }

        self.set_state("completed")
        return result
    
    def get_required_fields(self) -> list[str]:
        return ["age", "weight", "height", "blood_pressure"]