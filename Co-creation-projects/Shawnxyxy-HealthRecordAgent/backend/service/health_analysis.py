"""
Службы рабочих процессов аналитики здоровья
Отвечает за последовательное подключение нескольких агентов для выполнения полного анализа отчетов о состоянии.
"""

import asyncio
import logging
from typing import Dict, Any
from uuid import uuid4

from agents.planner import PlannerAgent
from agents.health_indicator import HealthIndicatorAgent
from agents.risk_assess import RiskAssessmentAgent
from agents.advice import AdviceAgent
from agents.report import ReportAgent
from agents.base import create_task, update_agent_state, complete_task
from memory.store import save_completed_report_run
from rag.indexers import index_report_run
from rag.retriever import retrieve

logger = logging.getLogger(__name__)


class HealthAnalysisService:
    def __init__(self, task_id: str | None = None, user_id: str | None = None):
        self.task_id = task_id or str(uuid4())
        self.user_id = user_id
# Инициализация задачи
        create_task(self.task_id, user_id=user_id)

        self.planner = PlannerAgent(task_id=self.task_id)
        self.indicator_agent = HealthIndicatorAgent(task_id=self.task_id)
        self.risk_agent = RiskAssessmentAgent(task_id=self.task_id)
        self.advice_agent = AdviceAgent(task_id=self.task_id)
        self.report_agent = ReportAgent(task_id=self.task_id)

    def _bundle_agent_traces(self, limit_per_agent: int = 80) -> Dict[str, Any]:
"""Этап 3: фрагменты трассировки каждого агента помещаются в базу данных."""
        pairs = [
            ("PlannerAgent", self.planner),
            ("HealthIndicatorAgent", self.indicator_agent),
            ("RiskAssessmentAgent", self.risk_agent),
            ("AdviceAgent", self.advice_agent),
            ("ReportAgent", self.report_agent),
        ]
        out: Dict[str, Any] = {}
        for name, ag in pairs:
            try:
                t = ag.get_traces()
                out[name] = t[-limit_per_agent:] if len(t) > limit_per_agent else list(t)
            except Exception:
                out[name] = []
        return out

    async def run(self, report_text: str, user_id: str) -> Dict[str, Any]:
        """
Выполните полный процесс анализа состояния здоровья
        """

№ 1. Планирование миссии
        update_agent_state(self.task_id, "PlannerAgent", "running")
plan_result = await self.planner.run({"goal": f"Проанализировать следующий отчет о физическом осмотре и сформулировать план выполнения:\n{report_text}"})
        update_agent_state(self.task_id, "PlannerAgent", "completed")

# 2. Анализ показателей здоровья
        update_agent_state(self.task_id, "HealthIndicatorAgent", "running")
        indicator_result = await self.indicator_agent.run({
            "report_text": report_text,
            "plan": plan_result
        })
        update_agent_state(self.task_id, "HealthIndicatorAgent", "completed", partial_report={"indicator_results": indicator_result})

№ 3. Оценка рисков
        update_agent_state(self.task_id, "RiskAssessmentAgent", "running")
        risk_result = await self.risk_agent.run({
            "indicator_results": indicator_result
        })
        update_agent_state(self.task_id, "RiskAssessmentAgent", "completed", partial_report={"risk_assessment": risk_result})

        rag_result = await asyncio.to_thread(
            retrieve,
            user_id,
            {
                "scenario": "health_report_analysis",
                "risk_focus": str(risk_result.get("overall_risk_level", "")),
"query": "Исторические изменения физического обследования и отзывы о реализации",
            },
        )
        retrieved_memory = rag_result.get("summary", "（暂无召回记忆）")

# 4. Создание рекомендаций по вопросам здоровья
        update_agent_state(self.task_id, "AdviceAgent", "running")
        advice_result = await self.advice_agent.run({
            "risk_assessment": risk_result,
            "retrieved_memory": retrieved_memory,
        })
        update_agent_state(self.task_id, "AdviceAgent", "completed", partial_report={"advice": advice_result})


# 5. Краткое содержание отчета
        update_agent_state(self.task_id, "ReportAgent", "running")
        final_report = await self.report_agent.run({
            "indicators": indicator_result,
            "risk_assessment": risk_result,
            "advice": advice_result,
            "retrieved_memory": retrieved_memory,
        })
        update_agent_state(self.task_id, "ReportAgent", "completed")
        complete_task(self.task_id, final_report)

        try:
            traces = self._bundle_agent_traces()
            await asyncio.to_thread(
                save_completed_report_run,
                user_id,
                self.task_id,
                final_report,
                traces,
            )
        except Exception as e:
            logger.exception("写入 SQLite 履历失败（分析结果仍有效）: %s", e)
        try:
            await asyncio.to_thread(index_report_run, self.task_id)
        except Exception as e:
            logger.warning("report run 向量索引失败（不影响返回）: %s", e)

        return self.task_id

# ---------- Временная запись локальной аутентификации ----------

async def _demo():
    demo_text = """
Мужчина, 28 лет, ИМТ 27,3, АД 145/95 мм рт. ст.,
Общий холестерин составил 6,2 ммоль/л, а глюкоза в крови натощак – 6,1 ммоль/л.
        """

    workflow = HealthAnalysisService(user_id="local-demo-user")
    result = await workflow.run(demo_text, user_id="local-demo-user")
    print(result)

if __name__ == "__main__":
    asyncio.run(_demo())
