"""
InnoCore AI ассистент по письму (Coach Agent)
Отвечает за перенос стиля, редактуру в реальном времени и объяснение сложных концепций
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from agents.base import BaseAgent
from core.database import db_manager
from core.vector_store import vector_store_manager
from core.exceptions import AgentException

class CoachAgent(BaseAgent):
    """Интеллектуальный агент-ассистент по письму"""
    
    def __init__(self, llm=None):
        super().__init__("Coach", llm)
        
        # Добавить инструменты
        self.add_tool("explain_concept", self._explain_concept, "Объяснение сложных концепций")
        self.add_tool("polish_text", self._polish_text, "Редактирование текста")
        self.add_tool("mimic_style", self._mimic_style, "Имитация стиля письма")
        self.add_tool("get_user_style", self._get_user_style, "Получение стиля письма пользователя")
        self.add_tool("suggest_improvements", self._suggest_improvements, "Предложения по улучшению")
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение задачи ассистента по письму"""
        await self.validate_input(input_data)
        
        self.set_state("running")
        
        try:
            user_id = input_data["user_id"]
            task_type = input_data["task_type"]  # explain, polish, mimic, suggest
            content = input_data["content"]
            context = input_data.get("context", {})
            
            result = None
            
            if task_type == "explain":
                result = await self._handle_explain_task(user_id, content, context)
            elif task_type == "polish":
                result = await self._handle_polish_task(user_id, content, context)
            elif task_type == "mimic":
                result = await self._handle_mimic_task(user_id, content, context)
            elif task_type == "suggest":
                result = await self._handle_suggest_task(user_id, content, context)
            else:
                raise AgentException(f"Неподдерживаемый тип задачи: {task_type}")
            
            self.set_state("completed")
            
            return {
                "status": "success",
                "task_type": task_type,
                "user_id": user_id,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.set_state("error")
            raise AgentException(f"Ошибка выполнения Coach Agent: {str(e)}")
    
    def get_required_fields(self) -> List[str]:
        """Получение обязательных полей ввода"""
        return ["user_id", "task_type", "content"]
    
    async def _handle_explain_task(self, user_id: str, content: str, context: Dict) -> Dict[str, Any]:
        """Обработка задачи объяснения"""
        try:
            # Получить исторические статьи пользователя как контекст
            user_context = await self._get_user_context(user_id)
            
            explain_prompt = f"""
            Объясните, пожалуйста, следующее содержание простым и понятным языком:
            
            Содержание для объяснения:
            {content}
            
            Контекстная информация:
            {json.dumps(context, ensure_ascii=False, indent=2)}
            
            Область исследований пользователя:
            {json.dumps(user_context, ensure_ascii=False, indent=2)}
            
            Пожалуйста, предоставьте:
            1. Простое и понятное объяснение
            2. Примеры или аналогии
            3. Важность в данной области
            4. Возможные сценарии применения
            
            Верните результат в формате JSON.
            """
            
            response = await self.think(explain_prompt)
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = {
                    "explanation": response,
                    "examples": ["Требуется добавить конкретные примеры"],
                    "importance": "Имеет важное значение в соответствующей области",
                    "applications": ["Потенциальные сценарии применения"]
                }
            
            self._add_to_history(f"Задача объяснения выполнена: {content[:50]}...")
            return result
            
        except Exception as e:
            self._add_to_history(f"Задача объяснения не выполнена: {str(e)}")
            return {
                "explanation": f"Ошибка в процессе объяснения: {str(e)}",
                "examples": [],
                "importance": "",
                "applications": []
            }
    
    async def _handle_polish_task(self, user_id: str, content: str, context: Dict) -> Dict[str, Any]:
        """Обработка задачи редактирования"""
        try:
            # Получить предпочтения стиля письма пользователя
            user_style = await self._get_user_writing_style(user_id)
            
            # Получить связанные эталоны стиля
            style_references = await self._get_style_references(user_id, content)
            
            polish_prompt = f"""
            Отредактируйте следующий текст в грамотный академический английский:
            
            Оригинальный текст:
            {content}
            
            Предпочтения стиля письма пользователя:
            {json.dumps(user_style, ensure_ascii=False, indent=2)}
            
            Эталоны стиля:
            {json.dumps(style_references, ensure_ascii=False, indent=2)}
            
            Контекстная информация:
            {json.dumps(context, ensure_ascii=False, indent=2)}
            
            Пожалуйста, предоставьте:
            1. Отредактированный текст на английском
            2. Описание основных изменений
            3. Рекомендации по улучшению стиля
            4. Источники референсных формулировок из статей
            
            Требования:
            - Сохранять исходный смысл
            - Использовать естественные академические выражения
            - Соответствовать стилю целевого журнала/конференции
            - Указать в комментариях, какие формулировки из исторических статей использованы
            
            Верните результат в формате JSON.
            """
            
            response = await self.think(polish_prompt)
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = {
                    "polished_text": response,
                    "modifications": ["Исправление грамматики", "Оптимизация лексики"],
                    "style_suggestions": ["Рекомендуется использовать более формальные выражения"],
                    "references": ["На основе норм академического письма"]
                }
            
            self._add_to_history(f"Задача редактирования выполнена: {content[:50]}...")
            return result
            
        except Exception as e:
            self._add_to_history(f"Задача редактирования не выполнена: {str(e)}")
            return {
                "polished_text": content,
                "modifications": [f"Ошибка в процессе редактирования: {str(e)}"],
                "style_suggestions": [],
                "references": []
            }
    
    async def _handle_mimic_task(self, user_id: str, content: str, context: Dict) -> Dict[str, Any]:
        """Обработка задачи имитации"""
        try:
            # Получить эталон целевого стиля
            target_style = context.get("target_style", "formal_academic")
            reference_papers = context.get("reference_papers", [])
            
            # Если референсные статьи не указаны, получить из библиотеки пользователя
            if not reference_papers:
                reference_papers = await self._get_user_top_papers(user_id, limit=3)
            
            mimic_prompt = f"""
            Перепишите указанное содержание в стиле следующих референсных статей:
            
            Оригинальный текст:
            {content}
            
            Целевой стиль:
            {target_style}
            
            Референсные статьи:
            {json.dumps(reference_papers, ensure_ascii=False, indent=2)}
            
            Контекстная информация:
            {json.dumps(context, ensure_ascii=False, indent=2)}
            
            Пожалуйста, предоставьте:
            1. Переписанный текст
            2. Анализ стиля (как отражён целевой стиль)
            3. Конкретные приёмы имитации
            4. Референсные структуры предложений
            
            Верните результат в формате JSON.
            """
            
            response = await self.think(mimic_prompt)
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = {
                    "rewritten_text": response,
                    "style_analysis": "Переписано в академическом стиле письма",
                    "mimic_techniques": ["Имитация структуры предложений", "Подбор лексики"],
                    "reference_structures": ["Академические формулировки"]
                }
            
            self._add_to_history(f"Задача имитации выполнена: {content[:50]}...")
            return result
            
        except Exception as e:
            self._add_to_history(f"Задача имитации не выполнена: {str(e)}")
            return {
                "rewritten_text": content,
                "style_analysis": f"Ошибка в процессе имитации: {str(e)}",
                "mimic_techniques": [],
                "reference_structures": []
            }
    
    async def _handle_suggest_task(self, user_id: str, content: str, context: Dict) -> Dict[str, Any]:
        """Обработка задачи рекомендаций"""
        try:
            # Получить историю письма пользователя
            user_writing_history = await self._get_user_writing_history(user_id)
            
            suggest_prompt = f"""
            Предоставьте рекомендации по улучшению следующего текста:
            
            Содержание текста:
            {content}
            
            История письма пользователя:
            {json.dumps(user_writing_history, ensure_ascii=False, indent=2)}
            
            Контекстная информация:
            {json.dumps(context, ensure_ascii=False, indent=2)}
            
            Пожалуйста, предоставьте:
            1. Общую оценку
            2. Конкретные рекомендации по улучшению (в порядке важности)
            3. Проблемы грамматики и выражения
            4. Рекомендации по оптимизации структуры
            5. Улучшения академического стиля
            
            Верните результат в формате JSON.
            """
            
            response = await self.think(suggest_prompt)
            
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                result = {
                    "overall_evaluation": "Текст в целом хорошего качества",
                    "improvement_suggestions": ["Рекомендуется усилить логику изложения", "Можно добавить больше деталей"],
                    "grammar_issues": ["Проверить согласованность времён"],
                    "structure_suggestions": ["Рекомендуется оптимизировать структуру абзацев"],
                    "academic_improvements": ["Использовать более формальную академическую лексику"]
                }
            
            self._add_to_history(f"Задача рекомендаций выполнена: {content[:50]}...")
            return result
            
        except Exception as e:
            self._add_to_history(f"Задача рекомендаций не выполнена: {str(e)}")
            return {
                "overall_evaluation": f"Ошибка в процессе анализа: {str(e)}",
                "improvement_suggestions": [],
                "grammar_issues": [],
                "structure_suggestions": [],
                "academic_improvements": []
            }
    
    async def _get_user_context(self, user_id: str) -> Dict[str, Any]:
        """Получение исследовательского профиля пользователя"""
        try:
            user = await db_manager.get_user(user_id)
            if user:
                return user.get("profile", {})
            return {}
        except Exception:
            return {}
    
    async def _get_user_writing_style(self, user_id: str) -> Dict[str, Any]:
        """Получение предпочтений стиля письма пользователя"""
        user_context = await self._get_user_context(user_id)
        return user_context.get("writing_style", {
            "tone": "formal",
            "complexity": "medium",
            "preferred_journals": ["Nature", "Science"],
            "language": "english"
        })
    
    async def _get_style_references(self, user_id: str, content: str) -> List[Dict[str, Any]]:
        """Получение эталонов стиля"""
        try:
            # Поиск связанных статей в библиотеке пользователя
            search_results = await vector_store_manager.hybrid_search(
                query=content,
                user_id=user_id,
                top_k=3,
                include_l2=True,
                include_l1=False
            )
            
            references = []
            for result in search_results:
                payload = result["payload"]
                references.append({
                    "title": payload.get("title", ""),
                    "abstract": payload.get("abstract", "")[:200],
                    "similarity": result["score"]
                })
            
            return references
            
        except Exception:
            return []
    
    async def _get_user_top_papers(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Получение статей пользователя с наивысшим рейтингом"""
        try:
            user_papers = await db_manager.get_user_papers(user_id, limit=limit)
            
            top_papers = []
            for paper in user_papers:
                top_papers.append({
                    "title": paper.get("title", ""),
                    "abstract": paper.get("abstract", "")[:300],
                    "rating": paper.get("rating", 0),
                    "authors": paper.get("authors", [])
                })
            
            return top_papers
            
        except Exception:
            return []
    
    async def _get_user_writing_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Получение истории письма пользователя"""
        try:
            # Здесь должны загружаться данные из истории письма пользователя
            # Временно возвращаем тестовые данные
            return [
                {
                    "date": "2024-01-01",
                    "content_type": "abstract",
                    "word_count": 200,
                    "feedback_score": 4.5
                }
            ]
        except Exception:
            return []
    
    # Методы инструментов
    async def _explain_concept(self, concept: str, context: Dict = None) -> Dict:
        """Инструмент объяснения концепций"""
        return await self._handle_explain_task(
            context.get("user_id", ""), 
            concept, 
            context or {}
        )
    
    async def _polish_text(self, text: str, context: Dict = None) -> Dict:
        """Инструмент редактирования текста"""
        return await self._handle_polish_task(
            context.get("user_id", ""), 
            text, 
            context or {}
        )
    
    async def _mimic_style(self, text: str, target_style: str, context: Dict = None) -> Dict:
        """Инструмент имитации стиля"""
        ctx = context or {}
        ctx["target_style"] = target_style
        return await self._handle_mimic_task(
            ctx.get("user_id", ""), 
            text, 
            ctx
        )
    
    async def _get_user_style(self, user_id: str) -> Dict:
        """Инструмент получения стиля пользователя"""
        return await self._get_user_writing_style(user_id)
    
    async def _suggest_improvements(self, text: str, context: Dict = None) -> Dict:
        """Инструмент предложений по улучшению"""
        return await self._handle_suggest_task(
            context.get("user_id", ""), 
            text, 
            context or {}
        )
