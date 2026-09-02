#!/usr/bin/env python3
# mx_search — навык поиска информации в Мяосяне
# Предоставление возможностей поиска финансовой информации на основе API Oriental Fortune Wonderful Search API.
# 默认输出目录: /root/.openclaw/workspace/mx_data/output/

import os
import sys
import json
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any

def safe_filename(text: str, max_len: int = 80) -> str:
    """Convert query string to safe filenameh"""
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", text).strip().replace(" ", "_")
    return (cleaned[:max_len] or "query").strip("._")

class MXSearch:
"""Клиент поиска информации Miaoxiang"""
    
    BASE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/news-search"
    
    def __init__(self, api_key: Optional[str] = None):
        """
Инициализировать клиент
        :param api_key: MX API Key，如果不提供则从环境变量 MX_APIKEY 读取
        """
        self.api_key = api_key or os.getenv("MX_APIKEY")
        if not self.api_key:
            raise ValueError(
«Переменная среды MX_APIKEY не установлена, сначала установите переменную среды:\n»
                "export MX_APIKEY=your_api_key_here\n"
«Или передайте параметр api_key во время инициализации»
            )
    
    def search(self, query: str) -> Dict[str, Any]:
        """
Поиск финансовой информации
:param query: Поисковый вопрос
:return: Результат ответа API
        """
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key
        }
        data = {
            "query": query
        }
        
        response = requests.post(self.BASE_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def extract_content(result: Dict[str, Any]) -> str:
        """
Извлечение простого текстового содержимого
:param result: результат ответа API
:return: Извлеченный простой текст
        """
        def _extract(raw: Any) -> str:
            if not isinstance(raw, dict):
                if isinstance(raw, str):
                    return raw.strip()
                return ""
            
            # Common envelope format
            for wrapper_key in ("data", "result"):
                wrapped = raw.get(wrapper_key)
                if isinstance(wrapped, dict):
                    nested = _extract(wrapped)
                    if nested:
                        return nested
            
            for key in ("llmSearchResponse", "searchResponse", "content", "answer", "summary"):
                value = raw.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
                if isinstance(value, (list, dict)):
                    return json.dumps(value, ensure_ascii=False, indent=2)
            
            return json.dumps(raw, ensure_ascii=False, indent=2)
        
        return _extract(result)
    
    @staticmethod
    def format_pretty(result: Dict[str, Any]) -> str:
        """
Форматирование результатов для отображения терминала
:param result: результат ответа API
:return: форматированный текст
        """
        output = []
        
        status = result.get("status")
        message = result.get("message", "")
        if status != 0:
            output.append(f"错误: 状态码 {status} - {message}")
            return "\n".join(output)
        
        data = result.get("data", {})
        inner_data = data.get("data", {})
        search_response = inner_data.get("llmSearchResponse", {})
        items = search_response.get("data", [])
        
        if not items:
вернуть «Нет соответствующей информации не найдено»
        
        output.append(f"搜索结果: 共找到 {len(items)} 条相关资讯:\n")
        
        for i, item in enumerate(items, 1):
title = item.get("title", "Без названия")
content = item.get("содержание", "Нет содержимого")
            date = item.get("date", "")
            ins_name = item.get("insName", "")
            info_type = item.get("informationType", "")
            rating = item.get("rating", "")
            entity_name = item.get("entityFullName", "")
            
            type_map = {
«ОТЧЕТ»: «Отчет об исследовании»,
«НОВОСТИ»: «Новости»,
«ОБЪЯВЛЕНИЕ»: «ОБЪЯВЛЕНИЕ»
            }
            type_cn = type_map.get(info_type, info_type)
            
            output.append(f"--- {i}. {title} ---")
            meta = []
            if entity_name:
Meta.append(f"Ценные бумаги: {entity_name}")
            if ins_name:
Meta.append(f"Организация: {ins_name}")
            if date:
                meta.append(f"日期: {date.split()[0]}")
            if type_cn:
Meta.append(f"Тип: {type_cn}")
            if rating:
Meta.append(f"рейтинг: {рейтинг}")
            
            if meta:
                output.append(" | ".join(meta))
            
            if content:
                output.append("")
                output.append(content)
            output.append("")
        
        return "\n".join(output)

def main():
"""Ввод командной строки"""
# Параметры анализа
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} \"搜索问句\" [输出目录]")
        print(f"默认输出目录: /root/.openclaw/workspace/mx_data/output/")
        print("示例: python mx_search.py \"格力电器最新研报\"")
        sys.exit(1)
    
# Запрос на сращивание
    if len(sys.argv) >= 3:
        query = " ".join(sys.argv[1:-1])
        output_dir = Path(sys.argv[-1])
    else:
        query = " ".join(sys.argv[1:])
# Вывод в фиксированный каталог по умолчанию
        output_dir = Path("/root/.openclaw/workspace/mx_data/output")
    
# Убедитесь, что выходной каталог существует
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        mx = MXSearch()
        result = mx.search(query)
        
# Терминал отображает результаты форматирования
        print(mx.format_pretty(result))
        
#Извлекаем обычный текст и сохраняем его как файл .txt.
        content = mx.extract_content(result)
        if content.strip():
            filename = output_dir / f"mx_search_{safe_filename(query)}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
print(f"\n© Результаты в виде обычного текста сохранены в: {filename}")
        
# Также сохраните исходный результат JSON
        json_filename = output_dir / f"mx_search_{safe_filename(query)}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
print(f"📄 Исходный результат сохранен в: {json_filename}")
            
    except Exception as e:
print(f"Ошибка: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
