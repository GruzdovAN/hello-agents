"""
InnoCore AI Insight Expert (Агент майнера)
Основной мозг. Отвечает за чтение, понимание, поиск в исторических базах данных, сравнительный анализ и составление отчетов.
"""

import asyncio
from typing import Dict, List, Optional, Any
import json
import re
from datetime import datetime

from agents.base import BaseAgent
from core.database import db_manager
from core.vector_store import vector_store_manager
from core.exceptions import AgentException

class MinerAgent(BaseAgent):
"""Эксперт-агент Insight"""
    
    def __init__(self, llm=None):
        super().__init__("Miner", llm)
        
# Добавить инструменты
        self.add_tool("parse_pdf", self._parse_pdf, "解析PDF文件")
self.add_tool("search_memory", self._search_memory, "поиск в памяти")
        self.add_tool("compare_papers", self._compare_papers, "对比论文")
self.add_tool("generate_report", self._generate_report, "Создать аналитический отчет")
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
"""Выполнение бумажного анализа и задач по поиску инноваций"""
        await self.validate_input(input_data)
        
        self.set_state("running")
        
        try:
            paper_id = input_data["paper_id"]
            user_id = input_data.get("user_id")
            analysis_type = input_data.get("analysis_type", "full")  # full, quick, innovation_only
            
# Получить информацию о бумаге
            paper = await db_manager.get_paper(paper_id)
            if not paper:
                raise AgentException(f"论文不存在: {paper_id}")
            
            self._add_to_history(f"开始分析论文: {paper['title']}")
            
# 1. Анализ PDF-контента
            parsed_content = await self._parse_paper_content(paper)
            
# 2. Найдите соответствующие исторические документы
            related_papers = await self._find_related_papers(
                paper["title"], 
                paper["abstract"], 
                user_id
            )
            
№3. Провести сравнительный анализ
            comparison_result = await self._perform_comparison_analysis(
                parsed_content, 
                related_papers
            )
            
# 4. Создать отчет об анализе
            report = await self._create_analysis_report(
                paper, 
                parsed_content, 
                related_papers, 
                comparison_result,
                user_id
            )
            
# 5. Сохраняем отчет в базу данных
            report_id = await self._save_analysis_report(paper_id, report, user_id)
            
# 6. Обновить векторную библиотеку
            await self._update_vector_store(paper_id, paper, parsed_content, user_id)
            
            self.set_state("completed")
            
            return {
                "status": "success",
                "paper_id": paper_id,
                "report_id": report_id,
                "analysis_type": analysis_type,
                "parsed_content": {
                    "sections": list(parsed_content.get("sections", {}).keys()),
                    "word_count": parsed_content.get("word_count", 0)
                },
                "related_papers_count": len(related_papers),
                "report_summary": {
                    "summary": report.get("summary", "")[:200] + "...",
                    "innovation_points": len(report.get("innovation_points", [])),
                    "limitations": len(report.get("limitations", [])),
                    "future_ideas": len(report.get("future_ideas", []))
                }
            }
            
        except Exception as e:
            self.set_state("error")
            raise AgentException(f"Miner Agent执行失败: {str(e)}")
    
    def get_required_fields(self) -> List[str]:
"""Получить необходимые поля ввода"""
        return ["paper_id"]
    
    async def _parse_paper_content(self, paper: Dict) -> Dict[str, Any]:
"""Проанализируйте содержание статьи"""
        file_path = paper.get("file_path")
        if not file_path:
# Если PDF-файла нет, используйте заголовок и краткое описание
            return {
                "title": paper.get("title", ""),
                "abstract": paper.get("abstract", ""),
                "sections": {
                    "abstract": paper.get("abstract", ""),
                    "introduction": "",
                    "method": "",
                    "experiment": "",
                    "conclusion": ""
                },
                "word_count": len(paper.get("abstract", "").split()),
                "parsing_method": "metadata_only"
            }
        
#Здесь следует использовать специальную библиотеку синтаксического анализа PDF-файлов.
# Временно возвращаем смоделированный структурированный контент
        return await self._extract_structured_content(file_path)
    
    async def _extract_structured_content(self, file_path: str) -> Dict[str, Any]:
"""Извлечение структурированного контента"""
        try:
# Сюда следует интегрировать Nougat или PyMuPDF для углубленного анализа.
            # 暂时返回模拟数据
            mock_content = {
                "title": "Sample Paper Title",
                "abstract": "This is a sample abstract...",
                "sections": {
                    "introduction": "In this paper, we propose...",
                    "method": "Our method consists of...",
                    "experiment": "We conducted experiments...",
                    "conclusion": "The results show that..."
                },
                "word_count": 1500,
                "parsing_method": "mock_parser"
            }
            
            self._add_to_history(f"PDF解析完成: {file_path}")
            return mock_content
            
        except Exception as e:
            self._add_to_history(f"PDF解析失败: {str(e)}")
            return {
                "title": "",
                "abstract": "",
                "sections": {},
                "word_count": 0,
                "parsing_method": "failed"
            }
    
    async def _find_related_papers(self, title: str, abstract: str, user_id: str = None) -> List[Dict]:
