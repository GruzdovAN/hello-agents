"""
Анализируйте связанные маршруты API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
import arxiv
import os
from core.config import get_config
from core.llm_adapter import get_llm_adapter
from utils.pdf_parser import pdf_parser

logger = logging.getLogger(__name__)
router = APIRouter()

# Инициализируем адаптер LLM (на основе HelloAgent)
config = get_config()
try:
    llm = get_llm_adapter() if config.llm.api_key else None
except Exception as e:
logger.warning(f"Ошибка инициализации LLM: {str(e)}")
    llm = None

# Пидантическая модель
class AnalysisRequest(BaseModel):
    paper_id: str
    user_id: Optional[str] = None
    analysis_type: str = "full"  # full, quick, innovation_only

class ComparisonRequest(BaseModel):
    paper_ids: List[str]
    user_id: Optional[str] = None
    comparison_aspects: List[str] = ["method", "results", "innovation"]

class InnovationSearchRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    search_scope: str = "both"  # l1, l2, both
    top_k: int = 10

class PaperAnalysisRequest(BaseModel):
    paper_url: str
    analysis_type: str = "summary"  # summary, innovation, comparison, comprehensive

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_paper(request: PaperAnalysisRequest):
"""Анализ документов — поддержка URL-адресов ArXiv и локальных PDF-файлов"""
    try:
        if not llm:
поднять HTTPException (status_code=503, Detail="Служба AI не настроена, установите OPENAI_API_KEY")
        
        import re
        paper_url = request.paper_url.strip()
        
# Проверьте, является ли это локально загруженным PDF-файлом
        if paper_url.startswith('/uploads/') or paper_url.endswith('.pdf'):
            logger.info(f"检测到本地 PDF 文件: {paper_url}")
            
# Создаём полный путь к файлу
            if paper_url.startswith('/uploads/'):
# Предположим, что загруженный файл находится в каталоге загрузок
                file_path = os.path.join('downloads', paper_url.replace('/uploads/', ''))
            else:
                file_path = paper_url
            
#Проверяем, существует ли файл
            if not os.path.exists(file_path):
                logger.warning(f"PDF 文件不存在: {file_path}")
поднять HTTPException (status_code=404, Detail=f «PDF-файл не существует: {paper_url}»)
            
# Разбор PDF-файлов
            logger.info(f"开始解析 PDF 文件: {file_path}")
            pdf_result = await pdf_parser.parse_pdf(file_path)
            
            if not pdf_result.get("success"):
поднять HTTPException(status_code=500, Detail=pdf_result.get("ошибка", "Ошибка анализа PDF"))
            
#Используйте проанализированный контент для анализа ИИ
            title = pdf_result.get("title", "未知标题")
            authors = pdf_result.get("authors", ["未知作者"])
            abstract = pdf_result.get("abstract", "")
            full_text = pdf_result.get("full_text", "")
            
# Ограничьте длину текста, чтобы не превысить лимит токенов
            text_for_analysis = full_text[:8000] if len(full_text) > 8000 else full_text
            
# Генерация слов-подсказок в зависимости от типа анализа
            prompts = {
"резюме": f"""Просьба представить краткий анализ следующих документов:

Название: {title}
Автор: {', '.join(авторы)}
Аннотация:{аннотация}

Содержание статьи (первые 8000 символов):
{text_for_analysis}

Пожалуйста, предоставьте:
1. Предыстория и мотивация исследования
2. Основные методы
3. Основной вклад
4. Результаты экспериментов
5. Значение исследования

Пожалуйста, отвечайте на китайском языке и будьте профессиональными и краткими. """,
                
«инновация»: f»»»Проанализируйте инновационные моменты следующих статей:

Название: {title}
Аннотация:{аннотация}

Содержание бумаги:
{text_for_analysis}

Пожалуйста, проанализируйте подробно:
1. Точки технологических инноваций
2. Методологическая инновация
3. Теоретический вклад
4. Отличия от существующих работ
5. Потенциальная ценность приложения

Пожалуйста, ответьте на китайском языке. """,
                
