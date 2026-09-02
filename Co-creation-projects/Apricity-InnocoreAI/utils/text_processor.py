"""
Инструмент обработки текста InnoCore AI
"""

import re
from typing import List, Dict, Optional, Any, Tuple
import string
from collections import Counter
import asyncio

class TextProcessor:
"""Текстовый процессор"""
    
    def __init__(self):
        self.stop_words = self._load_stop_words()
        self.punctuation = string.punctuation
    
    def _load_stop_words(self) -> set:
        """加载停用词"""
# Упрощенный список стоп-слов
        return {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
            'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours',
            'hers', 'ours', 'theirs', 'what', 'which', 'who', 'whom', 'whose',
            'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now', 'also'
        }
    
    def clean_text(self, text: str) -> str:
"""Чистый текст"""
        if not text:
            return ""
        
# Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text)
        
# Удалить специальные символы (сохранить базовую пунктуацию)
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/\\]', ' ', text)
        
# Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
"""Причастие"""
        if not text:
            return []
        
#Преобразование в нижний регистр и сегментация слов
        words = text.lower().split()
        
# Удалить знаки препинания
        words = [word.strip(self.punctuation) for word in words]
        
# Фильтровать пустые строки
        words = [word for word in words if word]
        
        return words
    
    def remove_stop_words(self, words: List[str]) -> List[str]:
"""Удалить стоп-слова"""
        return [word for word in words if word not in self.stop_words]
    
    def extract_sentences(self, text: str) -> List[str]:
"""Извлечение предложений"""
        if not text:
            return []
        
# Используйте регулярные выражения для разделения предложений
        sentences = re.split(r'[.!?]+', text)
        
# Очистите и отфильтруйте
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def extract_paragraphs(self, text: str) -> List[str]:
"""Извлечь абзац"""
        if not text:
            return []
        
# Разделить абзацы двойным переносом строки
        paragraphs = re.split(r'\n\s*\n', text)
        
# Очистите и отфильтруйте
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """计算文本可读性指标"""
        if not text:
            return {"flesch_score": 0.0, "avg_sentence_length": 0.0, "avg_word_length": 0.0}
        
        sentences = self.extract_sentences(text)
        words = self.tokenize(text)
        
        if not sentences or not words:
            return {"flesch_score": 0.0, "avg_sentence_length": 0.0, "avg_word_length": 0.0}
        
# Средняя длина предложения
        avg_sentence_length = len(words) / len(sentences)
        
# средняя длина слова
        avg_word_length = sum(len(word) for word in words) / len(words)
        
# Упрощенная оценка легкости чтения Флеша
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
        
        return {
            "flesch_score": max(0, min(100, flesch_score)),
            "avg_sentence_length": avg_sentence_length,
            "avg_word_length": avg_word_length
        }
    
    def extract_key_phrases(self, text: str, max_phrases: int = 10) -> List[str]:
"""Извлечение ключевых фраз"""
        if not text:
            return []
        
# Упрощенное извлечение ключевой фразы
        words = self.tokenize(text)
        words = self.remove_stop_words(words)
        
        # 寻找常见的学术短语模式
        phrase_patterns = [
            r'\b\w+\s+\w+\b',  # 两词短语
            r'\b\w+\s+\w+\s+\w+\b',  # 三词短语
        ]
        
        phrases = []
        for pattern in phrase_patterns:
            matches = re.findall(pattern, text.lower())
            phrases.extend(matches)
        
# Рассчитать частоту фраз
        phrase_freq = Counter(phrases)
        
# Фильтровать и сортировать
        filtered_phrases = [
            phrase for phrase, freq in phrase_freq.items()
            if freq > 1 and len(phrase.split()) >= 2
        ]
        
        filtered_phrases.sort(key=lambda x: phrase_freq[x], reverse=True)
        
        return filtered_phrases[:max_phrases]
    
    def detect_language(self, text: str) -> str:
"""Язык обнаружения (упрощенная реализация)"""
        if not text:
            return "unknown"
        
# Простое определение языка на основе общего словаря
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = chinese_chars + english_chars
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return "chinese"
        elif english_chars > 0:
            return "english"
        else:
            return "unknown"
    
    def extract_citations(self, text: str) -> List[Dict[str, Any]]:
"""Извлечь ссылку"""
        citations = []
        
# Режим числового задания [1], [2-3]
        numeric_pattern = r'\[(\d+(?:-\d+)?)\]'
        numeric_matches = re.finditer(numeric_pattern, text)
        for match in numeric_matches:
            citations.append({
                "type": "numeric",
                "text": match.group(0),
                "reference": match.group(1),
                "position": match.start()
            })
        
