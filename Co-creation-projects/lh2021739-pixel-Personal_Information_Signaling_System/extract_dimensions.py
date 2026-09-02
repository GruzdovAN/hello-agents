"""
Модуль извлечения измерений — LLM извлекает измерения из отчётов
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Кодировка консоли UTF-8 (Windows)
# Перенаправление только при запуске как скрипт, чтобы не конфликтовать при импорте
if sys.platform == 'win32' and __name__ == "__main__":
    import io
    if not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Загрузка .env (если есть)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Импорт LLM
try:
    from hello_agents.core.llm import HelloAgentsLLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("⚠️  Предупреждение: модуль hello_agents не установлен, LLM-извлечение недоступно")


def init_llm():
    """Инициализация LLM"""
    if not LLM_AVAILABLE:
        return None
    
    # Чтение конфигурации LLM из переменных окружения
    llm_model = (
        os.getenv("LLM_MODEL") or
        os.getenv("LLM_MODEL_ID") or
        "qwen-plus"
    )
    llm_api_key = (
        os.getenv("LLM_API_KEY") or
        os.getenv("MODELSCOPE_API_KEY") or
        os.getenv("MODELSCOPE_API_TOKEN")
    )
    llm_base_url = (
        os.getenv("LLM_BASE_URL") or
        "https://api-inference.modelscope.cn/v1/"
    )
    llm_provider = os.getenv("LLM_PROVIDER", "modelscope")
    
    if not llm_api_key:
        print("⚠️  Предупреждение: LLM API Key не найден")
        return None
    
    try:
        llm = HelloAgentsLLM(
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
            provider=llm_provider
        )
        return llm
    except Exception as e:
        print(f"⚠️  Ошибка инициализации LLM: {e}")
        return None


def extract_json_from_text(text: str) -> Optional[Dict]:
    """Извлечение JSON из текста"""
    import re
    
    # Прямой разбор
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Извлечение JSON из блока кода
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Извлечение первого полного JSON-объекта
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def extract_dimensions_from_text(text: str, llm, existing_themes: List[str] = None) -> Dict:
    """Извлечение измерений из текста отчёта
    
    Args:
        text: Текст отчёта
        llm: Экземпляр LLM
        existing_themes: Существующие themes для согласования уровня абстракции
    """
    if not llm:
        return {"dimensions": [], "confidence": 0.0, "error": "LLM не инициализирован"}
    
    themes_hint = ""
    if existing_themes:
        themes_hint = f"\nОриентир — стиль существующих themes (интересы пользователя): {existing_themes}\nИзвлекаемые измерения должны совпадать по уровню абстракции с этими themes."
    
    prompt = f"""Извлеки из отчёта пользователя 3–8 измерений (dimensions). Измерения — это **темы, области или интересы высокого уровня**, а не простое разбиение на существительные.

Содержимое отчёта:
{text}
{themes_hint}

**Принципы извлечения**:
1. **Целостность понятия**: если в отчёте есть «информационная сигнальная система», извлеки «информационная сигнальная система» или «система», не дроби на «информация», «сигнал», «система»
2. **Уровень темы**: измерения — темы (например «AI», «здоровье», «работа»), а не детали («обновление», «сегодня», «радость»)
3. **Фильтрация лишнего**:
   - глаголы действия (обновить, создать, удалить)
   - слова времени (сегодня, вчера, на этой неделе)
   - эмоции (радость, грусть), если эмоция не тема отчёта
   - слишком общие слова (дело, содержание, вопрос)
4. **Семантический контекст**: смысл предложения и тема за ним
5. **Уровень абстракции**: достаточно абстрактные темы для YouTube-поиска или тегов интересов

**Пример**:
- Отчёт: «Сегодня радостно: наша информационная сигнальная система снова обновилась»
- ❌ Неверно: ["информация", "сигнал", "система", "обновление", "сегодня"]
- ✅ Верно: ["информационная сигнальная система"] или ["система"] или ["техническая система"]

Верни список измерений в JSON:
{{
  "dimensions": ["измерение1", "измерение2", "измерение3"],
  "confidence": 0.85,
  "reasoning": "краткое обоснование"
}}

Требования:
- количество: 3–8 (по значимости содержания)
- формат: краткие темы (2–8 слов), целостные понятия
- confidence: уверенность 0–1
- reasoning: почему выбраны эти измерения