"сравнение": f"""Проведите сравнительный анализ следующих статей:

Название: {title}
Аннотация:{аннотация}

Содержание бумаги:
{text_for_analysis}

Пожалуйста, проанализируйте:
1. Сравнение с традиционными методами
2. Преимущества и недостатки
3. Применимые сценарии
4. Улучшение производительности
5. Ограничения

Пожалуйста, ответьте на китайском языке. """,
                
                "comprehensive": f"""请对以下论文进行全面综合分析：

Название: {title}
Автор: {', '.join(авторы)}
Аннотация:{аннотация}

Содержание бумаги:
{text_for_analysis}

Пожалуйста, предоставьте комплексный анализ, включающий:
1. Предыстория и значимость исследования
2. Подробное объяснение технических методов.
3. Анализ инновационных точек
4. Экспериментальная проверка
5. Оценка преимуществ и недостатков
6. Будущие направления исследований
7. Практическая ценность применения

Пожалуйста, отвечайте на китайском языке и оставайтесь профессиональными и содержательными. """
            }
            
            prompt = prompts.get(request.analysis_type, prompts["summary"])
            
# Позвоните в LLM для анализа
            logger.info(f"开始 AI 分析，类型: {request.analysis_type}")
            response = await llm.ainvoke(prompt)
            analysis_content = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "success": True,
                "paper_info": {
                    "id": "local_pdf",
                    "title": title,
                    "authors": authors,
                    "published_date": "N/A",
                    "url": paper_url,
"categories": ["локальные файлы"],
                    "page_count": pdf_result.get("page_count", 0),
                    "word_count": pdf_result.get("word_count", 0)
                },
                "analysis_type": request.analysis_type,
                "analysis": analysis_content,
                "abstract": abstract
            }
        
# Обработка бумаги ArXiv
        arxiv_patterns = [
            r'arxiv\.org/abs/(\d+\.\d+)',
            r'arxiv\.org/pdf/(\d+\.\d+)',
            r'arXiv:(\d+\.\d+)',
            r'\[(\d+\.\d+)v?\d*\]',
            r'^(\d{4}\.\d{4,5})v?\d*$'
        ]
        
        paper_id = None
        for pattern in arxiv_patterns:
            match = re.search(pattern, paper_url, re.IGNORECASE)
            if match:
                paper_id = match.group(1)
                break
        
        if not paper_id:
            raise HTTPException(
                status_code=400, 
Detail=f"Неверный ввод. Поддерживаемые форматы:\n" +
                       "- ArXiv URL: https://arxiv.org/abs/2511.16672\n" +
                       "- ArXiv ID: 2511.16672\n" +
«-Локальный PDF: автозаполнение после загрузки»
            )
        
        logger.info(f"正在分析 ArXiv 论文: {paper_id}")
        
# Получить информацию о бумаге
        search = arxiv.Search(id_list=[paper_id])
        paper = next(search.results(), None)
        
        if not paper:
поднять HTTPException(status_code=404, Detail=f"Бумага ArXiv не найдена: {paper_id}")
        
# Генерация слов-подсказок в зависимости от типа анализа
        prompts = {
"резюме": f"""Просьба представить краткий анализ следующих документов:

Название: {paper.title}
作者：{', '.join([имя в документе.авторы])}
Резюме: {paper.summary}

Пожалуйста, предоставьте:
1. Предыстория и мотивация исследования
2. Основные методы
3. Основной вклад
4. Результаты экспериментов
5. Значение исследования

Пожалуйста, отвечайте на китайском языке и будьте профессиональными и краткими. """,
            
«инновация»: f»»»Проанализируйте инновационные моменты следующих статей:

Название: {paper.title}
Резюме: {paper.summary}

Пожалуйста, проанализируйте подробно:
1. Точки технологических инноваций
2. Методологическая инновация
3. Теоретический вклад
4. Отличия от существующих работ
5. Потенциальная ценность приложения

Пожалуйста, ответьте на китайском языке. """,
            
"сравнение": f"""Проведите сравнительный анализ следующих статей:

Название: {paper.title}
Резюме: {paper.summary}

Пожалуйста, проанализируйте:
1. Сравнение с традиционными методами
2. Преимущества и недостатки
3. Применимые сценарии
4. Улучшение производительности
5. Ограничения

Пожалуйста, ответьте на китайском языке. """,
            
«комплексный»: f»»»Пожалуйста, проведите всесторонний и всесторонний анализ следующих документов:

Название: {paper.title}
作者：{', '.join([имя в документе.авторы])}
Резюме: {paper.summary}
Категории: {', '.join(paper.categories)}

Пожалуйста, предоставьте комплексный анализ, включающий:
1. Предыстория и значимость исследования
2. Подробное объяснение технических методов.
3. Анализ инновационных точек
4. Экспериментальная проверка
5. Оценка преимуществ и недостатков
6. Будущие направления исследований
7. Практическая ценность применения

Пожалуйста, отвечайте на китайском языке и оставайтесь профессиональными и содержательными. """
        }
        
        prompt = prompts.get(request.analysis_type, prompts["summary"])
        
