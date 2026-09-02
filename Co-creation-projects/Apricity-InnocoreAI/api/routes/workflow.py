"""
Маршрутизация API рабочего процесса — координируйте работу нескольких агентов для выполнения сложных задач.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
import asyncio
from agents.controller import agent_controller

logger = logging.getLogger(__name__)
router = APIRouter()

# Пидантическая модель
class WorkflowRequest(BaseModel):
    keywords: str
    analysis_type: str = "summary"  # summary, innovation, comparison, comprehensive
    citation_format: str = "bibtex"  # bibtex, apa, ieee, mla
    writing_task: Optional[str] = None  # improve, polish, translate
limit: int = 5 # Поиск количества статей

class WorkflowStatus(BaseModel):
    workflow_id: str
    status: str  # running, completed, failed
    current_step: str
    progress: int  # 0-100

@router.post("/complete", response_model=Dict[str, Any])
async def complete_workflow(request: WorkflowRequest):
    """
Полный рабочий процесс: Поиск -> Анализ -> Проверка ссылок -> Помощь в написании.
Автоматически координируйте всех агентов для выполнения задач
    """
    try:
        workflow_id = f"workflow_{asyncio.get_event_loop().time()}"
        results = {
            "workflow_id": workflow_id,
            "status": "running",
            "steps": []
        }
        
# Шаг 1: Охотник — Поиск документов
        logger.info(f"[工作流 {workflow_id}] 步骤 1/4: 搜索论文")
        try:
            from api.routes.papers import search_papers, PaperSearchRequest
            
            search_result = await search_papers(PaperSearchRequest(
                keywords=request.keywords,
                source="arxiv",
                limit=request.limit
            ))
            
            papers = search_result.get("papers", [])
            results["steps"].append({
                "step": 1,
"name": "Охотник — Поиск бумаги",
                "status": "completed",
                "result": {
                    "total_found": len(papers),
                    "papers": papers
                }
            })
            
            if not papers:
                raise HTTPException(status_code=404, detail="未找到相关论文")
            
        except Exception as e:
logger.error(f"Ошибка поиска бумаги: {str(e)}")
            results["steps"].append({
                "step": 1,
"name": "Охотник — Поиск бумаги",
                "status": "failed",
                "error": str(e)
            })
            results["status"] = "failed"
            return results
        
# Шаг 2: Майнер — анализируйте каждую бумагу
        logger.info(f"[工作流 {workflow_id}] 步骤 2/4: 分析论文")
        analyses = []
        try:
            from api.routes.analysis import analyze_paper, PaperAnalysisRequest
            
# Проанализируйте первые 3 статьи
            for i, paper in enumerate(papers[:3]):
                try:
                    analysis_result = await analyze_paper(PaperAnalysisRequest(
                        paper_url=paper["url"],
                        analysis_type=request.analysis_type
                    ))
                    analyses.append({
                        "paper_id": paper["id"],
                        "title": paper["title"],
                        "analysis": analysis_result.get("analysis", "")
                    })
                except Exception as e:
                    logger.warning(f"分析论文 {paper['id']} 失败: {str(e)}")
                    continue
            
            results["steps"].append({
                "step": 2,
"name": "Майнер — анализ бумаги",
                "status": "completed",
                "result": {
                    "total_analyzed": len(analyses),
                    "analyses": analyses
                }
            })
            
        except Exception as e:
logger.error(f"Анализ бумаги не удался: {str(e)}")
            results["steps"].append({
                "step": 2,
"name": "Майнер — анализ бумаги",
                "status": "failed",
                "error": str(e)
            })
        
# Шаг 3: Валидатор — создание и проверка ссылок
        logger.info(f"[工作流 {workflow_id}] 步骤 3/4: 生成引用")
        citations = []
        try:
            from api.routes.citations import validate_citation, CitationValidationRequest
            
# Генерация цитат для каждой статьи
            for paper in papers[:3]:
                try:
# Создаём цитируемый текст
                    authors_str = ", ".join(paper["authors"][:3])
                    if len(paper["authors"]) > 3:
                        authors_str += " et al."
                    
                    citation_text = f"{authors_str} ({paper['published_date'][:4]}). {paper['title']}. arXiv:{paper['id']}"
                    
                    citation_result = await validate_citation(CitationValidationRequest(
                        citation=citation_text,
                        format=request.citation_format
                    ))
                    
                    citations.append({
                        "paper_id": paper["id"],
                        "title": paper["title"],
                        "formatted_citation": citation_result.get("formatted_citation", "")
                    })
                except Exception as e:
                    logger.warning(f"生成引用失败: {str(e)}")
                    continue
            
            results["steps"].append({
                "step": 3,
"name": "Валидатор — генерация ссылок",
                "status": "completed",
                "result": {
                    "total_citations": len(citations),
                    "citations": citations
                }
            })
            
        except Exception as e:
logger.error(f «Не удалось создать ссылку: {str(e)}»)
            results["steps"].append({
                "step": 3,
"name": "Валидатор — генерация ссылок",
                "status": "failed",
                "error": str(e)
            })
        
# Шаг 4: Тренер — создание подробного отчета (необязательно)
        if request.writing_task:
            logger.info(f"[工作流 {workflow_id}] 步骤 4/4: 生成报告")
            try:
                from api.routes.writing import writing_coach, WritingCoachRequest
                
# Создайте подробный текст отчета
                report_text = f"# 关于 '{request.keywords}' 的研究综述\n\n"
                report_text += f"## 搜索结果\n找到 {len(papers)} 篇相关论文\n\n"
                
                if analyses:
report_text += "## Анализ статьи\n"
                    for i, analysis in enumerate(analyses[:3], 1):
                        report_text += f"\n### {i}. {analysis['title']}\n"
                        report_text += f"{analysis['analysis'][:500]}...\n"
                
                if citations:
report_text += "\n## Ссылки\n"
                    for i, citation in enumerate(citations, 1):
                        report_text += f"{i}. {citation['formatted_citation']}\n"
                
# Улучшайте отчеты с помощью Coach
                writing_result = await writing_coach(WritingCoachRequest(
                    text=report_text,
                    style="academic",
                    task=request.writing_task
                ))
                
                results["steps"].append({
                    "step": 4,
"name": "Coach — Генерация отчетов",
                    "status": "completed",
                    "result": {
                        "report": writing_result.get("result", "")
                    }
                })
                
            except Exception as e:
logger.error(f"Ошибка создания отчета: {str(e)}")
                results["steps"].append({
                    "step": 4,
"name": "Coach — Генерация отчетов",
                    "status": "failed",
                    "error": str(e)
                })
        
#Завершить рабочий процесс
        results["status"] = "completed"
        results["summary"] = {
            "total_papers": len(papers),
            "analyzed_papers": len(analyses),
            "generated_citations": len(citations),
            "keywords": request.keywords
        }
        
logger.info(f"[рабочий процесс {workflow_id}] завершен")
        return results
        
    except HTTPException:
        raise
    except Exception as e:
logger.error(f"Ошибка выполнения рабочего процесса: {str(e)}")
поднять HTTPException(status_code=500, Detail=f"Ошибка выполнения рабочего процесса: {str(e)}")

@router.post("/search-and-analyze", response_model=Dict[str, Any])
async def search_and_analyze(request: WorkflowRequest):
    """
