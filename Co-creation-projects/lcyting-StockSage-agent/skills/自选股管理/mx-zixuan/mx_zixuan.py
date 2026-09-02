#!/usr/bin/env python3
"""
Дополнительный навык управления Мяосян (mx_zixuan)
Поддерживает запрос, добавление и удаление акций, выбранных компанией Oriental Fortune самостоятельно.
Унифицированный вывод в /root/.openclaw/workspace/mx_data/output/
"""

import os
import sys
import csv
import json
import requests
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Конфигурация интерфейса
QUERY_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/get"
MANAGE_URL = "https://mkapi2.dfcfs.com/finskillshub/api/claw/self-select/manage"

def safe_filename(s: str, max_len: int = 80) -> str:
    """Convert query to safe filename - same as other mx_* skills"""
    s = s.replace(" ", "_").replace("/", "_").replace("\\", "_").replace(":", "_")
    s = s.replace("*", "_").replace("?", "_").replace('"', "_").replace("<", "_").replace(">", "_")
    s = s.replace("|", "_")[:max_len]
    return s or "query"

def get_apikey() -> str:
"""Получить apikey из переменной среды"""
    apikey = os.environ.get("MX_APIKEY", "")
    if not apikey:
# Попробуйте прочитать файл .env
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            if key.strip() == "MX_APIKEY":
                                apikey = value.strip()
                                break
            except Exception as e:
                print(f"⚠️  读取.env文件失败: {e}", file=sys.stderr)
    
    if not apikey:
        print("❌ 未找到MX_APIKEY，请设置环境变量：", file=sys.stderr)
        print("   export MX_APIKEY=your_apikey", file=sys.stderr)
поднять RuntimeError("MX_APIKEY не настроен")
    
    return apikey

def query_self_select(apikey: str) -> Dict:
"""Запросить список самостоятельно выбранных акций"""
    headers = {
        "Content-Type": "application/json",
        "apikey": apikey
    }
    
    response = requests.post(QUERY_URL, headers=headers, json={}, timeout=30)
    response.raise_for_status()
    return response.json()

