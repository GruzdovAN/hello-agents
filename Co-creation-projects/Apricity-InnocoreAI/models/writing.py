"""
модель письма
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class WritingDB(Base):
"""Написание модели базы данных"""
    __tablename__ = "writing"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    writing_type = Column(String(50), nullable=False)  # review, summary, critique, proposal
    content = Column(Text)
контур = Столбец (JSON) # Структура структуры
разделы = Столбец(JSON) # Содержимое раздела
citations = Column(JSON) #Информация о цитировании
метаданные = Столбец(JSON) # Дополнительные метаданные
    quality_score = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")  # draft, reviewing, completed
paper_ids = Column(JSON) # Список идентификаторов справочной бумаги
    user_id = Column(Integer, index=True)
    task_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Writing(BaseModel):
"""Написание модели ответа"""
    id: int
    title: str
    writing_type: str
    content: Optional[str] = None
    outline: List[Dict[str, Any]] = []
    sections: Dict[str, str] = {}
    citations: List[Dict[str, Any]] = []
    quality_score: float = 0.0
    word_count: int = 0
    status: str = "draft"
    created_at: datetime
    
    class Config:
        from_attributes = True

class WritingCreate(BaseModel):
"""Написание модели создания"""
    title: str = Field(..., min_length=1, max_length=200)
    writing_type: str = Field(..., regex=r'^(review|summary|critique|proposal)$')
    paper_ids: List[int] = []
    outline: Optional[List[Dict[str, Any]]] = None

class WritingUpdate(BaseModel):
"""Написание модели обновления"""
    title: Optional[str] = None
    content: Optional[str] = None
    outline: Optional[List[Dict[str, Any]]] = None
    sections: Optional[Dict[str, str]] = None
    citations: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class LiteratureReview(BaseModel):
"""литературный обзор"""
    introduction: str
    methodology_review: str
    findings_synthesis: str
    discussion: str
    conclusion: str
    references: List[Dict[str, Any]]

class PaperSummary(BaseModel):
"""Резюме диссертации"""
    background: str
    methods: str
    results: str
    conclusions: str
    significance: str

class PaperCritique(BaseModel):
"""Обзор статьи"""
    strengths: List[str]
    weaknesses: List[str]
    methodological_issues: List[str]
    interpretation_concerns: List[str]
    suggestions: List[str]

class ResearchProposal(BaseModel):
"""Предложение по исследованию"""
    background: str
    problem_statement: str
    research_questions: List[str]
    methodology: str
    expected_outcomes: str
    significance: str
    timeline: str

class WritingSection(BaseModel):
"""Написание глав"""
    title: str
    content: str
    subsections: List['WritingSection'] = []
    citations: List[str] = []

#Разрешить прямые ссылки
WritingSection.model_rebuild()