Упрощенный рабочий процесс: поиск + анализ
Выполняйте только шаги поиска и анализа
    """
    try:
        results = {
            "status": "running",
            "steps": []
        }
        
# Шаг 1: Поиск документов
        from api.routes.papers import search_papers, PaperSearchRequest
        
        search_result = await search_papers(PaperSearchRequest(
            keywords=request.keywords,
            source="arxiv",
            limit=request.limit
        ))
        
        papers = search_result.get("papers", [])
        results["steps"].append({
            "step": 1,
"name": "Поиск документов",
            "status": "completed",
            "papers": papers
        })
        
        if not papers:
            raise HTTPException(status_code=404, detail="未找到相关论文")
        
# Шаг 2: Проанализируйте первую статью
        from api.routes.analysis import analyze_paper, PaperAnalysisRequest
        
        first_paper = papers[0]
        analysis_result = await analyze_paper(PaperAnalysisRequest(
            paper_url=first_paper["url"],
            analysis_type=request.analysis_type
        ))
        
        results["steps"].append({
            "step": 2,
"name": "Аналитический документ",
            "status": "completed",
            "analysis": analysis_result
        })
        
        results["status"] = "completed"
        return results
        
    except HTTPException:
        raise
    except Exception as e:
logger.error(f"Ошибка поиска и анализа: {str(e)}")
поднять HTTPException(status_code=500, Detail=f"Ошибка выполнения: {str(e)}")

@router.get("/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
"""Получить статус рабочего процесса"""
    try:
# Здесь можно реализовать отслеживание статуса рабочего процесса
# Временно вернуться в состояние симуляции
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "progress": 100,
"message": "Рабочий процесс завершен"
        }
    except Exception as e:
logger.error(f «Не удалось получить статус рабочего процесса: {str(e)}»)
        raise HTTPException(status_code=500, detail=str(e))
