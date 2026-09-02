"""
Инструмент генерации векторов InnoCore AI
"""

import asyncio
from typing import List, Dict, Optional, Any
import numpy as np
from openai import AsyncOpenAI
import hashlib
import json

from ..core.config import get_config
from ..core.exceptions import AgentException

class EmbeddingGenerator:
"""Векторный генератор"""
    
    def __init__(self):
        self.config = get_config()
        self.client = None
        self.embedding_model = self.config.vector_db.embedding_model
self.cache = {} # Простой кеш памяти
    
    async def initialize(self):
"""Генератор вектора инициализации"""
        try:
            self.client = AsyncOpenAI(
                api_key=self.config.llm.api_key,
                base_url=self.config.llm.base_url
            )
        except Exception as e:
            raise AgentException(f"向量生成器初始化失败: {str(e)}")
    
    async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
"""Создать текстовый вектор"""
        if not text:
return [0.0] * 1536 # Возвращает нулевой вектор
        
#Проверить кеш
        if use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self.cache:
                return self.cache[cache_key]
        
        try:
# Очистка текста
            cleaned_text = self._clean_text(text)
            
# Вызов API OpenAI
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=cleaned_text
            )
            
            embedding = response.data[0].embedding
            
# результатов кэширования
            if use_cache:
                cache_key = self._get_cache_key(text)
                self.cache[cache_key] = embedding
            
            return embedding
            
        except Exception as e:
            raise AgentException(f"向量生成失败: {str(e)}")
    
    async def generate_batch_embeddings(self, texts: List[str], 
                                       batch_size: int = 10) -> List[List[float]]:
"""Пакетное создание векторов"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            try:
# Пакетный вызов API
                cleaned_texts = [self._clean_text(text) for text in batch]
                
                response = await self.client.embeddings.create(
                    model=self.embedding_model,
                    input=cleaned_texts
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
# Если пакет не удалось, сгенерируйте один за другим
                for text in batch:
                    try:
                        embedding = await self.generate_embedding(text)
                        embeddings.append(embedding)
                    except Exception as single_error:
                        print(f"单个向量生成失败: {str(single_error)}")
                        embeddings.append([0.0] * 1536)  # 零向量
        
        return embeddings
    
    async def generate_paper_embedding(self, paper_info: Dict[str, Any]) -> List[float]:
"""Создание комплексных векторов для документов"""
        # 组合论文的关键信息
        title = paper_info.get("title", "")
        abstract = paper_info.get("abstract", "")
        authors = " ".join(paper_info.get("authors", []))
        
# Создайте подробный текст
        combined_text = f"{title} {abstract} {authors}"
        
# Если есть структурированный контент, включите его тоже
        sections = paper_info.get("sections", {})
        if sections:
            section_text = " ".join(sections.values())
            combined_text += " " + section_text
        
        return await self.generate_embedding(combined_text)
    
    async def generate_section_embeddings(self, sections: Dict[str, str]) -> Dict[str, List[float]]:
"""Сгенерировать векторы для каждой главы"""
        section_embeddings = {}
        
        for section_name, section_content in sections.items():
            if section_content.strip():
                try:
                    embedding = await self.generate_embedding(section_content)
                    section_embeddings[section_name] = embedding
                except Exception as e:
                    print(f"章节 {section_name} 向量生成失败: {str(e)}")
                    section_embeddings[section_name] = [0.0] * 1536
        
        return section_embeddings
    
    def _clean_text(self, text: str) -> str:
"""Чистый текст"""
        if not text:
            return ""
        
# Удаляем лишние пробелы
        text = ' '.join(text.split())
        
#Обрезать слишком длинный текст (у OpenAI есть ограничения на токены)
max_length = 8000 # Консервативная оценка
        if len(text) > max_length:
            text = text[:max_length]
        
        return text
    
    def _get_cache_key(self, text: str) -> str:
"""Сгенерировать ключ кэша"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def clear_cache(self):
"""Очистить кеш"""
        self.cache.clear()
    
    def get_cache_size(self) -> int:
"""Получить размер кэша"""
        return len(self.cache)
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
"""Рассчитать сходство между двумя текстами"""
        try:
            embedding1 = await self.generate_embedding(text1)
            embedding2 = await self.generate_embedding(text2)
            
            return self._cosine_similarity(embedding1, embedding2)
            
        except Exception as e:
print(f"Ошибка расчета сходства: {str(e)}")
            return 0.0
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
"""Рассчитать косинусное подобие"""
        if len(vec1) != len(vec2):
            return 0.0
        
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception:
            return 0.0
    
    async def find_most_similar(self, query_text: str, 
                               candidate_texts: List[str],
                               top_k: int = 5) -> List[Dict[str, Any]]:
"""Найди наиболее похожий текст"""
        if not candidate_texts:
            return []
        
        try:
# Генерируем вектор запроса
            query_embedding = await self.generate_embedding(query_text)
            
# Генерируем текстовые векторы-кандидаты
            candidate_embeddings = await self.generate_batch_embeddings(candidate_texts)
            
# Вычисляем сходство
            similarities = []
            for i, candidate_embedding in enumerate(candidate_embeddings):
                similarity = self._cosine_similarity(query_embedding, candidate_embedding)
                similarities.append({
                    "text": candidate_texts[i],
                    "similarity": similarity,
                    "index": i
                })
            
# Сортировка по сходству
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:top_k]
            
        except Exception as e:
print(f"Ошибка поиска похожего текста: {str(e)}")
            return []
    
    async def cluster_texts(self, texts: List[str], 
                          num_clusters: int = 3) -> Dict[str, Any]:
"""Кластеризация текста (упрощенная реализация)"""
        try:
# Генерируем векторы всех текстов
            embeddings = await self.generate_batch_embeddings(texts)
            
# Простая логика кластеризации (на основе порога сходства)
            clusters = {}
            cluster_id = 0
            used_indices = set()
            
            for i, embedding in enumerate(embeddings):
                if i in used_indices:
                    continue
                
#Создаем новый кластер
                clusters[f"cluster_{cluster_id}"] = {
                    "texts": [texts[i]],
                    "indices": [i],
                    "center": embedding
                }
                used_indices.add(i)
                
# Найдите похожий текст и добавьте его в тот же кластер
                for j, other_embedding in enumerate(embeddings):
                    if j in used_indices:
                        continue
                    
                    similarity = self._cosine_similarity(embedding, other_embedding)
если сходство > 0,8: # Порог сходства
                        clusters[f"cluster_{cluster_id}"]["texts"].append(texts[j])
                        clusters[f"cluster_{cluster_id}"]["indices"].append(j)
                        used_indices.add(j)
                
                cluster_id += 1
            
            return {
                "clusters": clusters,
                "num_clusters": len(clusters),
                "total_texts": len(texts)
            }
            
        except Exception as e:
print(f"Ошибка кластеризации текста: {str(e)}")
            return {"clusters": {}, "num_clusters": 0, "total_texts": len(texts)}
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
"""Извлечение ключевых слов (упрощенная реализация на основе TF-IDF)"""
        try:
# причастие
            words = text.lower().split()
            
# Фильтровать стоп-слова (упрощенная версия)
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
            }
            
            filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
            
# Рассчитать частоту слов
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按频率排序
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
# Возвращаем первые N ключевых слов
            return [word for word, freq in sorted_words[:max_keywords]]
            
        except Exception as e:
print(f"Ошибка извлечения ключевого слова: {str(e)}")
            return []
    
    def get_embedding_info(self) -> Dict[str, Any]:
"""Получить информацию о векторном генераторе"""
        return {
            "model": self.embedding_model,
            "cache_size": len(self.cache),
            "vector_dimension": 1536,  # OpenAI embedding维度
            "provider": "openai"
        }