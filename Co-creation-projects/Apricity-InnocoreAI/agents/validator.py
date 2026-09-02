"""
Агент валидатора InnoCore AI
Отвечает за создание справочных форматов и проверку метаданных онлайн.
"""

import asyncio
import aiohttp
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib

from agents.base import BaseAgent
from core.database import db_manager
from core.exceptions import AgentException, ExternalAPIException

class ValidatorAgent(BaseAgent):
"""Агент цензора"""
    
    def __init__(self, llm=None):
        super().__init__("Validator", llm)
        
# Конфигурация API
        self.crossref_base_url = "https://api.crossref.org/works"
        self.google_scholar_url = "https://serpapi.com/search"
        
# Добавить инструменты
self.add_tool("generate_bibtex", self._generate_bibtex, "Создать цитату BibTeX")
        self.add_tool("generate_apa", self._generate_apa, "生成APA格式引用")
        self.add_tool("generate_ieee", self._generate_ieee, "生成IEEE格式引用")
self.add_tool("verify_metadata", self._verify_metadata, "Проверить метаданные")
self.add_tool("crossref_lookup", self._crossref_lookup, "CrossRef查询")
self.add_tool("scholar_lookup", self._scholar_lookup, "Академия Google")
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
"""Выполнение задач по проверке ссылок"""
        await self.validate_input(input_data)
        
        self.set_state("running")
        
        try:
            paper_info = input_data["paper_info"]
            formats = input_data.get("formats", ["bibtex", "apa", "ieee"])
            verify_external = input_data.get("verify_external", True)
            
# 1. Генерируйте ссылки в нескольких форматах
            citations = await self._generate_citations(paper_info, formats)
            
# 2. Метаданные внешней проверки
            verification_result = {}
            if verify_external:
                verification_result = await self._verify_paper_metadata(paper_info)
            
# 3. Объединение и обновление справочной информации
            final_citations = await self._merge_citation_data(
                citations, 
                verification_result, 
                paper_info
            )
            
