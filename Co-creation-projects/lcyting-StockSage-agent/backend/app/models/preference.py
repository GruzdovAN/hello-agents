"""
Интеллектуальный помощник по анализу запасов — модель данных о предпочтениях пользователя

Определите структуры постоянного хранения, такие как инвестиционные предпочтения пользователей, параметры контроля рисков и предпочтения интерфейса.
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, func
from app.models.database import Base


class UserPreference(Base):
"""Модель предпочтений пользователя"""

    __tablename__ = "user_preferences"

# Первичный ключ
    id = Column(Integer, primary_key=True, autoincrement=True)

#Связывание пользователей (в настоящее время упрощено: однопользовательский режим, многопользовательский режим можно расширить позже)
    user_id = Column(String(64), default="default", unique=True, nullable=False, comment="用户ID")

    # =========================================================================
#Инвестиционные предпочтения
    # =========================================================================
    risk_tolerance = Column(
        String(20), default="moderate", nullable=False,
        comment="风险承受度: conservative / moderate / aggressive"
    )
    investment_style = Column(
        String(20), default="blend", nullable=False,
        comment="投资风格: value / growth / momentum / dividend / blend"
    )
    preferred_sectors = Column(
        Text, default="[]",
comment="Предпочитаемые отрасли (массив JSON)"
    )
    excluded_sectors = Column(
        Text, default="[]",
comment="Исключить отрасли (массив JSON)"
    )
    investment_horizon = Column(
        String(20), default="medium",
comment="Срок инвестирования: короткий/средний/длинный"
    )
    target_return_rate = Column(
        Float, default=10.0, nullable=False,
comment="Целевая годовая доходность (%)"
    )

    # =========================================================================
# Параметры контроля рисков
    # =========================================================================
    max_position_ratio = Column(
        Float, default=30.0, nullable=False,
comment="Максимальный коэффициент позиции по одной акции (%)"
    )
    max_drawdown_limit = Column(
        Float, default=-15.0, nullable=False,
comment="Линия предупреждения о максимальном откате (%)"
    )

    # =========================================================================
# Настройки уведомлений
    # =========================================================================
    notification_enabled = Column(
        Boolean, default=True, nullable=False,
comment="Включить ли уведомления"
    )
    notification_channels = Column(
        Text, default='["push"]',
comment="Канал уведомлений (JSON: email/sms/push)"
    )
    market_alert_threshold = Column(
        Float, default=5.0, nullable=False,
comment="Порог напоминания об изменении рынка (%)"
    )

    # =========================================================================
# Настройки интерфейса
    # =========================================================================
    language = Column(
        String(10), default="zh", nullable=False,
comment="Язык интерфейса: ж/эн"
    )
    theme = Column(
        String(10), default="auto", nullable=False,
comment="Тема: светлая/темная/авто"
    )
    default_view = Column(
        String(20), default="dashboard", nullable=False,
comment="Домашняя страница по умолчанию: панель управления/список наблюдения"
    )

    # =========================================================================
# временная метка
    # =========================================================================
Create_at = Column(DateTime, server_default=func.now(), comment="Время создания")
update_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self) -> dict:
"""Преобразовать в словарь (для ответа API)"""
        import json

        return {
            "id": self.id,
            "user_id": self.user_id,
            "risk_tolerance": self.risk_tolerance,
            "investment_style": self.investment_style,
            "preferred_sectors": json.loads(self.preferred_sectors),
            "excluded_sectors": json.loads(self.excluded_sectors),
            "investment_horizon": self.investment_horizon,
            "target_return_rate": self.target_return_rate,
            "max_position_ratio": self.max_position_ratio,
            "max_drawdown_limit": self.max_drawdown_limit,
            "notification_enabled": self.notification_enabled,
            "notification_channels": json.loads(self.notification_channels),
            "market_alert_threshold": self.market_alert_threshold,
            "language": self.language,
            "theme": self.theme,
            "default_view": self.default_view,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_default(cls, user_id: str = "default") -> "UserPreference":
"""Создать экземпляр настройки по умолчанию"""
        return cls(
            user_id=user_id,
            risk_tolerance="moderate",
            investment_style="blend",
            preferred_sectors="[]",
            excluded_sectors="[]",
            investment_horizon="medium",
            target_return_rate=10.0,
            max_position_ratio=30.0,
            max_drawdown_limit=-15.0,
            notification_enabled=True,
            notification_channels='["push"]',
            market_alert_threshold=5.0,
            language="zh",
            theme="auto",
            default_view="dashboard",
        )