# год цитирования автора (Смит, 2020 г.)
        author_year_pattern = r'\(([A-Za-z]+(?:\s+et\s+al\.)?,\s*\d{4})\)'
        author_year_matches = re.finditer(author_year_pattern, text)
        for match in author_year_matches:
            citations.append({
                "type": "author_year",
                "text": match.group(0),
                "reference": match.group(1),
                "position": match.start()
            })
        
        return citations
    
    def extract_numbers_and_units(self, text: str) -> List[Dict[str, Any]]:
"""Извлечение чисел и единиц измерения"""
        patterns = [
            r'(\d+(?:\.\d+)?)\s*([a-zA-Z%]+)',  # 数字 + 单位
            r'(\d+(?:,\d{3})*(?:\.\d+)?)',  # 带逗号的数字
        ]
        
        results = []
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                results.append({
                    "text": match.group(0),
                    "number": match.group(1),
                    "unit": match.group(2) if len(match.groups()) > 1 else "",
                    "position": match.start()
                })
        
        return results
    
    def extract_acronyms(self, text: str) -> Dict[str, str]:
"""Извлечь сокращения"""
        acronyms = {}
        
# Поиск по шаблону полного имени (аббревиатуры)
        acronym_pattern = r'([A-Za-z\s]+)\s*\(([A-Z]{2,})\)'
        matches = re.finditer(acronym_pattern, text)
        
        for match in matches:
            full_name = match.group(1).strip()
            acronym = match.group(2)
            
# Убедитесь, что аббревиатура состоит из первой буквы полного имени
            initials = ''.join([word[0].upper() for word in full_name.split() if word])
            
            if acronym.startswith(initials):
                acronyms[acronym] = full_name
        
        return acronyms
    
    def summarize_text(self, text: str, max_sentences: int = 3) -> str:
"""Текстовое резюме (упрощенная реализация)"""
        if not text:
            return ""
        
        sentences = self.extract_sentences(text)
        
        if len(sentences) <= max_sentences:
            return " ".join(sentences)
        
# Простой алгоритм обобщения: выберите предложение, содержащее наибольшее количество ключевых слов.
        words = self.tokenize(text)
        words = self.remove_stop_words(words)
        word_freq = Counter(words)
        
        sentence_scores = []
        for sentence in sentences:
            sentence_words = self.tokenize(sentence)
            sentence_words = self.remove_stop_words(sentence_words)
            
            score = sum(word_freq.get(word, 0) for word in sentence_words)
            sentence_scores.append((sentence, score))
        
# Выберите предложение с наивысшим баллом
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [sentence for sentence, score in sentence_scores[:max_sentences]]
        
# Сортировка по исходному порядку текста
        summary_sentences = []
        for sentence in sentences:
            if sentence in top_sentences:
                summary_sentences.append(sentence)
        
        return " ".join(summary_sentences)
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
"""Извлечение сущности (упрощенная реализация)"""
        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "numbers": []
        }
        
# Режим имени (упрощенный)
        person_pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        person_matches = re.findall(person_pattern, text)
        entities["persons"] = list(set(person_matches))
        
# Организационная модель (упрощенная)
        org_patterns = [
            r'\b([A-Z][a-z]+\s+(?:University|Institute|Laboratory|Company|Corp|Inc|Ltd))\b',
            r'\b((?:[A-Z]+\s*){2,})\b'
        ]
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities["organizations"].extend(matches)
        entities["organizations"] = list(set(entities["organizations"]))
        
# Шаблон даты
        date_patterns = [
            r'\b(\d{4})\b',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            entities["dates"].extend(matches)
        entities["dates"] = list(set(entities["dates"]))
        
#Цифровой режим
        number_pattern = r'\b(\d+(?:\.\d+)?)\b'
        number_matches = re.findall(number_pattern, text)
        entities["numbers"] = list(set(number_matches))
        
        return entities
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
"""Рассчитать сходство текста (на основе совпадения словарного запаса)"""
        if not text1 or not text2:
            return 0.0
        
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def process_batch(self, texts: List[str], operations: List[str]) -> List[Dict[str, Any]]:
"""Пакетная обработка текста"""
        results = []
        
        for text in texts:
            result = {"text": text}
            
            for operation in operations:
                if operation == "clean":
                    result["cleaned"] = self.clean_text(text)
                elif operation == "tokenize":
                    result["tokens"] = self.tokenize(text)
                elif operation == "sentences":
                    result["sentences"] = self.extract_sentences(text)
                elif operation == "paragraphs":
                    result["paragraphs"] = self.extract_paragraphs(text)
                elif operation == "readability":
                    result["readability"] = self.calculate_readability(text)
                elif operation == "key_phrases":
                    result["key_phrases"] = self.extract_key_phrases(text)
                elif operation == "language":
                    result["language"] = self.detect_language(text)
                elif operation == "citations":
                    result["citations"] = self.extract_citations(text)
                elif operation == "entities":
                    result["entities"] = self.extract_entities(text)
                elif operation == "summary":
                    result["summary"] = self.summarize_text(text)
            
            results.append(result)
        
        return results