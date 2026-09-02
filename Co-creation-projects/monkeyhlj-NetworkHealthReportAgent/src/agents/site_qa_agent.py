from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional

from src.agents.base import BaseNetworkAgent


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "outputs"


class SiteQAAgent(BaseNetworkAgent):
    def __init__(self) -> None:
        prompt = (
            "Ты глобальный ассистент по эксплуатации корпоративной сети. Отвечай по переданному контексту. "
            "При возможности вызови network_data для сверки данных. "
            "Ответы краткие, профессиональные, с практическими шагами."
        )
        super().__init__(name="SiteQAAgent", system_prompt=prompt)

    def _build_prompt(
        self,
        question: str,
        context: Dict,
    ) -> str:
        return (
            "Ответь на вопрос пользователя о здоровье корпоративной сети."
            "\n\n[Вопрос]\n"
            f"{question}"
            "\n\n[Контекст JSON]\n"
            f"{json.dumps(context, ensure_ascii=False)}"
            "\n\nОтвет на русском, структура: 1) вывод 2) ключевые факты 3) рекомендуемые действия."
        )

    def _looks_like_report_request(self, question: str) -> bool:
        q = question.lower()
        return any(keyword in q for keyword in ["сгенерир", "экспорт", "скач", "отчёт", "отчет", "недел", "за неделю"])

    def _find_target_site(
        self,
        question: str,
        sites: List[Dict],
        selected_site_id: Optional[str] = None,
    ) -> Optional[Dict]:
        lowered = question.lower()
        for site in sites:
            site_id = str(site.get("site_id", "")).lower()
            site_name = str(site.get("site_name", "")).lower()
            city = str(site.get("city", "")).lower()
            province = str(site.get("province", "")).lower()
            if site_id and site_id in lowered:
                return site
            if site_name and site_name in lowered:
                return site
            if city and city in question:
                return site
            if province and province in question:
                return site

        candidates = re.findall(r"site[-_a-zA-Z0-9]+", lowered)
        for candidate in candidates:
            match = next((site for site in sites if str(site.get("site_id", "")).lower() == candidate), None)
            if match is not None:
                return match

        if selected_site_id:
            selected = next((site for site in sites if site.get("site_id") == selected_site_id), None)
            if selected is not None:
                return selected

        if len(sites) == 1 and self._looks_like_report_request(question):
            return sites[0]

        return None

    def _fallback_answer(
        self,
        question: str,
        sites: List[Dict],
        site_reports: List[Dict],
    ) -> str:
        q = question.strip().lower()
        if "сколько site" in q or "сколько площад" in q or "сколько сайт" in q:
            names = ", ".join([s["site_name"] for s in sites])
            return f"Сейчас {len(sites)} площадок (site): {names}."

        if "шанхай" in q.lower() or "shanghai" in q:
