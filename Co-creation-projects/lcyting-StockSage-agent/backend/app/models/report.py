"""
Интеллектуальный помощник по анализу запасов — модель данных аналитического отчета

Храните отчеты об углубленном анализе отдельных акций и поддерживайте сохранение отчетов и исторические запросы.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.models.database import Base


class AnalysisReport(Base):
"""Форма отчета об анализе"""

    __tablename__ = "analysis_reports"

id = Столбец(Целое число, Primary_key=True, автоинкремент=True, комментарий="报告ID")
user_id = Column(String(64), nullable=False, default="default", comment="Идентификатор пользователя")
    stock_code = Column(String(16), nullable=False, comment="股票代码")
    stock_name = Column(String(64), default="", comment="股票名称")
report_type = Column(String(32), default="full", comment="Тип отчета: полный=полный анализ, быстрый=быстрый обзор")
summary = Column(String(1024), default="", comment="Сводка отчета (одно предложение инвестиционного совета)")
content = Column(Text, default="", comment="Сообщить о полном содержимом (формат Markdown)")
data_snapshot = Column(Text, default="{}", comment="Снимок данных (формат JSON, сохраняет исходные запрошенные данные)")
Create_at = Column(DateTime, server_default=func.now(), comment="Время создания")

    def to_dict(self) -> dict:
"""Преобразовать в словарь"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "report_type": self.report_type,
            "summary": self.summary,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
