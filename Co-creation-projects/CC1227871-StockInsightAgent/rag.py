"""Шаг 7: База знаний RAG Investment — блокировка документов + поиск TF-IDF"""
import os
import re
import json
import math
from collections import Counter
from typing import List, Dict, Tuple


class InvestmentKnowledgeBase:
"""Облегченная база знаний по инвестициям - нет внешнего встроенного API, поиск TF-IDF"""

    def __init__(self, path: str = "memory/knowledge_base.json"):
        self.path = path
        self.chunks: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.chunks = []

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)

# ===== Импорт документа =====
    def add_text(self, text: str, title: str = "", source: str = "") -> str:
"""Импортируйте текст и автоматически разделите его на фрагменты"""
        chunks = self._chunk_text(text, title, source)
        self.chunks.extend(chunks)
        self._save()
return f"'{title}' был импортирован, всего {len(chunks)} фрагментов знаний (всего {len(self.chunks)} фрагментов)"

    def add_file(self, filepath: str) -> str:
"""Импортировать файл (поддерживает .txt .md)"""
        if not os.path.exists(filepath):
return f"Файл не существует: {путь к файлу}"
        try:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(filepath, "r", encoding="gbk") as f:
                    text = f.read()
        except Exception as e:
return f"Не удалось прочитать файл: {e}"
        title = os.path.basename(filepath)
        return self.add_text(text, title, filepath)

    def _chunk_text(self, text: str, title: str, source: str,
                    chunk_size: int = 300, overlap: int = 50) -> List[Dict]:
"""Интеллектуальное разделение по абзацам + границам предложений"""
# Сначала разбить по абзацам
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(current) + len(para) < chunk_size:
                current += ("\n" if current else "") + para
            else:
                if current:
                    chunks.append(current)
# Если абзац слишком длинный, разделите его на предложения
                if len(para) > chunk_size:
                    sentences = re.split(r"(?<=[。！？\.!?])\s*", para)
                    sub = ""
                    for s in sentences:
                        if len(sub) + len(s) < chunk_size:
                            sub += s
                        else:
                            if sub:
                                chunks.append(sub)
                            sub = s
                    if sub:
                        current = sub
                    else:
                        current = ""
                else:
                    current = para
        if current:
            chunks.append(current)

        return [{
            "id": f"{title}_{i}",
            "title": title,
            "source": source,
            "content": c,
        } for i, c in enumerate(chunks)]

# ===== Получение =====
    def search(self, query: str, top_k: int = 5) -> str:
"""TF-IDF извлекает наиболее важные фрагменты знаний"""
        if not self.chunks:
return «База знаний пуста. Для добавления документов можно использовать «Импортировать путь к файлу знаний».

# Пополняем словарный запас
        all_docs = [c["content"] for c in self.chunks]
        tokenized_docs = [self._tokenize(d) for d in all_docs]
        tokenized_query = self._tokenize(query)

# Расчет TF-IDF
        df = Counter()
        for tokens in tokenized_docs:
            df.update(set(tokens))
        N = len(tokenized_docs)

        scores = []
        for i, doc_tokens in enumerate(tokenized_docs):
            tf = Counter(doc_tokens)
            score = 0
            for term in set(tokenized_query):
                if term in tf:
                    tf_val = tf[term] / max(len(doc_tokens), 1)
                    idf_val = math.log((N + 1) / (df[term] + 1)) + 1
                    score += tf_val * idf_val
            if score > 0:
                scores.append((score, i))

        scores.sort(key=lambda x: x[0], reverse=True)

        if not scores:
# Возврат к сопоставлению ключевых слов
            for i, (doc, doc_tokens) in enumerate(zip(all_docs, tokenized_docs)):
                if any(kw in doc_tokens for kw in tokenized_query):
                    scores.append((0.5, i))
            scores.sort(key=lambda x: x[0], reverse=True)

        if not scores:
return f"Нет сведений, связанных с '{query}', не найдено"

lines = [f"Результаты поиска в базе знаний (запрос: '{query}'):"]
        for score, idx in scores[:top_k]:
            chunk = self.chunks[idx]
            lines.append(f"\n--- [{score:.2f}] {chunk['title']} ---")
            lines.append(chunk["content"][:400])

        return "\n".join(lines)

    def _tokenize(self, text: str) -> List[str]:
"""Простая сегментация китайских слов (2 грамма)"""
        # 提取中文字符和英文单词
        words = re.findall(r"[一-鿿]{1,2}|[a-zA-Z]+", text.lower())
        return [w for w in words if len(w) >= 2]

    def stats(self) -> str:
        titles = set(c["title"] for c in self.chunks)
return (f"База знаний: {len(self.chunks)} фрагменты знаний, "
f"{len(titles)} документы")

    def clear(self) -> str:
        self.chunks = []
        self._save()
вернуть «База знаний очищена»


