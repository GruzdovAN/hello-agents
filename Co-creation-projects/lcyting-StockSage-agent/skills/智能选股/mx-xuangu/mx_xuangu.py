#!/usr/bin/env python3
# mx_xuangu — умный навык выбора акций Мяосян
# 基于东方财富妙想API提供智能选股能力

import os
import sys
import json
import csv
import re
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

def safe_filename(s: str, max_len: int = 80) -> str:
"""Преобразование текста запроса в безопасные фрагменты имени файла"""
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = s.strip().replace(" ", "_")[:max_len]
    return s or "query"

def build_column_map(columns: List[Dict[str, Any]]) -> Dict[str, str]:
    """
Создайте исходное имя столбца -> сопоставление имен столбцов на китайском языке из возвращенных столбцов.
    """
    name_map: Dict[str, str] = {}
    for col in columns or []:
        if not isinstance(col, dict):
            continue
        en_key = col.get("field", "") or col.get("name", "") or col.get("key", "")
        cn_name = col.get("displayName", "") or col.get("title", "") or col.get("label", "")
        date_msg = col.get('dateMsg', '')
        if date_msg:
            cn_name = cn_name + ' ' + date_msg
        if en_key is not None and cn_name is not None:
            name_map[str(en_key)] = str(cn_name)
    return name_map

def columns_order(columns: List[Dict[str, Any]]) -> List[str]:
"""Возвращает исходный список имен столбцов в порядке столбцов для порядка заголовков CSV"""
    order: List[str] = []
    for col in columns or []:
        if not isinstance(col, dict):
            continue
        en_key = col.get("field") or col.get("name") or col.get("key")
        if en_key is not None:
            order.append(str(en_key))
    return order

def parse_partial_results_table(partial_results: str) -> List[Dict[str, str]]:
    """
Разобрать строку таблицы PartialResults Markdown в список словарей строк.
    """
    if not partial_results or not isinstance(partial_results, str):
        return []
    lines = [ln.strip() for ln in partial_results.strip().splitlines() if ln.strip()]
    if not lines:
        return []

    def split_cells(line: str) -> List[str]:
        return [c.strip() for c in line.split("|") if c.strip() != ""]

    header_cells = split_cells(lines[0])
    if not header_cells:
        return []
# Пропустить строки с разделителями (например, |---|---|)
    data_start = 1
    if data_start < len(lines) and re.match(r"^[\s\|\-]+$", lines[data_start]):
        data_start = 2
    rows: List[Dict[str, str]] = []
    for i in range(data_start, len(lines)):
        cells = split_cells(lines[i])
        if len(cells) != len(header_cells):
# Если количество столбцов несовместимо, выровняйте их по длине и заполните пробелы, если они отсутствуют.
            if len(cells) < len(header_cells):
                cells.extend([""] * (len(header_cells) - len(cells)))
            else:
                cells = cells[: len(header_cells)]
        rows.append(dict(zip(header_cells, cells)))
    return rows

def datalist_to_rows(
        datalist: List[Dict[str, Any]],
        column_map: Dict[str, str],
        column_order: List[str],
) -> List[Dict[str, str]]:
    """
Замените исходные ключи каждой строки в списке данных китайскими ключами в соответствии с columns_map, чтобы обеспечить порядок.
    """
    if not datalist:
        return []

    # 表头顺序：优先按 columns 顺序，未在 columns 中的键按首次出现顺序排在后面
    first = datalist[0]
    extra_keys = [k for k in first if k not in column_order]
    header_order = column_order + extra_keys

    rows: List[Dict[str, str]] = []
    for row in datalist:
        if not isinstance(row, dict):
            continue
        cn_row: Dict[str, str] = {}
        for en_key in header_order:
            if en_key not in row:
                continue
            cn_name = column_map.get(en_key, en_key)
            val = row[en_key]
            if val is None:
                cn_row[cn_name] = ""
            elif isinstance(val, (dict, list)):
                cn_row[cn_name] = json.dumps(val, ensure_ascii=False)
            else:
                cn_row[cn_name] = str(val)
        rows.append(cn_row)

    return rows