# 4. Кеширование результатов
            await self._cache_citation_results(final_citations)
            
            self.set_state("completed")
            
            return {
                "status": "success",
                "paper_info": paper_info,
                "citations": final_citations,
                "verification": verification_result,
                "formats_generated": list(citations.keys()),
                "verification_status": verification_result.get("status", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.set_state("error")
            raise AgentException(f"Validator Agent执行失败: {str(e)}")
    
    def get_required_fields(self) -> List[str]:
"""Получить необходимые поля ввода"""
        return ["paper_info"]
    
    async def _generate_citations(self, paper_info: Dict, formats: List[str]) -> Dict[str, Any]:
"""Создание цитат в нескольких форматах"""
        citations = {}
        
        for format_type in formats:
            try:
                if format_type.lower() == "bibtex":
                    citations["bibtex"] = await self._generate_bibtex_citation(paper_info)
                elif format_type.lower() == "apa":
                    citations["apa"] = await self._generate_apa_citation(paper_info)
                elif format_type.lower() == "ieee":
                    citations["ieee"] = await self._generate_ieee_citation(paper_info)
                else:
                    self._add_to_history(f"不支持的引用格式: {format_type}")
                    
            except Exception as e:
                self._add_to_history(f"生成{format_type}格式失败: {str(e)}")
                citations[format_type] = f"生成失败: {str(e)}"
        
        return citations
    
    async def _generate_bibtex_citation(self, paper_info: Dict) -> str:
"""Создание цитат в формате BibTeX"""
# Генерируем ссылочный ключ
        first_author = paper_info.get("authors", [""])[0]
        if isinstance(first_author, str):
            last_name = first_author.split()[-1].lower()
        else:
            last_name = "unknown"
        
        year = paper_info.get("year", datetime.now().year)
        title_words = paper_info.get("title", "").split()[:3]
        title_key = "".join([w.lower() for w in title_words if w.isalpha()])
        
        citation_key = f"{last_name}{year}{title_key}"
        
# Создаем запись BibTeX
        entry_type = self._determine_entry_type(paper_info)
        
        bibtex = f"@{entry_type}{{{citation_key},\n"
        
#Добавить автора
        authors = paper_info.get("authors", [])
        if authors:
            bibtex += f"  author = {{{self._format_bibtex_authors(authors)}}},\n"
        
#Добавить заголовок
        title = paper_info.get("title", "")
        if title:
            bibtex += f"  title = {{{title}}},\n"
        
#Добавить информацию о журнале/конференции
        if entry_type == "article":
            journal = paper_info.get("journal", "")
            if journal:
                bibtex += f"  journal = {{{journal}}},\n"
            
            volume = paper_info.get("volume", "")
            if volume:
                bibtex += f"  volume = {{{volume}}},\n"
            
            number = paper_info.get("number", "")
            if number:
                bibtex += f"  number = {{{number}}},\n"
            
            pages = paper_info.get("pages", "")
            if pages:
                bibtex += f"  pages = {{{pages}}},\n"
        
        elif entry_type == "inproceedings":
            booktitle = paper_info.get("booktitle", "")
            if booktitle:
                bibtex += f"  booktitle = {{{booktitle}}},\n"
            
            pages = paper_info.get("pages", "")
            if pages:
                bibtex += f"  pages = {{{pages}}},\n"
        
#Добавить год
        if year:
            bibtex += f"  year = {{{year}}},\n"
        
# Добавить DOI
        doi = paper_info.get("doi", "")
        if doi:
            bibtex += f"  doi = {{{doi}}},\n"
        
#Добавить URL
        url = paper_info.get("url", "")
        if url:
            bibtex += f"  url = {{{url}}},\n"
        
# Удалить последнюю запятую и закрыть
        bibtex = bibtex.rstrip(",\n") + "\n}"
        
        return bibtex
    
    async def _generate_apa_citation(self, paper_info: Dict) -> str:
"""Создать цитату в формате APA"""
        authors = paper_info.get("authors", [])
        year = paper_info.get("year", "")
        title = paper_info.get("title", "")
        
# Формат автора
        if len(authors) == 0:
            author_text = ""
        elif len(authors) == 1:
            author_text = authors[0]
        elif len(authors) == 2:
            author_text = f"{authors[0]} & {authors[1]}"
        elif len(authors) <= 7:
            author_text = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            author_text = ", ".join(authors[:6]) + f", ... {authors[-1]}"
        
# Создать цитируемость APA
        if year:
            apa_citation = f"{author_text} ({year}). {title}."
        else:
            apa_citation = f"{author_text}. {title}."
        
#Добавляем информацию журнала
        journal = paper_info.get("journal", "")
        volume = paper_info.get("volume", "")
        number = paper_info.get("number", "")
        pages = paper_info.get("pages", "")
        
        if journal:
            if volume and number:
                apa_citation += f" *{journal}*, *{volume}({number})*"
            elif volume:
                apa_citation += f" *{journal}*, *{volume}*"
            else:
                apa_citation += f" *{journal}*"
            
            if pages:
                apa_citation += f", {pages}."
            else:
                apa_citation += "."
        
# Добавить DOI
        doi = paper_info.get("doi", "")
        if doi:
            apa_citation += f" https://doi.org/{doi}"
        
        return apa_citation
    
    async def _generate_ieee_citation(self, paper_info: Dict) -> str:
"""Создать ссылку на формат IEEE"""
        authors = paper_info.get("authors", [])
        year = paper_info.get("year", "")
        title = paper_info.get("title", "")
        
# Автор формата (IEEE использует аббревиатуры)
        ieee_authors = []
        for author in authors[:3]:  # IEEE通常只列出前3个作者
            if isinstance(author, str):
                parts = author.split()
                if len(parts) >= 2:
                    last_name = parts[-1]
                    initials = " ".join([p[0] + "." for p in parts[:-1]])
                    ieee_authors.append(f"{initials} {last_name}")
                else:
                    ieee_authors.append(author)
        
        if len(authors) > 3:
            ieee_authors.append("et al.")
        
        author_text = ", ".join(ieee_authors)
        
# Создаем ссылку IEEE
        if title:
            ieee_citation = f'"{title},"'
        else:
            ieee_citation = ""
        
#Добавляем информацию журнала
        journal = paper_info.get("journal", "")
        volume = paper_info.get("volume", "")
        number = paper_info.get("number", "")
        pages = paper_info.get("pages", "")
        
        if journal:
            if volume and number:
                ieee_citation += f" *{journal}*, vol. {volume}, no. {number}"
            elif volume:
                ieee_citation += f" *{journal}*, vol. {volume}"
            else:
                ieee_citation += f" *{journal}*"
            
            if pages:
                ieee_citation += f", pp. {pages}"
        
#Добавить год и месяц
        if year:
            month = paper_info.get("month", "")
            if month:
                ieee_citation += f", {month}. {year}."
            else:
                ieee_citation += f", {year}."
        
# Добавить DOI
        doi = paper_info.get("doi", "")
        if doi:
            ieee_citation += f" doi: {doi}"
        
        return ieee_citation
    
    def _determine_entry_type(self, paper_info: Dict) -> str:
"""Определить тип записи BibTeX"""
        if paper_info.get("journal"):
            return "article"
        elif paper_info.get("booktitle"):
            return "inproceedings"
        elif paper_info.get("publisher"):
            return "book"
        else:
            return "misc"
    
    def _format_bibtex_authors(self, authors: List[str]) -> str:
"""Формат автора BibTeX"""
        formatted_authors = []
        for author in authors:
            if isinstance(author, str):
# Преобразование «Первый Последний» в «Последний, Первый»
                parts = author.split()
                if len(parts) >= 2:
                    formatted_authors.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
                else:
                    formatted_authors.append(author)
            else:
                formatted_authors.append(str(author))
        
        return " and ".join(formatted_authors)
    
    async def _verify_paper_metadata(self, paper_info: Dict) -> Dict[str, Any]:
        """校验论文元数据"""
        verification_result = {
            "status": "pending",
            "crossref_verified": False,
            "scholar_verified": False,
            "discrepancies": [],
            "suggested_corrections": {},
            "verification_timestamp": datetime.now().isoformat()
        }
        
        doi = paper_info.get("doi", "")
        title = paper_info.get("title", "")
        
        try:
# 1. Проверка перекрестных ссылок
            if doi:
                crossref_data = await self._crossref_lookup_by_doi(doi)
                if crossref_data:
                    verification_result["crossref_verified"] = True
                    discrepancies = self._compare_metadata(paper_info, crossref_data)
                    if discrepancies:
                        verification_result["discrepancies"].extend(discrepancies)
                        verification_result["suggested_corrections"].update(
                            self._generate_corrections(discrepancies)
                        )
            
# 2. Проверка Google Scholar
            if title:
                scholar_data = await self._scholar_lookup_by_title(title)
                if scholar_data:
                    verification_result["scholar_verified"] = True
                    discrepancies = self._compare_metadata(paper_info, scholar_data)
                    if discrepancies:
                        verification_result["discrepancies"].extend(discrepancies)
                        verification_result["suggested_corrections"].update(
                            self._generate_corrections(discrepancies)
                        )
            
# Определить окончательный статус
            if verification_result["crossref_verified"] or verification_result["scholar_verified"]:
                if not verification_result["discrepancies"]:
                    verification_result["status"] = "verified"
                else:
                    verification_result["status"] = "discrepancies_found"
            else:
                verification_result["status"] = "unverified"
            
        except Exception as e:
            verification_result["status"] = "error"
            verification_result["error"] = str(e)
            self._add_to_history(f"元数据校验失败: {str(e)}")
        
        return verification_result
    
    async def _crossref_lookup_by_doi(self, doi: str) -> Optional[Dict]:
"""Запрос CrossRef по DOI"""
        try:
            url = f"{self.crossref_base_url}/{doi}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_crossref_data(data)
                    else:
self._add_to_history(f"Ошибка запроса CrossRef, код состояния: {response.status}")
                        return None
                        
        except Exception as e:
            self._add_to_history(f"CrossRef查询异常: {str(e)}")
            return None
    
    async def _scholar_lookup_by_title(self, title: str) -> Optional[Dict]:
"""Поиск в Академии Google по названию"""
        try:
            config = self.config.external_apis
            if not config.serpapi_key:
self._add_to_history("Ключ SerpApi отсутствует, пропустите запрос Google Scholar")
                return None
            
            params = {
                "engine": "google_scholar",
                "q": title,
                "api_key": config.serpapi_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.google_scholar_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_scholar_data(data)
                    else:
self._add_to_history(f"Ошибка запроса Google Scholar, код состояния: {response.status}")
                        return None
                        
        except Exception as e:
            self._add_to_history(f"Google Scholar查询异常: {str(e)}")
            return None
    
    def _parse_crossref_data(self, data: Dict) -> Dict:
"""Разбор данных CrossRef"""
        message = data.get("message", {})
        
        return {
            "title": " ".join(message.get("title", [])),
            "authors": [f"{author.get('given', '')} {author.get('family', '')}" 
                       for author in message.get("author", [])],
            "year": message.get("published-print", {}).get("date-parts", [[""]])[0][0][:4],
            "journal": message.get("short-container-title", [""])[0],
            "volume": message.get("volume", ""),
            "issue": message.get("issue", ""),
            "page": message.get("page", ""),
            "doi": message.get("DOI", ""),
            "source": "crossref"
        }
    
    def _parse_scholar_data(self, data: Dict) -> Dict:
"""Парсинг данных Google Scholar"""
        organic_results = data.get("organic_results", [])
        if not organic_results:
            return {}
        
        first_result = organic_results[0]
        
#Извлечь год
        publication_info = first_result.get("publication_info", {})
        year = ""
        if "summary" in publication_info:
            year_match = re.search(r'\b(19|20)\d{2}\b', publication_info["summary"])
            if year_match:
                year = year_match.group()
        
        return {
            "title": first_result.get("title", ""),
            "authors": first_result.get("publication_info", {}).get("authors", []),
            "year": year,
            "journal": publication_info.get("summary", "").split(",")[0] if publication_info.get("summary") else "",
            "source": "google_scholar"
        }
    
    def _compare_metadata(self, original: Dict, reference: Dict) -> List[Dict]:
"""Сравнить различия в метаданных"""
        discrepancies = []
        
# Сравнить названия
        orig_title = original.get("title", "").lower().strip()
        ref_title = reference.get("title", "").lower().strip()
        if orig_title and ref_title and orig_title != ref_title:
            discrepancies.append({
                "field": "title",
                "original": original.get("title", ""),
                "reference": reference.get("title", ""),
                "similarity": self._calculate_similarity(orig_title, ref_title)
            })
        
# Сравнить авторов
        orig_authors = set([author.lower() for author in original.get("authors", [])])
        ref_authors = set([author.lower() for author in reference.get("authors", [])])
        if orig_authors and ref_authors and orig_authors != ref_authors:
            discrepancies.append({
                "field": "authors",
                "original": original.get("authors", []),
                "reference": reference.get("authors", []),
                "missing_in_original": list(ref_authors - orig_authors),
                "extra_in_original": list(orig_authors - ref_authors)
            })
        
# Сравнить годы
        orig_year = str(original.get("year", ""))
        ref_year = str(reference.get("year", ""))
        if orig_year and ref_year and orig_year != ref_year:
            discrepancies.append({
                "field": "year",
                "original": orig_year,
                "reference": ref_year
            })
        
        return discrepancies
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
"""Рассчитать сходство текста"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _generate_corrections(self, discrepancies: List[Dict]) -> Dict:
"""Сгенерировать предложения по исправлению"""
        corrections = {}
        
        for discrepancy in discrepancies:
            field = discrepancy["field"]
            if field == "title" and discrepancy.get("similarity", 0) > 0.8:
                corrections[field] = discrepancy["reference"]
            elif field == "year":
                corrections[field] = discrepancy["reference"]
            elif field == "authors":
# Для авторов рекомендуется полный перечень справочной информации.
                corrections[field] = discrepancy["reference"]
        
        return corrections
    
    async def _merge_citation_data(self, citations: Dict, verification: Dict, paper_info: Dict) -> Dict[str, Any]:
"""Объединить справочные данные"""
        final_citations = {}
        
        for format_type, citation_text in citations.items():
если isinstance(citation_text, str), а не citation_text.startswith("Генерация не удалась"):
#Добавить отметку статуса проверки
                verification_status = verification.get("status", "unknown")
                
                if verification_status == "verified":
                    citation_text += "  % [Verified]"
                elif verification_status == "discrepancies_found":
                    citation_text += "  % [Discrepancies Found]"
                else:
                    citation_text += "  % [Unverified]"
                
                final_citations[format_type] = citation_text
            else:
                final_citations[format_type] = citation_text
        
#Добавляем метаданные
        final_citations["metadata"] = {
            "original_info": paper_info,
            "verification": verification,
            "generated_formats": list(citations.keys()),
            "generation_timestamp": datetime.now().isoformat()
        }
        
        return final_citations
    
    async def _cache_citation_results(self, citations: Dict):
"""Кэшировать результаты ссылок"""
        try:
            metadata = citations.get("metadata", {})
            original_info = metadata.get("original_info", {})
            doi = original_info.get("doi", "")
            
            if doi:
# Кэшируем формат BibTeX
                bibtex = citations.get("bibtex", "")
                if bibtex and not bibtex.startswith("生成失败"):
                    verification = metadata.get("verification", {})
                    is_verified = verification.get("status") == "verified"
                    
                    await db_manager.cache_reference(
                        doi=doi,
                        bibtex=bibtex,
                        is_verified=is_verified
                    )
                    
                    self._add_to_history(f"引用已缓存: {doi}")
                    
        except Exception as e:
            self._add_to_history(f"缓存引用失败: {str(e)}")
    
# Служебные методы
    async def _generate_bibtex(self, paper_info: Dict) -> str:
"""Создание инструментов BibTeX"""
        return await self._generate_bibtex_citation(paper_info)
    
    async def _generate_apa(self, paper_info: Dict) -> str:
        """生成APA工具"""
        return await self._generate_apa_citation(paper_info)
    
    async def _generate_ieee(self, paper_info: Dict) -> str:
        """生成IEEE工具"""
        return await self._generate_ieee_citation(paper_info)
    
    async def _verify_metadata(self, paper_info: Dict) -> Dict:
"""Инструмент проверки метаданных"""
        return await self._verify_paper_metadata(paper_info)
    
    async def _crossref_lookup(self, identifier: str) -> Dict:
"""Инструмент запроса CrossRef"""
        if identifier.startswith("10."):  # DOI
            return await self._crossref_lookup_by_doi(identifier)
        else:
return {"error": "Укажите действительный DOI"}
    
    async def _scholar_lookup(self, title: str) -> Dict:
"""Инструмент запросов Google Scholar"""
        return await self._scholar_lookup_by_title(title)