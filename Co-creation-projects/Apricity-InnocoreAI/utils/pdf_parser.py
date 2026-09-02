"""
Инструмент анализа PDF-файлов
Поддерживает извлечение текста, названия, автора и другой информации из файлов PDF.
"""

import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class PDFParser:
"""Парсер PDF"""
    
    def __init__(self):
"""Инициализировать анализатор PDF"""
        self.supported_formats = ['.pdf']
    
    async def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
Разбирать PDF-файлы
        
        Args:
file_path: путь к PDF-файлу
            
        Returns:
            包含解析结果的字典
        """
        try:
            import pdfplumber
            
            logger.info(f"开始解析 PDF: {file_path}")
            
            with pdfplumber.open(file_path) as pdf:
# Извлечь весь текст
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                if not full_text.strip():
                    logger.warning("PDF 文件为空或无法提取文本")
                    return {
                        "success": False,
"error": "Невозможно извлечь текст из PDF"
                    }
                
# Извлечь метаданные
                metadata = pdf.metadata or {}
                
# Попробуйте извлечь заголовок из текста (обычно первые несколько строк первой страницы)
                title = self._extract_title(full_text, metadata)
                
# Попробуйте извлечь автора
                authors = self._extract_authors(full_text, metadata)
                
# Попробуйте извлечь резюме
                abstract = self._extract_abstract(full_text)
                
# Статистика
                page_count = len(pdf.pages)
                word_count = len(full_text.split())
                
                result = {
                    "success": True,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "full_text": full_text,
                    "page_count": page_count,
                    "word_count": word_count,
                    "metadata": {
                        "creator": metadata.get("/Creator", ""),
                        "producer": metadata.get("/Producer", ""),
                        "subject": metadata.get("/Subject", ""),
                        "keywords": metadata.get("/Keywords", "")
                    }
                }
                
logger.info(f"PDF успешно проанализирован: страниц: {page_count}, слов: {word_count}")
                return result
                
        except ImportError:
logger.error("pdfplumber не установлен")
            return {
                "success": False,
                "error": "PDF 解析库未安装，请运行: pip install pdfplumber"
            }
        except Exception as e:
logger.error(f"Ошибка анализа PDF: {str(e)}")
            return {
                "success": False,
"ошибка": f"Ошибка анализа PDF: {str(e)}"
            }
    
    def _extract_title(self, text: str, metadata: Dict) -> str:
"""Извлечение заголовков из текста или метаданных"""
# Сначала попытаемся получить из метаданных
        if metadata.get("/Title"):
            return metadata["/Title"]
        
# Извлеките первые несколько строк текста (обычно заголовок находится спереди, а шрифт крупнее)
        lines = text.split('\n')
        for i, line in enumerate(lines[:10]):  # 只检查前10行
            line = line.strip()
# Заголовки обычно длиннее и не содержат специальных символов.
            if len(line) > 10 and len(line) < 200 and not line.startswith(('http', 'www', '@')):
# Исключаем некоторые общие строки, не относящиеся к заголовку
                if not any(keyword in line.lower() for keyword in ['abstract', 'introduction', 'page', 'arxiv']):
                    return line
        
вернуть «Неизвестное название»
    
    def _extract_authors(self, text: str, metadata: Dict) -> list:
"""Извлечь автора из текста или метаданных"""
        authors = []
        
# Сначала попытаемся получить из метаданных
        if metadata.get("/Author"):
            author_str = metadata["/Author"]
            authors = [a.strip() for a in re.split(r'[,;]', author_str) if a.strip()]
            if authors:
                return authors
        
# Выдержка из текста (обычно после заголовка)
        lines = text.split('\n')
        for i, line in enumerate(lines[:20]):  # 检查前20行
            line = line.strip()
# Найти строки, содержащие информацию об авторе (обычно адрес электронной почты или учреждение)
            if '@' in line or 'university' in line.lower() or 'institute' in line.lower():
# Попробуйте извлечь первые несколько строк имени автора
                for j in range(max(0, i-3), i):
                    potential_author = lines[j].strip()
                    if potential_author and len(potential_author) < 100:
# Простое сопоставление шаблонов имен
                        if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+', potential_author):
                            authors.append(potential_author)
        
вернуть авторов, если авторы еще ["Неизвестный автор"]
    
    def _extract_abstract(self, text: str) -> str:
"""Извлечение резюме из текста"""
# Найти абстрактное ключевое слово
        abstract_patterns = [
            r'Abstract\s*[:\-]?\s*(.*?)(?=\n\n|\nIntroduction|\n1\.|\nKeywords)',
            r'ABSTRACT\s*[:\-]?\s*(.*?)(?=\n\n|\nINTRODUCTION|\n1\.|\nKEYWORDS)',
            r'摘要\s*[:\-]?\s*(.*?)(?=\n\n|关键词|引言|1\.)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                abstract = match.group(1).strip()
# Ограничить длину сводки
                if len(abstract) > 50 and len(abstract) < 2000:
                    return abstract[:1000]  # 最多返回1000字符
        
# Если не найден, вернуть первые 500 символов в виде сводки
        return text[:500].strip() + "..."
    
    async def parse_pdf_from_bytes(self, pdf_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
        """
Разобрать PDF из байтового потока
        
        Args:
pdf_bytes: Байтовое содержимое PDF-файла.
имя_файла: имя файла (для журналов)
            
        Returns:
            包含解析结果的字典
        """
        try:
            import pdfplumber
            import io
            
            logger.info(f"开始解析 PDF 字节流: {filename}")
            
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
# Извлечь весь текст
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
                
                if not full_text.strip():
                    return {
                        "success": False,
"error": "Невозможно извлечь текст из PDF"
                    }
                
# Извлечь метаданные
                metadata = pdf.metadata or {}
                
# Извлечение информации
                title = self._extract_title(full_text, metadata)
                authors = self._extract_authors(full_text, metadata)
                abstract = self._extract_abstract(full_text)
                
                result = {
                    "success": True,
                    "title": title,
                    "authors": authors,
                    "abstract": abstract,
                    "full_text": full_text,
                    "page_count": len(pdf.pages),
                    "word_count": len(full_text.split()),
                    "metadata": {
                        "creator": metadata.get("/Creator", ""),
                        "producer": metadata.get("/Producer", ""),
                        "subject": metadata.get("/Subject", ""),
                        "keywords": metadata.get("/Keywords", "")
                    }
                }
                
logger.info(f"Поток байтов PDF успешно проанализирован")
                return result
                
        except Exception as e:
logger.error(f"Ошибка анализа потока байтов PDF: {str(e)}")
            return {
                "success": False,
"ошибка": f"Ошибка анализа PDF: {str(e)}"
            }


# Глобальный экземпляр парсера PDF
pdf_parser = PDFParser()
