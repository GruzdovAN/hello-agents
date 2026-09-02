"""
Маршрутизация API, связанная с бумагой
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging
import arxiv
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# Пидантическая модель
class PaperSearchRequest(BaseModel):
    keywords: str
    source: str = "arxiv"
    limit: int = 10

class PaperResponse(BaseModel):
    id: str
    title: str
    authors: List[str]
    abstract: str
    url: str
    published_date: str

@router.post("/search", response_model=Dict[str, Any])
async def search_papers(request: PaperSearchRequest):
"""Поиск документов – использование настоящего ArXiv API"""
    try:
        papers = []
        
        if request.source == "arxiv" or request.source == "all":
# Поиск с использованием ArXiv API
            logger.info(f"正在搜索 ArXiv: {request.keywords}")
            
# Создаём поисковый запрос
            search = arxiv.Search(
                query=request.keywords,
                max_results=request.limit,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
# Получить результаты поиска
            for result in search.results():
                paper = {
                    "id": result.entry_id.split('/')[-1],
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "abstract": result.summary.replace('\n', ' ').strip(),
                    "url": result.entry_id,
                    "published_date": result.published.strftime("%Y-%m-%d"),
                    "pdf_url": result.pdf_url,
                    "categories": result.categories,
                    "primary_category": result.primary_category
                }
                papers.append(paper)
            
            logger.info(f"找到 {len(papers)} 篇论文")
        
# Если результат не найден, верните подсказку
        if not papers:
            return {
                "success": True,
                "papers": [],
                "total_found": 0,
                "keywords": request.keywords,
                "source": request.source,
"message": "Подходящие документы не найдены, попробуйте другие ключевые слова"
            }
        
        return {
            "success": True,
            "papers": papers,
            "total_found": len(papers),
            "keywords": request.keywords,
            "source": request.source
        }
        
    except Exception as e:
logger.error(f"Ошибка поиска бумаги: {str(e)}")
поднять HTTPException(status_code=500, Detail=f"Ошибка поиска: {str(e)}")

@router.post("/upload", response_model=Dict[str, Any])
async def upload_paper(file: UploadFile = File(...)):
"""Загрузить PDF-файл"""
    try:
#Проверяем тип файла
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
# Имитировать загрузку файла
        file_url = f"/uploads/{file.filename}"
        
        return {
            "success": True,
            "file_url": file_url,
            "filename": file.filename,
            "size": getattr(file, 'size', 0),
"message": "Файл успешно загружен"
        }
        
    except Exception as e:
logger.error(f"Ошибка загрузки файла: {str(e)}")
поднять HTTPException(status_code=500, Detail=f"Ошибка загрузки: {str(e)}")