class MXSelectStock:
"""Клиент интеллектуального выбора акций Miaoxiang"""
    
    BASE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/stock-screen"
    
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
Умный выбор акций
:param query: Запрос на естественном языке, например «Сегодняшняя цена акции A превышает 10 юаней».
:return: Результат ответа API
        """
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key
        }
        data = {
            "keyword": query
        }
        
        response = requests.post(self.BASE_URL, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    def extract_data(result: Dict[str, Any]) -> Tuple[List[Dict[str, str]], str, Optional[str]]:
        """
Извлечь данные:
– Отдавайте приоритет использованию полных данных allResults.result.dataList.
- Если нет, вернитесь к анализу таблицы частичного результата Markdown.
        :return: (rows, data_source, error)
        """
        status = result.get("status")
        if status != 0:
return [], "", f"Ошибка верхнего уровня: код состояния {status} - {result.get('message', '')}"
        
        data = result.get("data", {})
        inner_data = data.get("data", {})
        
# Расставляем приоритеты, используя полный объем данных dataList
        data_list = inner_data.get("allResults", {}).get("result", {}).get("dataList", [])
        columns = inner_data.get("allResults", {}).get("result", {}).get("columns", [])
        
        if isinstance(data_list, list) and data_list:
            column_map = build_column_map(columns)
            order = columns_order(columns)
            rows = datalist_to_rows(data_list, column_map, order)
            return rows, "dataList", None
        
# Возврат к анализу частичных результатов
        partial_results = inner_data.get("partialResults", "")
        if partial_results:
            rows = parse_partial_results_table(partial_results)
            return rows, "partialResults", None
        
        return [], "", "返回中无有效 dataList 且 partialResults 无法解析或为空"

def main():
"""Ввод командной строки """
parser = argparse.ArgumentParser(description='Интеллектуальный выбор акций с помощью запроса на естественном языке (акции A/акции Гонконга/акции США/секторы/фонды/ETF)')
parser.add_argument('query', nargs='?', help='Запрос на естественном языке, например «Акции с ценой выше 10 юаней»')
    parser.add_argument('--query', dest='query_opt', help='自然语言查询（显式参数）')
parser.add_argument('--output-dir', dest='output_dir', help='Каталог вывода, по умолчанию /root/.openclaw/workspace/mx_data/output/')
    args = parser.parse_args()
    
    # Resolve query
    query = args.query_opt or args.query
    if not query:
        parser.print_help()
        sys.exit(1)
    
    # Default output directory is fixed to /root/.openclaw/workspace/mx_data/output/
    default_output = Path("/root/.openclaw/workspace/mx_data/output")
    output_dir = Path(args.output_dir) if args.output_dir else default_output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        mx = MXSelectStock()
        result = mx.search(query)
        rows, data_source, err = mx.extract_data(result)
        
        if err:
print(f"Ошибка: {err}")
print(f"Предварительный просмотр исходного результата: {json.dumps(result, обеспечения_ascii=False)[:500]}")
            sys.exit(2)
        
        if not rows:
print("Соответствующие данные не найдены")
            sys.exit(0)
        
# Вывод CSV
        fieldnames = list(rows[0].keys())
        safe_name = safe_filename(query)
        csv_path = output_dir / f"mx_xuangu_{safe_name}.csv"
        desc_path = output_dir / f"mx_xuangu_{safe_name}_description.txt"
        
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        
#Запись файла описания
        description_lines = [
«Интеллектуальное объяснение результатов выбора акций»,
            "=" * 40,
f"Содержимое запроса: {query}",
            f"数据行数: {len(rows)}（来源: {data_source}）",
f"Имя столбца (китайский): {', '.join(fieldnames)}",
            "",
«Пояснение: данные получены от компании Oriental Fortune Miaoxiang Intelligent Stock Selection»;
+ («Имена столбцов были сопоставлены с китайским языком по столбцам». if data_source == «dataList» else «Таблица получена в результате анализа частичных результатов.»),
        ]
        desc_path.write_text("\n".join(description_lines), encoding="utf-8")
        
#Вывод информации о терминале
        print(f"✅ CSV: {csv_path}")
print(f"📄 описание: {desc_path}")
print(f"📊 Количество строк: {len(rows)}")
        
# Сохраняем исходный JSON
        json_path = output_dir / f"mx_xuangu_{safe_name}_raw.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
print(f"📄 Исходный JSON: {json_path}")
            
    except Exception as e:
print(f"Ошибка: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