# ===== Предустановленные знания об инвестициях =====
INVESTMENT_KNOWLEDGE = """
# Метод оценки акций

## Отношение цены к прибыли (PE)
PE = цена акции / прибыль на акцию. Отражает цену, которую рынок готов заплатить за доллар прибыли.
- PE < 10: возможно, недооценен (необходимо исключить низкое качество доходов).
- PE 10-20: разумный диапазон
- PE 20-30: от умеренного до высокого, обычно соответствует растущим акциям.
- PE > 30: высокая оценка, должна поддерживаться высокими темпами роста.
Отраслевые различия велики: PE банков обычно превышает 5-10 раз, а PE акций технологических компаний может достигать 30-50 раз.

## Соотношение цены и бронирования (PB)
PB = цена акции / чистые активы на акцию. Подходит для отраслей с тяжелыми активами (банковское дело, недвижимость, производство).
- PB < 1: сеть повреждена, вероятно, серьезно недооценена.
- PB 1-2: Достаточно низкий
- PB 2-5: Нормальный уровень
- PB > 5: высокий, должен поддерживаться высокой рентабельностью собственного капитала.

## Индикатор PEG
PEG = PE / Темп роста чистой прибыли (%). Используется для оценки акций роста.
- ПЭГ < ​​0,5: значительно занижено.
- ПЭГ 0,5–1,0: достаточно низкий
- ПЭГ 1,0–1,5: разумный
- PEG > 2,0: переоценен.

## Ставка дивидендов
Дивидендная доходность = дивиденд на акцию / цена акции. Измерьте возврат денежных средств.
- Дивидендная доходность > 4%: высокие дивиденды, сильный защитный характер
- Дивидендная доходность 2-4%: нормальный уровень
- Дивидендная доходность < 2%: низкая

# Интерпретация технических индикаторов

## MACD золотой крест мертвый крест
- Золотой крест: DIF пересекает DEA, сигнал на покупку. Золотой крест над нулевой осью сильнее.
- Крест смерти: DIF пересекает уровень DEA, что является сигналом на продажу. Мертвый крест ниже нулевой оси слабее.
- Верхняя дивергенция: цена акций достигает нового максимума, но MACD не достигает нового максимума, что является сигналом достижения пика.
- Нижняя дивергенция: цена акции достигает нового минимума, а MACD не достигает нового минимума, что является сигналом дна.

## Индекс относительной силы RSI
- RSI > 80: сильная перекупленность, высокий риск коррекции.
- RSI 70-80: область перекупленности, возможна коррекция в краткосрочной перспективе.
- RSI 30-70: нормальный диапазон
- RSI 20-30: зона перепроданности, возможен отскок в краткосрочной перспективе.
- RSI < 20: Сильная перепроданность, высокая вероятность отскока.

## Система скользящих средних
- Длинная позиция: MA5 > MA10 > MA20 > MA60, восходящий тренд.
- Короткая позиция: MA5 < MA10 < MA20 < MA60, нисходящий тренд.
- Золотой крест: краткосрочная скользящая средняя пересекает долгосрочную скользящую среднюю.
- Крест смерти: краткосрочная скользящая средняя пересекает долгосрочную скользящую среднюю.

## Полосы Боллинджера
- Цена достигает верхней линии: краткосрочная перекупленность, возможна коррекция.
- Цена достигает нижней линии: краткосрочная перепроданность, возможен отскок.
- Сужение полосы пропускания: сигнал об изменении рынка, возможном прорыве
- Расширение пропускной способности: тенденция ускоряется

#Принципы контроля рисков

## Управление позициями
- Одна акция не превышает 20% от общей позиции
- Одна отрасль не должна превышать 30% от общей позиции.
-Всегда оставляйте 10-20% наличных на случай чрезвычайных ситуаций.
-Создавайте позиции партиями: покупайте как минимум 3 раза, чтобы снизить риск концентрации затрат.

## Принцип стоп-лосса
- Технический стоп-лосс: стоп-лосс, если он падает ниже ключевого уровня поддержки (MA60/предыдущий минимум).
- Пропорциональный стоп-лосс: безусловный стоп-лосс, если убыток превышает 8-10%
- Временной стоп-лосс: если покупка не оправдает ожиданий через 20 торговых дней после покупки, переоцените ее.
- Фундаментальный стоп-лосс: если фундаментальные показатели компании значительно ухудшаются, немедленно стоп-лосс.

## Соотношение риска и выгоды
- Соотношение риска и прибыли в каждой сделке должно быть >= 1:2.
- Ожидаемая прибыль должна как минимум в 2 раза превышать потенциальные потери.

# Правила торговли акциями A

## Часы торговли
- 早盘集合竞价: 9:15-9:25
- Непрерывные торги: 9:30-11:30, 13:00-15:00
- Аукцион поздних торгов Шэньчжэньской фондовой биржи: 14:57-15:00.

## Ограничение цены
- Материнская плата: ± 10%
- GEM (начиная с 300)/Совет по инновациям в области науки и технологий (начиная с 688): ±20%
- Акции ST: ±5%
- Цена новых акций за 5 дней до листинга не ограничена.

## Система Т+1
Акции А реализуют торговлю T+1, и вы сможете продать их только на следующий день, если купите их в тот же день.
"""


# Глобальный синглтон
_kb_instance = None


def get_kb() -> InvestmentKnowledgeBase:
    global _kb_instance
    if _kb_instance is None:
        _kb_instance = InvestmentKnowledgeBase()
#Импорт предустановленных данных во время первой инициализации
        if not _kb_instance.chunks:
_kb_instance.add_text(INVESTMENT_KNOWLEDGE, «Основы инвестирования», «встроенный»)
    return _kb_instance


# ===== Вспомогательные функции =====

def rag_search(query: str) -> str:
"""Выполните поиск в базе знаний по инвестициям. Введите: ключевые слова для запроса или вопросы"""
    return get_kb().search(query.strip())


def rag_import(query: str) -> str:
"""Импорт документов в базу знаний. Ввод: путь к файлу"""
    return get_kb().add_file(query.strip())


def rag_stats(query: str = "") -> str:
"""Просмотр статистики базы знаний"""
    return get_kb().stats()
