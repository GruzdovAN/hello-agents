"""
Интеллектуальный помощник по анализу акций — маршрутизация API по пользовательским предпочтениям

Предоставьте предпочтительные интерфейсы для чтения, обновления и запроса инвестиционного портрета.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List

from app.models.database import get_db_session
from app.services import preference_service
from app.utils.response import success_response, error_response

router = APIRouter(prefix="/preferences", tags=["用户偏好"])


# =========================================================================
# Запросить модель тела
# =========================================================================

class PreferenceUpdateRequest(BaseModel):
"""Тело запроса на обновление предпочтений - все поля являются необязательными, поддерживаются частичные обновления"""

Risk_tolerance: Необязательно[str] = Поле(Нет, описание="风险承受度: консервативный/умеренный/агрессивный", шаблон="^(консервативный|умеренный|агрессивный)$")
Investment_style: Необязательный[str] = Field(None,description="投资风格: значение/рост/импульс/дивиденд/смесь", шаблон="^(значение|рост|импульс|дивиденд|смесь)$")
Investment_horizon: Необязательно[str] = Поле(Нет, описание="投资期限: короткий/средний/длинный", шаблон="^(короткий|средний|длинный)$")
target_return_rate: Необязательный[float] = Field(None,description="Целевая годовая доходность (%)", ge=0, le=100)
max_position_ratio: Необязательно[float] = Поле(Нет, описание="Максимальная позиция одного билета (%)", ge=1, le=100)
max_drawdown_limit: Необязательно[float] = Поле(Нет, описание="Линия предупреждения о максимальном откате (%)", le=0)
Notification_enabled: Необязательный[bool] = Поле(Нет, описание="Включены ли уведомления")
Notification_channels: Необязательный[List[str]] = Поле(Нет, описание="Каналы уведомлений")
market_alert_threshold: Необязательно[float] = Поле(Нет, описание="Изменить порог оповещения (%)", ge=0, le=100)
язык: Необязательный[str] = Поле(Нет, описание="Язык интерфейса: ж/ен", шаблон="^(ж|ен)$")
тема: Необязательно[str] = Поле(Нет, описание="主题: светлый/темный/авто", шаблон="^(светлый|темный|авто)$")
default_view: Необязательно[str] = Поле(Нет, описание="Домашняя страница по умолчанию: панель мониторинга/список наблюдения", шаблон="^(панель мониторинга|список наблюдения)$")
предпочтительные_секторы: Необязательный[List[str]] = Поле(Нет, описание="Список предпочтительных отраслей")
исключенные_секторы: Необязательный[List[str]] = Поле(Нет, описание="Список исключенных отраслей")


# =========================================================================
# API-интерфейс
# =========================================================================

@router.get("/")
async def get_preferences(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db_session),
):
    """获取用户偏好配置"""
    try:
        result = await preference_service.get_preference(db, user_id)
        return success_response(data=result)
    except Exception as e:
        return error_response(code=500, message=f"获取偏好失败: {str(e)}")


@router.put("/")
async def update_preferences(
    request: PreferenceUpdateRequest,
    user_id: str = "default",
    db: AsyncSession = Depends(get_db_session),
):
"""Обновление пользовательских настроек (поддержка частичного обновления, передача только тех полей, которые необходимо изменить)"""
    try:
        # 仅提交非None的字段
        update_data = request.model_dump(exclude_none=True)
        if not update_data:
            return error_response(code=400, message="未提供需要更新的字段")

        result = await preference_service.update_preference(db, user_id, update_data)
        return success_response(data=result, message="偏好更新成功")
    except Exception as e:
        return error_response(code=500, message=f"更新偏好失败: {str(e)}")


@router.get("/profile")
async def get_profile(
    user_id: str = "default",
    db: AsyncSession = Depends(get_db_session),
):
"""Получите сводку инвестиционного портрета пользователей"""
    try:
        result = await preference_service.get_profile_summary(db, user_id)
        return success_response(data=result)
    except Exception as e:
        return error_response(code=500, message=f"获取画像失败: {str(e)}")
