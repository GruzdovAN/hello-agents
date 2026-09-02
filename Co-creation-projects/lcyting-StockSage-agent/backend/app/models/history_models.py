"""
Анализ истории модели ORM (имя файла, согласованное с решением по внедрению)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.models.database import Base


class AnalysisHistory(Base):
"""Таблица истории анализа - хранит различные отчеты анализа по дням"""

    __tablename__ = "analysis_history"

id = Столбец(Целое число, Primary_key=True, autoincrement=True, comment="记录ID")
user_id = Column(String(64), nullable=False, default="default", comment="Идентификатор пользователя")
    date = Column(String(16), nullable=False, comment="日期 yyyy-mm-dd")
type = Column(String(32), nullable=False, comment="类型: Sentiment/data_anaанализ/buffett/chat")
    stock_code = Column(String(16), nullable=True, comment="股票代码")
    stock_name = Column(String(64), nullable=True, comment="股票名称")
    title = Column(String(256), nullable=True, comment="标题")
    content = Column(Text, nullable=False, comment="内容（Markdown格式）")
Create_at = Column(DateTime, server_default=func.now(), comment="Время создания")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "type": self.type,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
