"""
Служба задач
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from ..core.database import get_db
from ..models.task import TaskDB, Task, TaskCreate, TaskUpdate
from ..core.exceptions import TaskNotFoundError
from ..agents.controller import AgentController
import json
import asyncio

class TaskService:
"""Класс обслуживания задач"""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_controller = AgentController()
    
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
"""Получать задачи по ID"""
        task_db = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task_db:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
        return Task.from_orm(task_db)
    
    def get_tasks_by_user(self, user_id: int, skip: int = 0, limit: int = 20) -> List[Task]:
"""Получить список задач пользователя"""
        tasks_db = self.db.query(TaskDB).filter(
            TaskDB.user_id == user_id
        ).order_by(TaskDB.created_at.desc()).offset(skip).limit(limit).all()
        return [Task.from_orm(task) for task in tasks_db]
    
    def create_task(self, task_create: TaskCreate, user_id: int) -> Task:
"""Создать задачу"""
        task_db = TaskDB(
            title=task_create.title,
            description=task_create.description,
            task_type=task_create.task_type,
            priority=task_create.priority,
            parameters=task_create.parameters,
            user_id=user_id
        )
        
        self.db.add(task_db)
        self.db.commit()
        self.db.refresh(task_db)
        
# Выполнять задачи асинхронно
        self._execute_task_async(task_db.id)
        
        return Task.from_orm(task_db)
    
    def update_task(self, task_id: int, task_update: TaskUpdate) -> Task:
"""Задание обновления"""
        task_db = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task_db:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
        
#Обновить поля
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task_db, field, value)
        
        # 如果任务完成，设置完成时间
        if task_update.status == "completed":
            task_db.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(task_db)
        
        return Task.from_orm(task_db)
    
    def delete_task(self, task_id: int) -> bool:
"""Удалить задачу"""
        task_db = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task_db:
            raise TaskNotFoundError(f"Task with id {task_id} not found")
        
        self.db.delete(task_db)
        self.db.commit()
        
        return True
    
    def cancel_task(self, task_id: int) -> Task:
"""Отменить задачу"""
        return self.update_task(task_id, TaskUpdate(status="failed", error_message="Task cancelled by user"))
    
    def retry_task(self, task_id: int) -> Task:
"""Повторить задачу"""
#Сбросить статус задачи
        task = self.update_task(task_id, TaskUpdate(
            status="pending",
            progress=0,
            error_message=None
        ))
        
# Повторно выполняем задачу
        self._execute_task_async(task_id)
        
        return task
    
    def get_task_statistics(self, user_id: int) -> Dict[str, Any]:
"""Получить статистику задач"""
        total_tasks = self.db.query(TaskDB).filter(TaskDB.user_id == user_id).count()
        
# Статистика по статусам
        status_stats = self.db.query(
            TaskDB.status,
            self.db.func.count(TaskDB.id)
        ).filter(TaskDB.user_id == user_id).group_by(TaskDB.status).all()
        
# Статистика по типам
        type_stats = self.db.query(
            TaskDB.task_type,
            self.db.func.count(TaskDB.id)
        ).filter(TaskDB.user_id == user_id).group_by(TaskDB.task_type).all()
        
# Уровень успеха
        completed_tasks = self.db.query(TaskDB).filter(
            and_(TaskDB.user_id == user_id, TaskDB.status == "completed")
        ).count()
        
        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'success_rate': success_rate,
            'status_distribution': dict(status_stats),
            'type_distribution': dict(type_stats)
        }
    
    def _execute_task_async(self, task_id: int):
"""Выполнять задачи асинхронно"""
        try:
            # 获取任务信息
            task_db = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
            if not task_db:
                return
            
# Обновить статус задачи на выполнение
            task_db.status = "running"
            task_db.progress = 0
            self.db.commit()
            
# Запускаем соответствующий агент согласно типу задачи
            if task_db.task_type == "literature_search":
                result = asyncio.run(self._execute_literature_search(task_db))
            elif task_db.task_type == "analysis":
                result = asyncio.run(self._execute_analysis(task_db))
            elif task_db.task_type == "writing":
                result = asyncio.run(self._execute_writing(task_db))
            else:
                raise ValueError(f"Unknown task type: {task_db.task_type}")
            
# Обновить результаты задачи
            task_db.status = "completed"
            task_db.progress = 100
            task_db.results = result
            task_db.completed_at = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
#Обновить статус задачи на неудачный
            task_db.status = "failed"
            task_db.error_message = str(e)
            self.db.commit()
    
    async def _execute_literature_search(self, task_db: TaskDB) -> Dict[str, Any]:
"""Выполнение заданий по поиску литературы"""
        parameters = task_db.parameters or {}
        query = parameters.get('query', '')
        max_papers = parameters.get('max_papers', 20)
        
# Используйте агента охотника для поиска литературы
        hunter_agent = self.agent_controller.get_agent('hunter')
        
# Обновление прогресса
        await self._update_task_progress(task_db.id, 20)
        
# Выполнить поиск
        search_results = await hunter_agent.search_papers(query, max_papers)
        
# Обновление прогресса
        await self._update_task_progress(task_db.id, 60)
        
# Используйте майнер-агент для глубокого майнинга
        miner_agent = self.agent_controller.get_agent('miner')
        enriched_results = await miner_agent.enrich_papers(search_results)
        
# Обновление прогресса
        await self._update_task_progress(task_db.id, 90)
        
# Сохраняем статью в базу данных
        paper_service = PaperService(self.db)
        saved_papers = []
        for paper_data in enriched_results:
            try:
                paper = paper_service.create_paper(
                    PaperCreate(**paper_data),
                    task_db.user_id
                )
                saved_papers.append(paper.dict())
            except Exception as e:
                print(f"Error saving paper: {e}")
        
        return {
            'query': query,
            'total_found': len(enriched_results),
            'papers_saved': len(saved_papers),
            'papers': saved_papers
        }
    
    async def _execute_analysis(self, task_db: TaskDB) -> Dict[str, Any]:
        """执行分析任务"""
        parameters = task_db.parameters or {}
        paper_ids = parameters.get('paper_ids', [])
        analysis_type = parameters.get('analysis_type', 'comprehensive')
        
# Используйте агент тренера для анализа
        coach_agent = self.agent_controller.get_agent('coach')
        
# Обновление прогресса
        await self._update_task_progress(task_db.id, 30)
        
# Выполнить анализ
        analysis_result = await coach_agent.analyze_papers(paper_ids, analysis_type)
        
# Обновление прогресса
        await self._update_task_progress(task_db.id, 80)
        
# Сохранить результаты анализа
        analysis_service = AnalysisService(self.db)
        analysis = analysis_service.create_analysis(
            {
                'title': f"Analysis of {len(paper_ids)} papers",
                'analysis_type': analysis_type,
                'paper_ids': paper_ids,
                'methodology': analysis_result.get('methodology', ''),
                'findings': analysis_result.get('findings', {}),
                'insights': analysis_result.get('insights', ''),
                'limitations': analysis_result.get('limitations', ''),
                'recommendations': analysis_result.get('recommendations', ''),
                'confidence_score': analysis_result.get('confidence_score', 0.0),
                'novelty_score': analysis_result.get('novelty_score', 0.0),
                'impact_score': analysis_result.get('impact_score', 0.0)
            },
            task_db.user_id,
            task_db.id
        )
        
        return {
            'analysis_id': analysis.id,
            'analysis_type': analysis_type,
            'papers_analyzed': len(paper_ids),
            'result': analysis.dict()
        }
    
    async def _execute_writing(self, task_db: TaskDB) -> Dict[str, Any]:
"""Выполнение письменных заданий"""
        parameters = task_db.parameters or {}
        paper_ids = parameters.get('paper_ids', [])
        writing_type = parameters.get('writing_type', 'review')
        outline = parameters.get('outline')
        
# Используйте тренерский агент для записи
        coach_agent = self.agent_controller.get_agent('coach')
        
# Обновление прогресса
        await self._update_task_progress(task_db.id, 25)
        
# Генерация контента
        writing_result = await coach_agent.generate_writing(paper_ids, writing_type, outline)
        
# Обновление прогресса
        await self._update_task_progress(task_db.id, 75)
        
# Сохранить результаты записи
        writing_service = WritingService(self.db)
        writing = writing_service.create_writing(
            {
                'title': writing_result.get('title', 'Generated Writing'),
                'writing_type': writing_type,
                'content': writing_result.get('content', ''),
                'outline': writing_result.get('outline', []),
                'sections': writing_result.get('sections', {}),
                'citations': writing_result.get('citations', []),
                'paper_ids': paper_ids
            },
            task_db.user_id,
            task_db.id
        )
        
        return {
            'writing_id': writing.id,
            'writing_type': writing_type,
            'papers_referenced': len(paper_ids),
            'word_count': writing.word_count,
            'result': writing.dict()
        }
    
    async def _update_task_progress(self, task_id: int, progress: int):
"""Обновить ход выполнения задачи"""
        task_db = self.db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if task_db:
            task_db.progress = progress
            self.db.commit()