Верни только JSON, без другого текста."""

    try:
        messages = [
            {"role": "system", "content": "Ты — ассистент по анализу текста: извлекаешь темы и измерения интересов высокого уровня, учитываешь контекст и целостность понятий, не делаешь простого токенизации."},
            {"role": "user", "content": prompt}
        ]
        
        response = llm.invoke(messages)
        
        # Извлечение JSON
        result = extract_json_from_text(response)
        
        if result and "dimensions" in result:
            return {
                "dimensions": result["dimensions"],
                "confidence": result.get("confidence", 0.8),
                "reasoning": result.get("reasoning", "")
            }
        else:
            print(f"⚠️  Некорректный формат ответа LLM: {response[:200]}")
            return {"dimensions": [], "confidence": 0.0, "error": "Ошибка разбора формата"}
    
    except Exception as e:
        print(f"⚠️  Ошибка извлечения измерений: {e}")
        return {"dimensions": [], "confidence": 0.0, "error": str(e)}


def extract_dimensions_from_report(report_file: Path, llm, existing_themes: List[str] = None) -> Optional[Dict]:
    """Извлечение измерений из Markdown-файла
    
    Args:
        report_file: Путь к файлу отчёта
        llm: Экземпляр LLM
        existing_themes: Существующие themes для согласования уровня абстракции
    """
    if not report_file.exists():
        print(f"❌ Файл отчёта не найден: {report_file}")
        return None
    
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Удаление заголовка Markdown (если есть)
        lines = content.split('\n')
        # Пропуск начальных строк с #
        content_lines = []
        for line in lines:
            if line.strip().startswith('#') and not content_lines:
                continue
            content_lines.append(line)
        text = '\n'.join(content_lines).strip()
        
        if not text:
            print(f"⚠️  Содержимое отчёта пусто: {report_file}")
            return None
        
        # Извлечение измерений (с existing_themes)
        result = extract_dimensions_from_text(text, llm, existing_themes=existing_themes)
        
        # Добавление информации об отчёте
        result["report_file"] = str(report_file)
        result["report_date"] = report_file.stem
        result["extraction_date"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        
        return result
    
    except Exception as e:
        print(f"❌ Ошибка чтения отчёта {report_file}: {e}")
        return None


def save_extraction_result(base_dir: Path, result: Dict, report_type: str):
    """Сохранение результата извлечения"""
    dimensions_dir = base_dir / "archive" / "dimensions"
    dimensions_dir.mkdir(parents=True, exist_ok=True)
    
    # Имя файла по дате отчёта
    report_date = result.get("report_date", datetime.now().strftime("%Y-%m-%d"))
    output_file = dimensions_dir / f"{report_date}_{report_type}_dimensions.json"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"✅ Результат извлечения измерений сохранён: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return None


def batch_extract_dimensions(base_dir: Path, report_type: str = None, llm=None, existing_themes: List[str] = None) -> List[Dict]:
    """Пакетное извлечение измерений
    
    Args:
        base_dir: Корневой каталог
        report_type: Тип отчёта (daily/weekly/monthly), None — все типы
        llm: Экземпляр LLM
        existing_themes: Существующие themes; если None — загрузка из themes.yaml
    """
    if not llm:
        llm = init_llm()
        if not llm:
            print("❌ LLM не инициализирован, извлечение невозможно")
            return []
    
    # Если existing_themes не передан — загрузка из themes.yaml
    if existing_themes is None:
        try:
            # Без циклического импорта — читаем yaml здесь
            import yaml
            themes_file = base_dir / "themes.yaml"
            if themes_file.exists():
                with open(themes_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and isinstance(data, dict):
                        existing_themes = data.get('themes', [])
                    else:
                        existing_themes = []
                if existing_themes:
                    print(f"📌 Загружено {len(existing_themes)} существующих themes как ориентир: {existing_themes}")
        except Exception as e:
            print(f"⚠️  Не удалось загрузить themes.yaml, existing themes не используются: {e}")
            existing_themes = []
    
    reports_dir = base_dir / "archive" / "reports"
    results = []
    
    # Типы отчётов для обработки
    types_to_process = [report_type] if report_type else ["daily", "weekly", "monthly"]
    
    for rtype in types_to_process:
        type_dir = reports_dir / rtype
        if not type_dir.exists():
            continue
        
        print(f"\n📂 Обработка{rtype}отчётов...")
        report_files = sorted(type_dir.glob("*.md"))
        
        for report_file in report_files:
            print(f"  Обработка: {report_file.name}")
            result = extract_dimensions_from_report(report_file, llm, existing_themes=existing_themes)
            
            if result and result.get("dimensions"):
                # Добавление типа отчёта
                result["report_type"] = rtype
                
                # Сохранение результата извлечения
                save_extraction_result(base_dir, result, rtype)
                
                results.append(result)
                print(f"    ✅ Извлечено {len(result['dimensions'])} измерений: {', '.join(result['dimensions'][:5])}")
                # Вывод reasoning (для отладки)
                if result.get("reasoning"):
                    print(f"       Рассуждение: {result['reasoning'][:100]}...")
            else:
                print(f"    ⚠️  Измерения не извлечены")
    
    return results


def load_extraction_results(base_dir: Path) -> List[Dict]:
    """Загрузка всех результатов извлечения"""
    dimensions_dir = base_dir / "archive" / "dimensions"
    
    if not dimensions_dir.exists():
        return []
    
    results = []
    for json_file in dimensions_dir.glob("*_dimensions.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                results.append(result)
        except Exception as e:
            print(f"⚠️  Ошибка чтения результата извлечения {json_file.name}: {e}")
    
    return results


if __name__ == "__main__":
    # CLI
    import argparse
    
    parser = argparse.ArgumentParser(description="Извлечение измерений из отчётов")
    parser.add_argument("--report-type", choices=["daily", "weekly", "monthly"], 
                       help="Тип отчёта (по умолчанию — все)")
    parser.add_argument("--report-file", type=str,
                       help="Путь к одному файлу отчёта")
    parser.add_argument("--base-dir", type=str,
                       help="Корневой каталог (по умолчанию — каталог скрипта)")
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    
    llm = init_llm()
    if not llm:
        print("❌ Не удалось инициализировать LLM, выход")
        sys.exit(1)
    
    # Загрузка existing_themes (если есть)
    existing_themes = None
    try:
        import yaml
        themes_file = base_dir / "themes.yaml"
        if themes_file.exists():
            with open(themes_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and isinstance(data, dict):
                    existing_themes = data.get('themes', [])
    except Exception:
        pass
    
    if args.report_file:
        # Один файл
        report_file = Path(args.report_file)
        result = extract_dimensions_from_report(report_file, llm, existing_themes=existing_themes)
        if result:
            report_type = result.get("report_type", "daily")
            save_extraction_result(base_dir, result, report_type)
            print(f"\nИзвлечённые измерения: {result.get('dimensions', [])}")
    else:
        # Пакетная обработка
        results = batch_extract_dimensions(base_dir, args.report_type, llm, existing_themes=existing_themes)
        print(f"\n✅ Обработано {len(results)} отчётов")

