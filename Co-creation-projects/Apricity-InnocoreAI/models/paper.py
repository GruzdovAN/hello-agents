"""
Модель эссе
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class PaperDB(Base):
"""Модель базы данных диссертации"""
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
авторы = Столбец(Текст) #Хранение списка авторов в формате JSON
    abstract = Column(Text)
ключевые слова = Столбец(Текст) #Ключевые слова для хранения в формате JSON
    publication_year = Column(Integer)
    journal = Column(String(200))
    doi = Column(String(100), unique=True, index=True)
    arxiv_id = Column(String(50), unique=True, index=True)
    pdf_url = Column(String(500))
    pdf_path = Column(String(500))
    full_text = Column(Text)
embeddings = Column(JSON) # Сохранение векторных векторных представлений
метаданные = Столбец(JSON) # Сохранение дополнительных метаданных
    quality_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    is_processed = Column(Boolean, default=False)
    user_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Paper(BaseModel):
"""Бумажная модель ответа"""
    id: int
    title: str
    authors: List[str]
    abstract: Optional[str] = None
    keywords: List[str] = []
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    quality_score: float = 0.0
    relevance_score: float = 0.0
    is_processed: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaperCreate(BaseModel):
"""Модель создания диссертации"""
    title: str = Field(..., min_length=1, max_length=500)
    authors: List[str] = []
    abstract: Optional[str] = None
    keywords: List[str] = []
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None

class PaperUpdate(BaseModel):
"""Модель обновления диссертации"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    publication_year: Optional[int] = None
    journal: Optional[str] = None
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None

class PaperSearch(BaseModel):
"""Модель поиска по бумаге"""
    query: str = Field(..., min_length=1)
    filters: Dict[str, Any] = {}
    sort_by: str = "relevance"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

class PaperAnalysis(BaseModel):
"""Результаты анализа диссертации"""
    paper_id: int
    summary: str
    key_findings: List[str]
    methodology: str
    limitations: List[str]
    future_work: List[str]
    novelty_score: float
    impact_score: float
    confidence_score: float