def manage_self_select(apikey: str, query: str) -> Dict:
"""Добавить или удалить дополнительные акции"""
    headers = {
        "Content-Type": "application/json",
        "apikey": apikey
    }
    
    data = {
        "query": query
    }
    
    response = requests.post(MANAGE_URL, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()

def format_query_result(result: Dict, output_dir: Path):
"""Отформатировать вывод результатов запроса + сохранить CSV"""
    if result.get("status") != 0 and result.get("code") != 0:
print(f"❌ Ошибка запроса: {result.get('message', 'Неизвестная ошибка')}", file=sys.stderr)
        return
    
    data = result.get("data", {})
    all_results = data.get("allResults", {})
    result_data = all_results.get("result", {})
    columns = result_data.get("columns", [])
    data_list = result_data.get("dataList", [])
    
    if not data_list:
print("ℹ️ Список дополнительных акций пуст, зайдите в приложение Oriental Fortune, чтобы проверить")
        return
    
#Извлекаем поля, которые нужно отобразить
    display_fields = [
("SECURITY_CODE", "Код акции", 8),
("SECURITY_SHORT_NAME", "Название акции", 8),
("NEWEST_PRICE", "Последняя цена (юани)", 10),
(«CHG», «Изменение (%)», 10),
(«ПЧГ», «Повышение или понижение (юань)», 10),
("010000_TURNOVER_RATE", "Оборачиваемость (%)", 10),
("010000_LIANGBI", "количественное соотношение", 6)
    ]
    
# Печать заголовка
print("📊 Мой список выбора акций")
    print("=" * 100)
    header = " | ".join([f"{name:<{width}}" for _, name, width in display_fields])
    print(header)
    print("-" * 100)
    
#Печать строк данных
    for stock in data_list:
        row = []
        for key, _, width in display_fields:
            value = stock.get(key, "-")
            # 处理涨跌幅颜色
            if key == "CHG" and value != "-":
                try:
                    chg = float(value)
                    if chg > 0:
                        value = f"+{value}%"
                    elif chg < 0:
                        value = f"{value}%"
                    else:
                        value = f"{value}%"
                except:
                    pass
            row.append(f"{str(value):<{width}}")
        print(" | ".join(row))
    
    print("-" * 100)
print(f"Всего {len(data_list)} только выбранных вами акций")
    
    # 保存到 CSV - same output convention as other mx_* skills
Safe_name = "Мой список выбора акций"
    csv_path = output_dir / f"mx_zixuan_{safe_filename(safe_name)}.csv"
    
    # Build CSV header from all columns (Chinese names)
    fieldnames = []
    csv_rows = []
    column_name_map = {}
    for col in columns:
        title = col.get("title", col.get("key", "unknown"))
        key = col.get("key", "unknown")
        column_name_map[key] = title
        fieldnames.append(title)
    
    for stock in data_list:
        csv_row = {}
        for key, title in column_name_map.items():
            csv_row[title] = stock.get(key, "")
        csv_rows.append(csv_row)
    
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in csv_rows:
            writer.writerow(row)
    
    # Save raw JSON
    json_path = output_dir / f"mx_zixuan_{safe_filename(safe_name)}_raw.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
print(f"\nвещество CSV сохранено: {csv_path}")
print(f"📄 Исходный JSON: {json_path}")

def format_manage_result(result: Dict, query: str):
"""Форматирование вывода результата операции"""
    if result.get("status") != 0 and result.get("code") != 0:
print(f"❌ Операция не удалась: {result.get('message', 'Неизвестная ошибка')}", file=sys.stderr)
        return
    
    print(f"✅ 操作成功: {result.get('message', '已完成')}")

def main():
parser = argparse.ArgumentParser(description="Замечательный инструмент управления выбором (mx_zixuan)")
parser.add_argument("command", nargs="?", help="Команда: запрос/добавление/удаление или команда естественного языка")
    parser.add_argument("stock", nargs="?", help="股票名称或代码（可选）")
parser.add_argument("--output-dir", dest="output_dir", help=f"Каталог вывода, по умолчанию {Path('/root/.openclaw/workspace/mx_data/output')}")
    
    args = parser.parse_args()
    
    # Default output directory
    default_output = Path("/root/.openclaw/workspace/mx_data/output")
    output_dir = Path(args.output_dir) if args.output_dir else default_output
    output_dir.mkdir(parents=True, exist_ok=True)
    
    apikey = get_apikey()
    
# Команды процесса
    if not args.command:
print("ℹ️ Использование:", file=sys.stderr)
print("Запросить выбранные акции: скрипты Python/запрос mx_zixuan.py", file=sys.stderr)
        print("  添加自选股: python scripts/mx_zixuan.py add 贵州茅台", file=sys.stderr)
print("Удалить дополнительные акции: скрипты Python/mx_zixuan.py delete Kweichow Moutai", file=sys.stderr)
print("Естественный язык: скрипты Python/mx_zixuan.py \"Добавьте Квейчоу Мутая в свой выбор\"", file=sys.stderr)
        print(f"\n  默认输出目录: {output_dir}", file=sys.stderr)
        sys.exit(1)
    
    command = args.command.lower()
    
    if command in ["query", "list", "查询", "列表"]:
# Запрос дополнительных акций
        result = query_self_select(apikey)
        format_query_result(result, output_dir)
    elif command in ["add", "添加", "增加"] and args.stock:
# Добавить акции
query = f"Добавить {args.stock} в мой список выбора акций"
        result = manage_self_select(apikey, query)
        format_manage_result(result, query)
Команда elif в ["delete", "del", "remove", "delete", "remove"] и args.stock:
# Удаление акций
query = f"Удалить {args.stock} из моего списка выбора акций"
        result = manage_self_select(apikey, query)
        format_manage_result(result, query)
    else:
# обработка естественного языка
        query = args.command
        if args.stock:
            query += " " + args.stock
        
# Определить, является ли это запросом или операцией управления
если есть(ключевое слово в запросе по ключевому слову в ["запрос", "список", "мой выбор", "что там"]):
            result = query_self_select(apikey)
            format_query_result(result, output_dir)
        else:
            result = manage_self_select(apikey, query)
            format_manage_result(result, query)

if __name__ == "__main__":
    main()
