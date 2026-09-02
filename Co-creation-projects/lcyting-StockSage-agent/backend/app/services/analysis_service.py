"""
智能股票分析助手 — 分析报告服务层

Координируйте несколько источников данных (рынки, финансы, информация) для создания отчетов об углубленном анализе отдельных акций.
Поддерживает постоянное хранение отчетов и исторические запросы.
"""

import sys
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # backend/app/services -> project root
_BACKEND_DIR = _PROJECT_ROOT
for p in [str(_PROJECT_ROOT), str(_BACKEND_DIR)]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.models.database import async_session_factory
from app.models.report import AnalysisReport
from app.services.market_service import get_stock_quote, get_stock_financial, get_stock_profile
from app.services.news_service import analyze_sentiment


async def generate_analysis_report(
    stock_code: str,
    user_id: str = "default",
    report_type: str = "full",
) -> dict:
"""Создание отчета об углубленном анализе отдельных акций

Собирайте рыночные данные, финансовые данные, профили компаний и информацию общественного мнения и интегрируйте их в структурированные аналитические отчеты.

    Args:
stock_code: 6-значный код акции
user_id: идентификатор пользователя
report_type: тип отчета полный/быстрый

    Returns:
        {
            "success": True/False,
            "report": { ... } or None,
            "error": str or None,
"data_collected": dict # Статус сбора каждого источника данных
        }
    """
    result = {
        "success": False,
        "report": None,
        "error": None,
        "data_collected": {},
    }

    try:
# Этап 1: Сбор рыночных данных
        quote_data = get_stock_quote(stock_code)
        result["data_collected"]["quote"] = quote_data["success"]

        # 阶段2: 收集财务数据
        financial_data = get_stock_financial(stock_code)
        result["data_collected"]["financial"] = financial_data["success"]

# Этап 3: Соберите профиль компании
        profile_data = get_stock_profile(stock_code)
        result["data_collected"]["profile"] = profile_data["success"]

# Этап 4: Сбор данных общественного мнения (асинхронный)
        sentiment_data = analyze_sentiment(stock_code)
        result["data_collected"]["sentiment"] = sentiment_data["success"]

# Этап 5: Создание содержания отчета
        stock_name = _extract_stock_name(profile_data)
        report_content = _build_report_content(
            stock_code, stock_name, report_type,
            quote_data, financial_data, profile_data, sentiment_data
        )
        report_summary = _generate_summary(report_content)

# Этап 6: Отчеты о постоянстве
        async with async_session_factory() as db:
            data_snapshot = json.dumps({
                "quote": {"success": quote_data["success"], "tables": quote_data.get("tables", [])},
                "financial": {"success": financial_data["success"], "tables": financial_data.get("tables", [])},
                "profile": {"success": profile_data["success"], "tables": profile_data.get("tables", [])},
                "sentiment": {
                    "success": sentiment_data["success"],
                    "total_count": sentiment_data.get("total_count", 0),
                },
            }, ensure_ascii=False)

            report = AnalysisReport(
                user_id=user_id,
                stock_code=stock_code,
                stock_name=stock_name,
                report_type=report_type,
                summary=report_summary,
                content=report_content,
                data_snapshot=data_snapshot,
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)

            result["report"] = report.to_dict()
            result["success"] = True
            return result

    except Exception as e:
        result["error"] = str(e)
        return result


async def get_report(report_id: int) -> dict:
"""Получить указанный отчет

    Args:
report_id: идентификатор отчета

    Returns:
        {"success": True/False, "report": {...} or None, "error": str or None}
    """
    result = {"success": False, "report": None, "error": None}

    try:
        async with async_session_factory() as db:
            from sqlalchemy import select
            stmt = select(AnalysisReport).where(AnalysisReport.id == report_id)
            db_result = await db.execute(stmt)
            report = db_result.scalar_one_or_none()

            if report is None:
                result["error"] = f"报告 {report_id} 不存在"
                return result

            result["report"] = report.to_dict()
            result["success"] = True
            return result

    except Exception as e:
        result["error"] = str(e)
        return result


async def get_user_reports(user_id: str = "default", limit: int = 20) -> dict:
    """获取用户的历史分析报告列表

    Args:
user_id: идентификатор пользователя
лимит: максимальное возвращаемое количество

    Returns:
        {"success": True/False, "reports": [...], "total": int, "error": str or None}
    """
    result = {"success": False, "reports": [], "total": 0, "error": None}

    try:
        async with async_session_factory() as db:
            from sqlalchemy import select, func

#Общее количество запросов
            count_stmt = select(func.count(AnalysisReport.id)).where(
                AnalysisReport.user_id == user_id
            )
            db_result = await db.execute(count_stmt)
            total = db_result.scalar() or 0

# Список запросов
            stmt = (
                select(AnalysisReport)
                .where(AnalysisReport.user_id == user_id)
                .order_by(AnalysisReport.created_at.desc())
                .limit(limit)
            )
            db_result = await db.execute(stmt)
            reports = db_result.scalars().all()

            result["reports"] = [r.to_dict() for r in reports]
            result["total"] = total
            result["success"] = True
            return result

    except Exception as e:
        result["error"] = str(e)
        return result


def _extract_stock_name(profile_data: dict) -> str:
"""Извлечение названий акций из данных профиля компании"""
    try:
        tables = profile_data.get("tables", [])
        for table in tables:
            rows = table.get("rows", [])
            for row in rows:
                for key in row:
если в ключе «имя» или «короткое имя»:
                        return str(row[key])
        return ""
    except Exception:
        return ""