sh_sites = [s вместо s на сайтах, если s.get("city") == "Shanghai" или s.get("province") == "Shanghai City"]
            if not sh_sites:
                return "Площадок в Шанхае нет."
            details = "; ".join([f"{s['site_name']}({s['site_id']})" for s in sh_sites])
            return f"Площадки, связанные с Шанхаем: {len(sh_sites)} — {details}."

        target = None
        for s in sites:
            if s["site_id"] in question or s["site_name"] in question or s.get("city", "") in question:
                target = s
                break

        if target:
            target_report = next((r for r in site_reports if r.get("site", {}).get("site_id") == target["site_id"]), None)
            if target_report:
                device = target_report.get("sections", {}).get("device_status", {})
                return (
                    f"{target['site_name']}: город {target.get('city')}, тип {target.get('site_type')}, "
                    f"критичность {target.get('criticality')}. "
                    f"Доступность устройств {device.get('online_rate', 0) * 100:.2f}%, "
                    f"средняя задержка {device.get('avg_latency_ms', 0)} мс, "
                    f"средние потери {device.get('avg_packet_loss', 0) * 100:.2f}%."
                )

        levels = [r.get("health_level", "unknown") for r in site_reports]
        healthy = len([x for x in levels if x == "healthy"])
        warning = len([x for x in levels if x == "warning"])
        critical = len([x for x in levels if x == "critical"])
        return (
            f"Общий обзор: {len(sites)} площадок, healthy={healthy}, warning={warning}, critical={critical}. "
            "Можно спросить: площадки в Шанхае, детали по site, состояние оборудования на площадке."
        )

    def _summarize_report(self, report: Dict, question: str) -> Optional[str]:
        llm_prompt = (
            "Ты помощник по краткому резюме отчёта о здоровье корпоративной сети. "
            "По входному JSON сформируй русский абзац для первой страницы отчёта: "
            "общий вывод, главные риски, приоритетные действия. "
            "Если в вопросе пользователя есть фокус — учти его."
            "\n\n[Вопрос]\n"
            f"{question}"
            "\n\n[JSON отчёта]\n"
            f"{json.dumps(report, ensure_ascii=False)}"
        )
        return self.run_llm(llm_prompt)

    def _build_report_markdown(
        self,
        site: Dict,
        report: Dict,
        question: str,
        summary: Optional[str],
    ) -> str:
        window = report.get("window", {})
        sections = report.get("sections", {})
        device = sections.get("device_status", {})
        user_status = sections.get("user_status", {})
        log_analysis = sections.get("log_analysis", {})
        recommendations = report.get("recommendations", [])

        lines = [
            f"# Недельный отчёт о здоровье сети: {site.get('site_name', site.get('site_id', 'site'))}",
            "",
            f"- Время генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"- Окно статистики: {window.get('start_date', '')} — {window.get('end_date', '')}",
            f"- ID площадки: {site.get('site_id', '')}",
            f"- Город: {site.get('city', '')}",
            f"- Оценка здоровья: {report.get('health_score', 'N/A')}",
            f"- Уровень: {report.get('health_level', 'N/A')}",
            "",
        ]

        if summary:
            lines.extend([
                "## Резюме LLM",
                summary.strip(),
                "",
            ])

        lines.extend([
            "## Ключевые метрики",
            f"- Доступность устройств: {device.get('online_rate', 0) * 100:.2f}%",
            f"- Средняя задержка: {device.get('avg_latency_ms', 0)} мс",
            f"- Средние потери пакетов: {device.get('avg_packet_loss', 0) * 100:.2f}%",
            f"- Доля compliant-терминалов: {user_status.get('compliant_rate', 0) * 100:.2f}%",
            f"- Терминалы высокого риска: {user_status.get('high_risk_terminals', 0)}",
            "",
            "## Анализ логов",
            log_analysis.get("summary", "Нет резюме по логам."),
            "",
            "## Состояние устройств",
            device.get("summary", "Нет резюме по устройствам."),
            "",
            "## Состояние пользователей",
            user_status.get("summary", "Нет резюме по пользователям."),
            "",
            "## Рекомендации",
        ])

        if recommendations:
            lines.extend([f"{idx + 1}. {item}" for idx, item in enumerate(recommendations)])
        else:
            lines.append("1. Продолжать наблюдение; явных рисков пока не выявлено.")

        lines.extend([
            "",
            "## Вопрос пользователя",
            question,
        ])
        return "\n".join(lines).strip() + "\n"

    def _save_report_artifact(self, site: Dict, start_date: str, end_date: str, content: str) -> Dict:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_site_id = re.sub(r"[^0-9A-Za-z_-]+", "_", str(site.get("site_id", "site")))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_site_id}_{start_date}_{end_date}_{timestamp}.md"
        file_path = OUTPUT_DIR / filename
        file_path.write_text(content, encoding="utf-8")
        return {
            "file_name": filename,
            "file_path": str(file_path),
        }

    def _build_answer_payload(
        self,
        question: str,
        sites: List[Dict],
        site_reports: List[Dict],
        start_date: str,
        end_date: str,
        selected_site_id: Optional[str] = None,
    ) -> Dict:
        context = {
            "scope": "global",
            "window": {"start_date": start_date, "end_date": end_date},
            "site_count": len(sites),
            "sites": sites,
            "reports": site_reports,
            "selected_site_id": selected_site_id,
        }

        prompt = self._build_prompt(question=question, context=context)
        llm_answer: Optional[str] = self.run_llm(prompt)

        target_site = self._find_target_site(question, sites, selected_site_id=selected_site_id)
        is_report_request = self._looks_like_report_request(question)

        if is_report_request and target_site is not None:
            if not self.llm_enabled:
                return {
                    "answer": (
                        "Запрос на недельный отчёт площадки распознан, но LLM не включён — отчёт с моделью не сгенерировать. "
                        "Настройте LLM_API_KEY (или OPENAI_API_KEY) в .env и повторите."
                    ),
                    "artifact": None,
                    "debug": {
                        **self.debug_meta(),
                        "intent": "site_report_requires_llm",
                        "target_site_id": target_site.get("site_id"),
                    },
                }

            target_report = next((r for r in site_reports if r.get("site", {}).get("site_id") == target_site["site_id"]), None)
            if target_report is not None:
                report_summary = self._summarize_report(target_report, question)
                if not report_summary:
                    return {
                        "answer": (
                            "Запрос на отчёт распознан, но вызов LLM не удался — файл недельного отчёта не создан. "
                            "Проверьте настройки LLM и сеть."
                        ),
                        "artifact": None,
                        "debug": {
                            **self.debug_meta(),
                            "intent": "site_report_llm_failed",
                            "target_site_id": target_site.get("site_id"),
                        },
                    }
                answer_text = self._build_report_markdown(
                    site=target_site,
                    report=target_report,
                    question=question,
                    summary=report_summary,
                )
                artifact = self._save_report_artifact(target_site, start_date, end_date, answer_text)
                return {
                    "answer": answer_text,
                    "artifact": artifact,
                    "debug": {
                        **self.debug_meta(),
                        "intent": "site_report_export",
                        "target_site_id": target_site.get("site_id"),
                    },
                }

        answer_text = llm_answer or self._fallback_answer(question=question, sites=sites, site_reports=site_reports)
        return {
            "answer": answer_text,
            "artifact": None,
            "debug": {
                **self.debug_meta(),
                "intent": "general_qa",
                "target_site_id": target_site.get("site_id") if target_site else None,
            },
        }

    def answer_global(
        self,
        question: str,
        sites: List[Dict],
        site_reports: List[Dict],
        start_date: str,
        end_date: str,
    ) -> str:
        return self._build_answer_payload(
            question=question,
            sites=sites,
            site_reports=site_reports,
            start_date=start_date,
            end_date=end_date,
        )["answer"]

    def answer_global_payload(
        self,
        question: str,
        sites: List[Dict],
        site_reports: List[Dict],
        start_date: str,
        end_date: str,
        selected_site_id: Optional[str] = None,
    ) -> Dict:
        return self._build_answer_payload(
            question=question,
            sites=sites,
            site_reports=site_reports,
            start_date=start_date,
            end_date=end_date,
            selected_site_id=selected_site_id,
        )

    def debug_meta(self) -> Dict:
        return {
            "agent": "SiteQAAgent",
            "llm_enabled": self.llm_enabled,
            "mcp_enabled": self.mcp_enabled,
            "tools": self.list_tool_names(),
            "flow": [
                "collect_global_context",
                "build_prompt",
                "try_llm_or_stream",
                "fallback_if_needed",
            ],
        }

    def stream_answer_global(
        self,
        question: str,
        sites: List[Dict],
        site_reports: List[Dict],
        start_date: str,
        end_date: str,
        selected_site_id: Optional[str] = None,
    ) -> Iterator[str]:
        target_site = self._find_target_site(question, sites, selected_site_id=selected_site_id)
        if self._looks_like_report_request(question) and target_site is not None:
            payload = self._build_answer_payload(
                question=question,
                sites=sites,
                site_reports=site_reports,
                start_date=start_date,
                end_date=end_date,
                selected_site_id=selected_site_id,
            )
            yield payload["answer"]
            return

        context = {
            "scope": "global",
            "window": {"start_date": start_date, "end_date": end_date},
            "site_count": len(sites),
            "sites": sites,
            "reports": site_reports,
            "selected_site_id": selected_site_id,
        }
        prompt = self._build_prompt(question=question, context=context)
        stream_iter = self.stream_llm(prompt)
        if stream_iter is not None:
            try:
                for chunk in stream_iter:
                    yield chunk
                return
            except Exception:
                pass

        prompt = self._build_prompt(question=question, context=context)
        yield self.run_llm(prompt) or self._fallback_answer(question=question, sites=sites, site_reports=site_reports)
