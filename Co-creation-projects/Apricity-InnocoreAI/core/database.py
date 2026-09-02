"""
Модуль управления базами данных InnoCore AI
"""

import asyncio
import asyncpg
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json
import uuid
from contextlib import asynccontextmanager

from .config import get_config
from .exceptions import DatabaseException

class DatabaseManager:
"""Менеджер базы данных"""
    
    def __init__(self):
        self.config = get_config().database
        self.pool = None
    
    async def initialize(self):
"""Инициализировать пул соединений с базой данных"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=1,
                max_size=self.config.pool_size
            )
            await self._create_tables()
        except Exception as e:
            raise DatabaseException(f"数据库初始化失败: {str(e)}")
    
    async def _create_tables(self):
"""Создать таблицу базы данных"""
        create_tables_sql = """
--Пользовательская таблица
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            profile JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
-- Бумажный стол
        CREATE TABLE IF NOT EXISTS papers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title TEXT NOT NULL,
            authors TEXT[] DEFAULT '{}',
            abstract TEXT,
            doi VARCHAR(255) UNIQUE,
            file_path TEXT,
            content_hash VARCHAR(64) UNIQUE,
            is_preset BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
-- Таблица взаимосвязей между бумагами пользователей
        CREATE TABLE IF NOT EXISTS user_paper_relations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
            tags TEXT[] DEFAULT '{}',
            rating INTEGER DEFAULT 0,
            is_read BOOLEAN DEFAULT FALSE,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, paper_id)
        );
        
--Форма аналитического отчета
        CREATE TABLE IF NOT EXISTS analysis_reports (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            paper_id UUID REFERENCES papers(id) ON DELETE CASCADE,
            generated_for_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            summary TEXT,
            innovation_point TEXT,
            limitation TEXT,
            future_idea TEXT,
            vector_ids JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
-- Таблица ссылочного кэша
        CREATE TABLE IF NOT EXISTS reference_cache (
            doi VARCHAR(255) PRIMARY KEY,
            bibtex_std TEXT,
            is_verified BOOLEAN DEFAULT FALSE,
            last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
--Создать индекс
        CREATE INDEX IF NOT EXISTS idx_papers_content_hash ON papers(content_hash);
        CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi);
        CREATE INDEX IF NOT EXISTS idx_user_paper_relations_user_id ON user_paper_relations(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_paper_relations_paper_id ON user_paper_relations(paper_id);
        CREATE INDEX IF NOT EXISTS idx_analysis_reports_paper_id ON analysis_reports(paper_id);
        CREATE INDEX IF NOT EXISTS idx_analysis_reports_user_id ON analysis_reports(generated_for_user_id);
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_tables_sql)
    
    @asynccontextmanager
    async def get_connection(self):
"""Получить соединение с базой данных"""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            try:
                yield conn
            except Exception as e:
                raise DatabaseException(f"数据库操作失败: {str(e)}")
    
# Операции, связанные с пользователем
    async def create_user(self, email: str, profile: Dict = None) -> str:
"""Создать пользователя"""
        async with self.get_connection() as conn:
            user_id = await conn.fetchval(
                "INSERT INTO users (email, profile) VALUES ($1, $2) RETURNING id",
                email, json.dumps(profile or {})
            )
            return str(user_id)
    
    async def get_user(self, user_id: str) -> Optional[Dict]:
"""Получить информацию о пользователе"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )
            return dict(row) if row else None
    
    async def update_user_profile(self, user_id: str, profile: Dict) -> bool:
"""Обновить конфигурацию пользователя"""
        async with self.get_connection() as conn:
            result = await conn.execute(
                "UPDATE users SET profile = $1 WHERE id = $2",
                json.dumps(profile), user_id
            )
            return result == "UPDATE 1"
    
# Операции, связанные с бумагой
    async def create_paper(self, title: str, authors: List[str], 
                          abstract: str = None, doi: str = None,
                          file_path: str = None, content_hash: str = None,
                          is_preset: bool = False) -> str:
"""Создать бумажную запись"""
        async with self.get_connection() as conn:
            paper_id = await conn.fetchval(
                """
                INSERT INTO papers (title, authors, abstract, doi, file_path, content_hash, is_preset)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                title, authors, abstract, doi, file_path, content_hash, is_preset
            )
            return str(paper_id)
    
    async def get_paper(self, paper_id: str) -> Optional[Dict]:
"""Получить бумажную информацию"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM papers WHERE id = $1", paper_id
            )
            return dict(row) if row else None
    
    async def get_paper_by_hash(self, content_hash: str) -> Optional[Dict]:
"""Получить статьи на основе хэша контента"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM papers WHERE content_hash = $1", content_hash
            )
            return dict(row) if row else None
    
    async def search_papers(self, query: str, limit: int = 10, offset: int = 0) -> List[Dict]:
"""Поиск документов"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM papers 
                WHERE title ILIKE $1 OR abstract ILIKE $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3
                """,
                f"%{query}%", limit, offset
            )
            return [dict(row) for row in rows]
    
# Операции с пользовательскими документами
    async def add_paper_to_user(self, user_id: str, paper_id: str, 
                               tags: List[str] = None, rating: int = 0) -> bool:
"""Добавить статью в библиотеку пользователя"""
        async with self.get_connection() as conn:
            try:
                await conn.execute(
                    """
                    INSERT INTO user_paper_relations (user_id, paper_id, tags, rating)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (user_id, paper_id) DO UPDATE SET
                        tags = EXCLUDED.tags,
                        rating = EXCLUDED.rating,
                        added_at = CURRENT_TIMESTAMP
                    """,
                    user_id, paper_id, tags or [], rating
                )
                return True
            except Exception:
                return False
    
    async def get_user_papers(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
"""Получить список бумаг пользователя"""
        async with self.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT p.*, upr.tags, upr.rating, upr.is_read, upr.added_at
                FROM papers p
                JOIN user_paper_relations upr ON p.id = upr.paper_id
                WHERE upr.user_id = $1
                ORDER BY upr.added_at DESC
                LIMIT $2 OFFSET $3
                """,
                user_id, limit, offset
            )
            return [dict(row) for row in rows]
    
# Работа с аналитическим отчетом
    async def create_analysis_report(self, paper_id: str, summary: str,
                                   innovation_point: str, limitation: str,
                                   future_idea: str, vector_ids: Dict = None,
                                   user_id: str = None) -> str:
        """创建分析报告"""
        async with self.get_connection() as conn:
            report_id = await conn.fetchval(
                """
                INSERT INTO analysis_reports 
                (paper_id, generated_for_user_id, summary, innovation_point, limitation, future_idea, vector_ids)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                paper_id, user_id, summary, innovation_point, 
                limitation, future_idea, json.dumps(vector_ids or {})
            )
            return str(report_id)
    
    async def get_analysis_report(self, paper_id: str, user_id: str = None) -> Optional[Dict]:
"""Получить отчет об анализе"""
        async with self.get_connection() as conn:
            if user_id:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM analysis_reports 
                    WHERE paper_id = $1 AND (generated_for_user_id = $2 OR generated_for_user_id IS NULL)
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    paper_id, user_id
                )
            else:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM analysis_reports 
                    WHERE paper_id = $1 AND generated_for_user_id IS NULL
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    paper_id
                )
            return dict(row) if row else None
    
# Операция ссылочного кэша
    async def cache_reference(self, doi: str, bibtex: str, is_verified: bool = False):
"""Кэшировать справочную информацию"""
        async with self.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO reference_cache (doi, bibtex_std, is_verified, last_check)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (doi) DO UPDATE SET
                    bibtex_std = EXCLUDED.bibtex_std,
                    is_verified = EXCLUDED.is_verified,
                    last_check = CURRENT_TIMESTAMP
                """,
                doi, bibtex, is_verified
            )
    
    async def get_cached_reference(self, doi: str) -> Optional[Dict]:
"""Получить кэшированную справочную информацию"""
        async with self.get_connection() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM reference_cache WHERE doi = $1", doi
            )
            return dict(row) if row else None
    
    async def close(self):
"""Закройте пул соединений с базой данных"""
        if self.pool:
            await self.pool.close()

# Экземпляр глобального менеджера баз данных
db_manager = DatabaseManager()