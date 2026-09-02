"""
Интеллектуальный помощник по анализу запасов — уровень обслуживания пользовательских предпочтений

Предоставляет операции CRUD для предпочтений, а также методы для вывода контекста предпочтений на уровень агента.
"""

import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import UserPreference


# =========================================================================
# 默认偏好（当用户未配置或无登录时使用）
# =========================================================================
DEFAULT_PREFERENCE = {
    "risk_tolerance": "moderate",
    "investment_style": "blend",
    "preferred_sectors": [],
    "excluded_sectors": [],
    "investment_horizon": "medium",
    "target_return_rate": 10.0,
    "max_position_ratio": 30.0,
    "max_drawdown_limit": -15.0,
    "notification_enabled": True,
    "notification_channels": ["push"],
    "market_alert_threshold": 5.0,
    "language": "zh",
    "theme": "auto",
    "default_view": "dashboard",
}


# =========================================================================
#CRUD-операции
# =========================================================================

async def get_preference(db: AsyncSession, user_id: str = "default") -> dict:
    """获取用户偏好，不存在时返回默认值"""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        return {**DEFAULT_PREFERENCE, "user_id": user_id}
    return pref.to_dict()


async def get_or_create_preference(db: AsyncSession, user_id: str = "default") -> UserPreference:
"""Получить или создать записи пользовательских настроек и вернуть объекты ORM"""
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    pref = result.scalar_one_or_none()
    if pref is None:
        pref = UserPreference.create_default(user_id)
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


async def update_preference(db: AsyncSession, user_id: str, data: dict) -> dict:
"""Обновление пользовательских настроек, поддержка частичных обновлений"""
    pref = await get_or_create_preference(db, user_id)

# Белый список полей, которые разрешено обновлять (чтобы предотвратить внедрение неопределенных полей)
    ALLOWED_FIELDS = {
        "risk_tolerance", "investment_style", "investment_horizon",
        "target_return_rate", "max_position_ratio", "max_drawdown_limit",
        "notification_enabled", "market_alert_threshold",
        "language", "theme", "default_view",
#Ниже приведены поля JSON
        "preferred_sectors", "excluded_sectors", "notification_channels",
    }

    for key, value in data.items():
        if key not in ALLOWED_FIELDS:
            continue

# Сериализация полей массива JSON
        if key in ("preferred_sectors", "excluded_sectors", "notification_channels"):
            if value is not None:
                setattr(pref, key, json.dumps(value, ensure_ascii=False))
# логическое поле
        elif key == "notification_enabled":
            setattr(pref, key, bool(value))
# Числовые поля
        elif key in ("target_return_rate", "max_position_ratio", "max_drawdown_limit", "market_alert_threshold"):
            setattr(pref, key, float(value))
        else:
            setattr(pref, key, value)

    await db.commit()
    await db.refresh(pref)
    return pref.to_dict()


# =========================================================================
#Метод введения агента
# =========================================================================

async def get_preference_context(db: AsyncSession, user_id: str = "default") -> str:
"""Сгенерировать текст контекста предпочтений для слоя агента для внедрения в процесс анализа.

    返回格式化的中文描述，可直接作为Agent系统提示词的一部分。
    """
    pref = await get_preference(db, user_id)
    if pref is None:
        pref = DEFAULT_PREFERENCE

    risk_map = {
        "conservative": "保守型——侧重低估值、高股息、蓝筹股，回避高风险标的",
        "moderate": "稳健型——均衡配置，兼顾成长与价值",
"aggressive": "Агрессивный - сосредоточение внимания на быстрорастущих и волатильных целях, принятие больших просадок",
    }
    style_map = {
"value": "Стоимостные инвестиции - отдайте предпочтение низкому PE, низкому PB, высокой дивидендной доходности",
«рост»: «Инвестиции в рост – предпочтение высоких темпов роста доходов и высоких целей роста прибыли»,
"momentum": "Импульсное инвестирование: предпочитайте сильные акции и следуйте тенденциям",
"dividend": "Инвестиции в дивиденды — предпочитают высокие цели по дивидендной доходности",
"blend": "Смешанный стиль — сочетание нескольких инвестиционных стратегий",
    }
    horizon_map = {
"short": "Краткосрочно (<1 года)",
«средний»: «среднесрочный (1-3 года)»,
"long": "Долгосрочно (>3 года)",
    }

    preferred = json.loads(pref.get("preferred_sectors", "[]")) if isinstance(pref.get("preferred_sectors"), str) else pref.get("preferred_sectors", [])
    excluded = json.loads(pref.get("excluded_sectors", "[]")) if isinstance(pref.get("excluded_sectors"), str) else pref.get("excluded_sectors", [])

    context_parts = [
«## Инвестиционные предпочтения пользователя (пожалуйста, скорректируйте анализ и рекомендации соответствующим образом)»,
f"- Толерантность к риску: {risk_map.get(pref['risk_tolerance'], pref['risk_tolerance'])}",
f"- Стиль инвестирования: {style_map.get(pref['investment_style'], pref['investment_style'])}",
f"- Инвестиционный горизонт: {horizon_map.get(pref['investment_horizon'], pref['investment_horizon'])}",
        f"- 目标年化收益率: {pref['target_return_rate']}%",
        f"- 单票最大仓位: {pref['max_position_ratio']}%",
        f"- 最大回撤预警线: {pref['max_drawdown_limit']}%",
    ]

    if preferred:
        context_parts.append(f"- 偏好行业: {', '.join(preferred)}")
    if excluded:
        context_parts.append(f"- 排除行业: {', '.join(excluded)}")

    return "\n".join(context_parts)


async def get_profile_summary(db: AsyncSession, user_id: str = "default") -> dict:
"""Получить сводку портрета инвестиций пользователя (используется для отображения сводки предпочтений внешнего интерфейса)"""
    pref = await get_preference(db, user_id)
    if pref is None:
        pref = DEFAULT_PREFERENCE

Risk_labels = {"консервативный": "консервативный", "умеренный": "надежный", "агрессивный": "агрессивный"}
style_labels = {"value": "стоимостное инвестирование", "growth": "инвестирование в рост", "momentum": "импульсное инвестирование", "dividend": "дивидендное инвестирование", "blend": "смешанный стиль"}

    return {
        "user_id": pref["user_id"],
        "risk_label": risk_labels.get(pref["risk_tolerance"], pref["risk_tolerance"]),
        "style_label": style_labels.get(pref["investment_style"], pref["investment_style"]),
        "target_return": f"{pref['target_return_rate']}%",
        "max_drawdown": f"{pref['max_drawdown_limit']}%",
        "preferred_sectors_count": len(pref.get("preferred_sectors", []) if isinstance(pref.get("preferred_sectors"), list) else json.loads(pref.get("preferred_sectors", "[]"))),
        "is_configured": pref.get("id") is not None,
    }