def _build_report_content(
    stock_code: str,
    stock_name: str,
    report_type: str,
    quote_data: dict,
    financial_data: dict,
    profile_data: dict,
    sentiment_data: dict,
) -> str:
"""Создание содержимого Markdown отчета"""
    title = stock_name or stock_code
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
lines.append(f"# {title}（{stock_code}）отчет о глубинном анализе")
lines.append(f"**Время генерации**: {сейчас}")
lines.append(f"**Тип отчета**: {'Полный анализ' if report_type == 'полный' else 'Краткий обзор'}")
    lines.append("")
    lines.append("---")
    lines.append("")

# 1. Обзор рынка
lines.append("## 1. Обзор рынка")
    if quote_data.get("success"):
        lines.append(_format_data_section(quote_data))
    else:
        lines.append("> ⚠️ 行情数据获取失败")
        if quote_data.get("error"):
            lines.append(f"> 原因: {quote_data['error']}")
    lines.append("")

№ 2. Финансовый анализ
lines.append("## 2. Финансовый анализ")
    if financial_data.get("success"):
        lines.append(_format_data_section(financial_data))
    else:
        lines.append("> ⚠️ 财务数据获取失败")
        if financial_data.get("error"):
            lines.append(f"> 原因: {financial_data['error']}")
    lines.append("")

№ 3. Профиль компании
lines.append("## 3. Профиль компании")
    if profile_data.get("success"):
        lines.append(_format_data_section(profile_data))
    else:
        lines.append("> ⚠️ 公司概况获取失败")
        if profile_data.get("error"):
            lines.append(f"> 原因: {profile_data['error']}")
    lines.append("")

№ 4. Анализ общественного мнения
lines.append("## 4. Анализ общественного мнения")
    if sentiment_data.get("success"):
        total = sentiment_data.get("total_count", 0)
        news_count = len(sentiment_data.get("news_items", []))
        report_count = len(sentiment_data.get("report_items", []))
        ann_count = len(sentiment_data.get("announce_items", []))
lines.append(f"-Общее количество связанной информации: {total} штук")
lines.append(f" - Новости: {news_count} строк")
        lines.append(f"  - 研报: {report_count} 条")
lines.append(f" - Объявления: {ann_count} строк")

        if news_count > 0:
            lines.append("")
lines.append("### Последние новости")
            for item in sentiment_data.get("news_items", [])[:5]:
                title = item.get("title", "")
                date = item.get("date", "").split()[0] if item.get("date") else ""
                institution = item.get("institution", "")
                source = f" — {institution}" if institution else ""
                lines.append(f"- [{date}] {title}{source}")
    else:
        lines.append("> ⚠️ 舆情数据获取失败")
        if sentiment_data.get("error"):
            lines.append(f"> 原因: {sentiment_data['error']}")
    lines.append("")

№ 5. Комплексная оценка
lines.append("## 5. Комплексная оценка")
lines.append("> Комплексный оценочный анализ на основе приведенных выше данных выглядит следующим образом: ")
    lines.append("")
    collected_count = sum(1 for v in [
        quote_data.get("success"),
        financial_data.get("success"),
        profile_data.get("success"),
        sentiment_data.get("success"),
    ] if v)

    if collected_count >= 3:
        lines.append(f"数据收集完成度: {collected_count}/4，综合分析可用。")
        lines.append("")
lines.append("### Справочник по оценке (необходимо объединить с углубленным анализом AI Agent)")
lines.append("- См. данные оценки в реальном времени в разделе [Обзор рынка]")
lines.append("- См. основные показатели, такие как рентабельность собственного капитала и чистая прибыль, в разделе [Финансовый анализ]")
        lines.append("")
    else:
        lines.append(f"⚠️ 数据收集不完整（{collected_count}/4），建议检查API Key配置后重试。")

lines.append("### Инвестиционный совет")
    lines.append("> ⚠️ **免责声明**: 本报告由智能股票分析助手自动生成，所有数据来源于东方财富妙想API。")
    lines.append("> 分析结果仅供参考和学习，不构成任何投资建议。投资有风险，入市需谨慎。")
    lines.append("")

    return "\n".join(lines)


def _format_data_section(data: dict) -> str:
"""Отформатируйте таблицу данных в Markdown"""
    lines = []
    tables = data.get("tables", [])
    if not tables:
        return "(暂无数据)"

for table in table[:3]: # Отобразить до 3 таблиц
        sheet_name = table.get("sheet_name", "")
        rows = table.get("rows", [])
        fieldnames = table.get("fieldnames", [])

        if sheet_name:
            lines.append(f"### {sheet_name}")

        if not rows:
lines.append("(Нет данных)")
            continue

# Ограничиваем количество строк
        display_rows = rows[:10]
        display_fields = fieldnames[:8]

# Заголовок
        header = " | ".join(display_fields)
        lines.append(f"| {header} |")
        lines.append(f"|{'|'.join(['---'] * len(display_fields))}|")

        for row in display_rows:
            values = [str(row.get(col, "")) for col in display_fields]
            lines.append(f"| {' | '.join(values)} |")

        if len(rows) > 10:
            lines.append(f"*(共{len(rows)}行，仅显示前10行)*")
        lines.append("")

    return "\n".join(lines)


def _generate_summary(report_content: str) -> str:
"""Создать краткую сводку из содержимого отчета"""
# Извлеките ключевую информацию из содержимого отчета для создания сводки
    try:
        lines = report_content.split("\n")
        data_status = ""
        for line in lines:
если в строке «завершение сбора данных»:
                data_status = line.strip()
                break
        return f"[智能股票分析助手] 分析报告已生成。{data_status}详见完整报告。"
    except Exception:
return «Отчет об анализе создан, просмотрите его полное содержимое».
