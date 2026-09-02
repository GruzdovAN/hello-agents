"""
модель пользователя
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserDB(Base):
"""Модель пользовательской базы данных"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    institution = Column(String(200))
    research_field = Column(String(100))
Preferences = Column(Text) Формат #JSON для хранения пользовательских настроек
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(BaseModel):
"""Модель реакции пользователя"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    institution: Optional[str] = None
    research_field: Optional[str] = None
    is_active: bool = True
    is_premium: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
"""Модель, созданная пользователем"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    institution: Optional[str] = None
    research_field: Optional[str] = None

class UserUpdate(BaseModel):
"""Модель обновления пользователя"""
    full_name: Optional[str] = None
    institution: Optional[str] = None
    research_field: Optional[str] = None
    preferences: Optional[str] = None

class UserPreferences(BaseModel):
"""Пользовательские настройки"""
    research_interests: List[str] = []
    citation_style: str = "APA"
    language: str = "zh"
    notification_enabled: bool = True
    auto_save: bool = True