"""Найти похожие статьи"""
        try:
# Построить запрос
            query = f"{title} {abstract}"
            
            # 执行混合搜索
            search_results = await vector_store_manager.hybrid_search(
                query=query,
                user_id=user_id,
                top_k=10,
                include_l1=True,
                include_l2=bool(user_id)
            )
            
# Получите подробную информацию о бумаге
            related_papers = []
            for result in search_results:
                payload = result["payload"]
                paper_id = payload.get("paper_id")
                
                if paper_id:
                    paper_info = await db_manager.get_paper(paper_id)
                    if paper_info:
                        paper_info["similarity_score"] = result["score"]
                        paper_info["collection_type"] = result["collection_type"]
                        related_papers.append(paper_info)
            
            self._add_to_history(f"找到 {len(related_papers)} 篇相关论文")
            return related_papers
            
        except Exception as e:
            self._add_to_history(f"搜索相关论文失败: {str(e)}")
            return []
    
    async def _perform_comparison_analysis(self, current_paper: Dict, related_papers: List[Dict]) -> Dict[str, Any]:
"""Провести сравнительный анализ"""
        if not related_papers:
            return {
                "comparison_summary": "未找到相关论文进行对比",
                "unique_contributions": [],
                "similar_works": [],
                "gaps_identified": []
            }
        
# Создайте подсказку для сравнительного анализа
        comparison_prompt = f"""
        请分析当前论文与历史相关论文的对比情况：
        
Текущие статьи:
Заголовок: {current_paper.get('title', '')}
Текст: {current_paper.get('abstract', '')}
        主要内容：{str(current_paper.get('sections', {}))[:1000]}...
        
Сопутствующие документы:
        {self._format_related_papers_for_comparison(related_papers[:5])}
        
Проведите сравнительный анализ со следующих точек зрения:
1. Инновации и улучшения метода.
2. Преимущества экспериментального дизайна
3. Отличия от существующих работ
4. Возможные пробелы в исследованиях
        
Пожалуйста, верните результаты анализа в формате JSON.
        """
        
        try:
            response = await self.think(comparison_prompt)
            
# Попробуйте проанализировать ответ JSON
            try:
                comparison_result = json.loads(response)
            except json.JSONDecodeError:
# Если анализ JSON не удался, используйте анализ текста
                comparison_result = self._parse_text_comparison(response)
            
self._add_to_history("Сравнительный анализ завершен")
            return comparison_result
            
        except Exception as e:
            self._add_to_history(f"对比分析失败: {str(e)}")
            return {
                "comparison_summary": "对比分析过程中出现错误",
                "unique_contributions": [],
                "similar_works": [],
                "gaps_identified": []
            }
    
    def _format_related_papers_for_comparison(self, papers: List[Dict]) -> str:
"""Отформатируйте связанные статьи для сравнения"""
        formatted = []
        for i, paper in enumerate(papers, 1):
            formatted.append(f"""
Бумага {i}:
Заголовок: {paper.get('title', '')}
            摘要：{paper.get('abstract', '')[:300]}...
            相似度：{paper.get('similarity_score', 0):.3f}
            """)
        return "\n".join(formatted)
    
    def _parse_text_comparison(self, text: str) -> Dict[str, Any]:
"""Результаты сравнения разобранных текстовых форматов"""
# Простая логика анализа текста
        return {
            "comparison_summary": text[:500],
            "unique_contributions": ["基于文本分析的创新点"],
"similar_works": ["Сопутствующие исследования"],
"gaps_identified": ["Исследование по выявлению пробелов"]
        }
    
    async def _create_analysis_report(self, paper: Dict, parsed_content: Dict, 
                                    related_papers: List[Dict], comparison_result: Dict,
                                    user_id: str = None) -> Dict[str, Any]:
        """创建分析报告"""
        
        report_prompt = f"""
Создайте подробный отчет по анализу бумаги на основе следующей информации:
        
Информация о бумаге:
Заголовок: {paper.get('title', '')}
        作者：{', '.join(paper.get('authors', []))}
Аннотация: {paper.get('abstract', '')}
        
Разобрать содержимое:
        {str(parsed_content.get('sections', {}))[:1500]}...
        
Результаты сравнительного анализа:
        {str(comparison_result)[:1000]}...
        
Создайте отчет со следующими разделами:
1. Резюме. Обзор основных материалов и методов, использованных в статье.
2. Инновации – инновационные моменты по сравнению с соответствующими статьями.
3. Ограничение. Ограничения настоящего исследования.
4. Идеи на будущее – предложения по будущим направлениям исследований, основанные на анализе.
        
Пожалуйста, верните отчет в формате JSON.
        """
        
        try:
            response = await self.think(report_prompt)
            