# Позвоните в LLM для анализа
        response = await llm.ainvoke(prompt)
        analysis_content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "success": True,
            "paper_info": {
                "id": paper_id,
                "title": paper.title,
                "authors": [a.name for a in paper.authors],
                "published_date": paper.published.strftime("%Y-%m-%d"),
                "url": paper.entry_id,
                "categories": paper.categories
            },
            "analysis_type": request.analysis_type,
            "analysis": analysis_content,
            "abstract": paper.summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
logger.error(f"Анализ бумаги не удался: {str(e)}")
поднять HTTPException (status_code=500, Detail=f «Анализ не выполнен: {str(e)}»)

@router.post("/compare", response_model=Dict[str, Any])
async def compare_papers(request: ComparisonRequest):
"""Сравнить несколько статей"""
    try:
# Здесь нужно реализовать логику сравнения бумаг
# Временно возвращаем результаты моделирования
        
        comparison_result = {
            "paper_ids": request.paper_ids,
            "comparison_aspects": request.comparison_aspects,
"сходства": ["сходство1", "сходство2"],
"differences": ["разница 1", "разница 2"],
            "innovation_gaps": ["创新空白1", "创新空白2"],
"рекомендации": ["рекомендации 1", "рекомендации 2"]
        }
        
        return {
            "success": True,
            "result": comparison_result
        }
        
    except Exception as e:
logger.error(f"Сравнение бумаги не удалось: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/innovation/search", response_model=Dict[str, Any])
async def search_innovation_opportunities(request: InnovationSearchRequest):
"""Поиск инновационных возможностей"""
    try:
#Здесь нам необходимо реализовать логику поиска инновационных возможностей
# Временно возвращаем результаты моделирования
        
        innovation_results = {
            "query": request.query,
            "opportunities": [
                {
"title": "Инновационная возможность 1",
"description": "Инновационные направления на основе текущих исследований",
                    "related_papers": ["paper1", "paper2"],
                    "confidence": 0.85
                },
                {
"title": "Инновационная возможность 2",
                    "description": "另一个潜在的研究方向",
                    "related_papers": ["paper3", "paper4"],
                    "confidence": 0.72
                }
            ],
            "research_gaps": ["研究空白1", "研究空白2"],
            "future_directions": ["未来方向1", "未来方向2"]
        }
        
        return {
            "success": True,
            "result": innovation_results
        }
        
    except Exception as e:
logger.error(f"Ошибка поиска возможностей для инноваций: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paper/{paper_id}/summary")
async def get_paper_summary(paper_id: str, user_id: Optional[str] = None):
"""Получить реферат"""
    try:
# Здесь нужно реализовать логику генерации бумажных рефератов
# Временно возвращаем результаты моделирования
        
        summary = {
            "paper_id": paper_id,
            "summary": "这是一篇关于...的论文，主要贡献包括...",
            "key_contributions": ["贡献1", "贡献2", "贡献3"],
"methodology": "В статье использован метод...",
"results": "Результаты эксперимента показывают...",
"limitations": "Ограничения исследования включают...",
"future_work": "Будущее направление работы..."
        }
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
logger.error(f"Не удалось получить реферат статьи: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/paper/{paper_id}/innovations")
async def get_paper_innovations(paper_id: str, user_id: Optional[str] = None):
"""Получите инновационные баллы в статье"""
    try:
# Здесь нам нужно реализовать логику извлечения очков инноваций
# Временно возвращаем результаты моделирования
        
        innovations = {
            "paper_id": paper_id,
            "innovations": [
                {
«аспект»: «инновация метода»,
                    "description": "提出了新的方法...",
                    "novelty": "high",
                    "impact": "significant"
                },
                {
«аспект»: «теоретическая инновация»,
                    "description": "在理论上有所突破...",
                    "novelty": "medium",
                    "impact": "moderate"
                }
            ],
            "comparison_with_prior_work": "与之前的工作相比...",
            "potential_applications": ["应用1", "应用2"]
        }
        
        return {
            "success": True,
            "innovations": innovations
        }
        
    except Exception as e:
logger.error(f"Не удалось получить инновационные баллы статьи: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}/insights")
async def get_user_insights(user_id: str):
"""Получите информацию об исследованиях пользователей"""
    try:
# Здесь нам нужно реализовать анализ пользовательской информации
# Временно возвращаем результаты моделирования
        
        insights = {
            "user_id": user_id,
"research_interests": ["Интерес1", "Интерес2"],
            "reading_patterns": {
                "papers_read": 50,
"favorite_topics": ["topic1", "topic2"],
                "reading_frequency": "daily"
            },
            "knowledge_gaps": ["知识空白1", "知识空白2"],
            "research_suggestions": [
                {
"topic": "Предлагаемое направление исследования 1",
"reason": "Исходя из вашей истории чтения...",
                    "related_papers": ["paper1", "paper2"]
                }
            ],
            "skill_assessment": {
                "technical_skills": ["技能1", "技能2"],
                "writing_skills": ["写作技能1", "写作技能2"],
                "improvement_areas": ["改进领域1", "改进领域2"]
            }
        }
        
        return {
            "success": True,
            "insights": insights
        }
        
    except Exception as e:
logger.error(f"Не удалось получить данные исследования пользователей: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch", response_model=Dict[str, Any])
async def batch_analyze_papers(paper_ids: List[str], user_id: Optional[str] = None):
"""Документы по анализу партии"""
    try:
        results = []
        
        for paper_id in paper_ids:
            try:
# Отправьте задание на анализ бумаги
                task_id = await agent_controller.submit_task(
                    TaskType.PAPER_ANALYSIS,
                    {
                        "paper_id": paper_id,
                        "user_id": user_id,
                        "analysis_type": "quick"  # 批量分析使用快速模式
                    }
                )
                
# Выполняем задачи
                result = await agent_controller.execute_task(task_id)
                
                results.append({
                    "paper_id": paper_id,
                    "task_id": task_id,
                    "success": True,
                    "result": result
                })
                
            except Exception as e:
                results.append({
                    "paper_id": paper_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_papers": len(paper_ids),
            "successful_analyses": sum(1 for r in results if r["success"]),
            "results": results
        }
        
    except Exception as e:
logger.error(f"Ошибка пакетного анализа документов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-pdf", response_model=Dict[str, Any])
async def upload_pdf_for_analysis(file: UploadFile = File(...)):
    """
Загрузить PDF-файлы и проанализировать
Возвратить информацию о файле и результаты анализа
    """
    try:
#Проверяем тип файла
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持 PDF 文件")
        
# Читаем содержимое файла
        logger.info(f"接收到 PDF 文件: {file.filename}")
        pdf_bytes = await file.read()
        
# Разобрать PDF-файл
        pdf_result = await pdf_parser.parse_pdf_from_bytes(pdf_bytes, file.filename)
        
        if not pdf_result.get("success"):
поднять HTTPException(status_code=500, Detail=pdf_result.get("ошибка", "Ошибка анализа PDF"))
        
# Сохраняем файл в каталог загрузок
        os.makedirs("downloads", exist_ok=True)
        file_path = os.path.join("downloads", file.filename)
        
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
        
logger.info(f"PDF-файл сохранен: {file_path}")
        
        return {
            "success": True,
            "filename": file.filename,
            "file_path": f"/uploads/{file.filename}",
            "title": pdf_result.get("title", "未知标题"),
            "authors": pdf_result.get("authors", ["未知作者"]),
            "abstract": pdf_result.get("abstract", "")[:500],  # 限制摘要长度
            "page_count": pdf_result.get("page_count", 0),
            "word_count": pdf_result.get("word_count", 0),
            "message": "PDF 文件上传并解析成功，可以使用返回的 file_path 进行分析"
        }
        
    except HTTPException:
        raise
    except Exception as e:
logger.error(f"Ошибка загрузки PDF: {str(e)}")
поднять HTTPException(status_code=500, Detail=f"Ошибка загрузки: {str(e)}")
