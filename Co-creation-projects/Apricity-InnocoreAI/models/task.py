"""
модель задачи
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class TaskDB(Base):
"""Модель базы данных задач"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(50), nullable=False)  # literature_search, analysis, writing
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    priority = Column(String(10), default="medium")  # low, medium, high
параметры = Столбец (JSON) #Параметры задачи
результаты = Столбец (JSON) #Результаты задачи
    error_message = Column(Text)
    progress = Column(Integer, default=0)  # 0-100
    user_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

class Task(BaseModel):
"""Модель ответа на задачу"""
    id: int
    title: str
    description: Optional[str] = None
    task_type: str
    status: str
    priority: str
    progress: int = 0
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
"""Модель создания задачи"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_type: str = Field(..., regex=r'^(literature_search|analysis|writing)$')
    priority: str = Field(default="medium", regex=r'^(low|medium|high)$')
    parameters: Dict[str, Any] = {}

class TaskUpdate(BaseModel):
"""Модель обновления задачи"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class LiteratureSearchTask(BaseModel):
"""Параметры задачи поиска литературы"""
    query: str
    max_papers: int = 20
    year_range: Optional[tuple] = None
    venues: List[str] = []
    quality_threshold: float = 0.5

class AnalysisTask(BaseModel):
"""Параметры задачи анализа"""
    paper_ids: List[int]
    analysis_type: str = "comprehensive"  # comprehensive, methodology, findings
    focus_areas: List[str] = []

class WritingTask(BaseModel):
"""Запись параметров задачи"""
    paper_ids: List[int]
    writing_type: str = "review"  # review, summary, critique
    outline: Optional[List[str]] = None
    style: str = "academic"
    length: int = 1000