# Попробуйте проанализировать ответ JSON
            try:
                report = json.loads(response)
            except json.JSONDecodeError:
# Если анализ JSON не удался, создайте отчет по умолчанию
                report = self._generate_default_report(paper, parsed_content, comparison_result)
            
#Добавляем метаданные
            report.update({
                "paper_id": paper.get("id"),
                "generated_for_user_id": user_id,
                "generated_at": datetime.now().isoformat(),
                "related_papers_count": len(related_papers),
                "analysis_method": "miner_agent"
            })
            
self._add_to_history("Создание аналитического отчета завершено")
            return report
            
        except Exception as e:
            self._add_to_history(f"生成分析报告失败: {str(e)}")
            return self._generate_default_report(paper, parsed_content, comparison_result)
    
    def _generate_default_report(self, paper: Dict, parsed_content: Dict, comparison_result: Dict) -> Dict[str, Any]:
"""Создать отчет по умолчанию"""
        return {
            "summary": f"本文提出了{paper.get('title', '')}相关的研究工作。",
            "innovation_points": ["需要进一步分析的创新点"],
«ограничения»: [«Выявленные ограничения исследования»],
"future_ideas": ["Предлагаемые направления будущих исследований"],
            "paper_id": paper.get("id"),
            "generated_at": datetime.now().isoformat(),
            "analysis_method": "default"
        }
    
    async def _save_analysis_report(self, paper_id: str, report: Dict, user_id: str = None) -> str:
"""Сохранить отчет об анализе в базу данных"""
        try:
            report_id = await db_manager.create_analysis_report(
                paper_id=paper_id,
                summary=report.get("summary", ""),
                innovation_point=json.dumps(report.get("innovation_points", []), ensure_ascii=False),
                limitation=json.dumps(report.get("limitations", []), ensure_ascii=False),
                future_idea=json.dumps(report.get("future_ideas", []), ensure_ascii=False),
                vector_ids=report.get("vector_ids", {}),
                user_id=user_id
            )
            
            self._add_to_history(f"分析报告已保存: {report_id}")
            return report_id
            
        except Exception as e:
            self._add_to_history(f"保存分析报告失败: {str(e)}")
            return ""
    
    async def _update_vector_store(self, paper_id: str, paper: Dict, parsed_content: Dict, user_id: str = None):
"""Обновить векторную библиотеку"""
        try:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            
# Объединить контент
            content = f"{title} {abstract}"
            sections = parsed_content.get("sections", {})
            if sections:
                content += " " + " ".join(sections.values())
            
            # 添加到L2用户库
            if user_id:
                await vector_store_manager.add_to_l2(
                    user_id=user_id,
                    paper_id=paper_id,
                    title=title,
                    abstract=abstract,
                    content=content,
                    metadata={
                        "authors": paper.get("authors", []),
                        "sections": list(sections.keys()),
                        "word_count": parsed_content.get("word_count", 0),
                        "analysis_date": datetime.now().isoformat()
                    }
                )
                self._add_to_history(f"论文已添加到用户向量库: {user_id}")
            
        except Exception as e:
            self._add_to_history(f"更新向量库失败: {str(e)}")
    
# Служебные методы
    async def _parse_pdf(self, file_path: str) -> Dict:
"""Инструмент анализа PDF"""
        return await self._extract_structured_content(file_path)
    
    async def _search_memory(self, query: str, user_id: str = None) -> List[Dict]:
"""Инструмент поиска в памяти"""
        try:
            results = await vector_store_manager.hybrid_search(
                query=query,
                user_id=user_id,
                top_k=5
            )
            return [{"id": r["id"], "score": r["score"], "payload": r["payload"]} for r in results]
        except Exception as e:
            return [{"error": str(e)}]
    
    async def _compare_papers(self, current_paper: Dict, related_papers: List[Dict]) -> Dict:
"""Инструмент сравнительного эссе"""
        return await self._perform_comparison_analysis(current_paper, related_papers)
    
    async def _generate_report(self, paper_info: Dict, analysis_result: Dict) -> Dict:
"""Инструмент создания отчетов"""
        return await self._create_analysis_report(
            paper_info, 
            analysis_result.get("parsed_content", {}),
            analysis_result.get("related_papers", []),
            analysis_result.get("comparison_result", {})
        )