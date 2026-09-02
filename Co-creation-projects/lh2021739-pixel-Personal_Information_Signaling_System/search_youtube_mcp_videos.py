"""
Поиск YouTube по темам, оценка, отчёт
Темы из themes.yaml, поиск на YouTube
Объединение, оценка, ежедневный отчёт
"""

import sys
import os
import json
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Кодировка UTF-8 (Windows)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import httpx
except ImportError:
    print("❌ Ошибка: нужен httpx")
    print("💡 pip install httpx")
    sys.exit(1)

try:
    import yaml
except ImportError:
    print("❌ Ошибка: нужен PyYAML")
    print("💡 pip install pyyaml")
    sys.exit(1)

# Загрузка .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv необязательно, пропускается, если не установлен


# LLM для режима research
try:
    from hello_agents.core.llm import HelloAgentsLLM
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Константы
DAYS_WINDOW = int(os.getenv("DAYS_WINDOW", "14"))  # Временное окно: по умолчанию 14 дней.



def load_youtube_api_key():
    """Загрузите ключ API YouTube из переменной среды или файла конфигурации."""
    # Сначала попробуйте переменные среды

    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if api_key:
        return api_key
    
    # Попробуйте прочитать из файла конфигурации

    config_file = Path(__file__).parent / "config"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("YOUTUBE_API_KEY=") and not line.startswith("#"):
                        api_key = line.split("=", 1)[1].strip()
                        if api_key:
                            return api_key
        except Exception as e:
            print(f"⚠️  Ошибка чтения файла конфигурации: {e}")
    
    return None


def load_themes():
    """Прочтите список тем из themes.yaml."""
    themes_file = Path(__file__).parent / "themes.yaml"
    if not themes_file.exists():
        print(f"❌ Ошибка: файл themes.yaml не найден: {themes_file}")
        return []
    
    try:
        with open(themes_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                print(f"❌ Ошибка: themes.yaml пуст или неверного формата")
                return []
            themes = data.get('themes', [])
            if not themes:
                print(f"⚠️  Предупреждение: в themes.yaml нет списка тем")
                return []
            print(f"✅ Загружено {len(themes)} тем: {', '.join(themes)}")
            return themes
    except Exception as e:
        print(f"❌ Ошибка чтения themes.yaml: {e}")
        import traceback
        traceback.print_exc()
        return []


def load_whitelist_channels():
    """Чтение каналов из белого списка из Channels.yaml"""
    channels_file = Path(__file__).parent / "channels.yaml"
    if not channels_file.exists():
        print(f"⚠️  Предупреждение: файл channels.yaml не найден: {channels_file}")
        return []
    
    try:
        with open(channels_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                print(f"⚠️  Предупреждение: channels.yaml пуст или неверного формата")
                return []
            channels = data.get('whitelist_channels', [])
            print(f"✅ Загружено {len(channels)} каналов в белом списке")
            return channels
    except Exception as e:
        print(f"⚠️  Ошибка чтения channels.yaml: {e}")
        return []


def search_youtube_videos(query: str, max_results: int = 10, api_key: str = None):
    """Поиск видео на YouTube"""
    if not api_key:
        api_key = load_youtube_api_key()
    
    if not api_key:
        print("❌ Ошибка: не найден YouTube API Key")
        print("💡 Задайте переменную окружения YOUTUBE_API_KEY или укажите ключ в файле config")
        return None
    
    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "key": api_key,
            "q": query,
            "part": "snippet",
            "type": "video",
            "maxResults": min(max_results, 50),  # API limit
            "order": "relevance"
        }
        
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        
        data = response.json()
        
        if "items" not in data or not data["items"]:
            return []
        
        videos = []
        for item in data["items"]:
            video_info = {
                "video_id": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"]["description"],
                "channel_title": item["snippet"]["channelTitle"],
                "channel_id": item["snippet"]["channelId"],
                "published_at": item["snippet"]["publishedAt"],
                "thumbnail": item["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
                "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                "query": query  # Запишите ключевые слова для поиска

            }
            videos.append(video_info)
        
        return videos
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            print(f"❌ Ошибка: недействительный API-ключ или исчерпана квота (запрос: {query})")
        else:
            print(f"❌ HTTP-ошибка: {e.response.status_code} (запрос: {query})")
        return None
    except Exception as e:
        print(f"❌ Ошибка поиска (запрос: {query}): {str(e)}")
        return None


def parse_published_time(published_at_str: str):
    """Разобрать строку времени публикации в объект datetime."""
    try:
        # API YouTube возвращает формат ISO 8601: 2024-01-01T12:00:00Z.

        dt = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
        return dt
    except Exception as e:
        print(f"⚠️  Ошибка разбора даты публикации: {published_at_str}, ошибка: {e}")
        return None


def is_within_time_window(published_at_str: str, days_window: int = DAYS_WINDOW):
    """Проверьте, находится ли видео в пределах временного окна (по умолчанию 14 дней)."""
    published_time = parse_published_time(published_at_str)
    if not published_time:
        return False
    
    now = datetime.now(timezone.utc)
    time_diff = now - published_time
    
    return time_diff <= timedelta(days=days_window)


def calculate_time_score(published_at_str: str):
    """Рейтинг времени расчета: +3 в течение 24 часов, +2 в течение 48 часов."""
    published_time = parse_published_time(published_at_str)
    if not published_time:
        return 0
    
    now = datetime.now(timezone.utc)
    time_diff = now - published_time
    
    if time_diff <= timedelta(hours=24):
        return 3
    elif time_diff <= timedelta(hours=48):
        return 2
    else:
        return 0


def count_theme_keywords(text: str, themes: list):
    """Подсчитайте количество ключевых слов, встречающихся в теме, в тексте (без учета регистра)."""
    if not text:
        return 0
    
    text_lower = text.lower()
    count = 0
    for theme in themes:
        if theme.lower() in text_lower:
            count += 1
    return count


def score_video(video: dict, themes: list, whitelist_channels: list):
    """Посчитать рейтинг видео"""
    score = 0
    
    # 1. Рейтинг канала в белом списке +10.

    if video['channel_title'] in whitelist_channels:
        score += 10
    
    # 2. Каждое попадание ключевого слова темы в заголовок или описание +5.

    title_matches = count_theme_keywords(video['title'], themes)
    desc_matches = count_theme_keywords(video['description'], themes)
    keyword_score = (title_matches + desc_matches) * 5
    score += keyword_score
    
    # 3. Рейтинг времени выпуска

    time_score = calculate_time_score(video['published_at'])
    score += time_score
    
    return score


def merge_and_deduplicate_videos(all_videos: list):
    """Объединить список видео и удалить дубликаты по videoId"""
    video_dict = {}
    
    for video in all_videos:
        video_id = video['video_id']
        if video_id not in video_dict:
            video_dict[video_id] = video
        else:
            # Если он уже существует, объедините ключевые слова запроса.

            existing_queries = video_dict[video_id].get('queries', [])
            if isinstance(existing_queries, str):
                existing_queries = [existing_queries]
            if video['query'] not in existing_queries:
                existing_queries.append(video['query'])
            video_dict[video_id]['queries'] = existing_queries
    
    return list(video_dict.values())


def generate_action(videos: list):
    """Создать поле действия: создать 1 исполняемое действие из Top1 (≤15 минут)."""
    if not videos:
        return "Пока нет рекомендуемых видео"
    
    # Используйте только Top1
    top1 = videos[0]
    action = f"Посмотреть «{top1['title']}» ({top1['channel_title']}), ориентировочно ≤15 мин."
    
    return action


def has_clickbait_words(title: str):
    """Проверьте, есть ли в заголовке кликбейтные слова"""
    clickbait_words = ['INSANE', 'HYPE', 'SHOCKING', 'UNBELIEVABLE', 'MIND-BLOWING', 
                       'AMAZING', 'INCREDIBLE', 'YOU WON\'T BELIEVE', 'THIS WILL BLOW YOUR MIND']
    title_upper = title.upper()
    for word in clickbait_words:
        if word in title_upper:
            return True
    return False


def is_older_than_days(published_at_str: str, days: int = 30):
    """Проверьте, не старше ли видео указанное количество дней."""
    published_time = parse_published_time(published_at_str)
    if not published_time:
        return False
    
    now = datetime.now(timezone.utc)
    time_diff = now - published_time
    
    return time_diff > timedelta(days=days)


def generate_risk(videos: list, themes: list):
    """Создание поля риска: обнаружение отклонений"""
    if not videos:
        return "Нет рисков"
    
    # Проверяйте только Топ3

    top3 = videos[:3]
    warnings = []
    
    # Проверьте, есть ли видео старше 30 дней

    old_videos = []
    for video in top3:
        if is_older_than_days(video['published_at'], days=30):
            old_videos.append(video['title'])
    
    if old_videos:
        warnings.append(f"В Top3 есть видео старше 30 дн.: {', '.join(old_videos[:2])}")
    
    # Проверьте, есть ли в заголовках словарный запас

    clickbait_videos = []
    for video in top3:
        if has_clickbait_words(video['title']):
            clickbait_videos.append(video['title'])
    
    if clickbait_videos:
        warnings.append(f"Обнаружен кликбейт в заголовке: {', '.join(clickbait_videos[:2])}")
    
    # Если есть предупреждение, верните предупреждение; в противном случае верните положительный отзыв

    if warnings:
        return "; ".join(warnings)
    else:
        return "Сегодняшние сигналы свежие и достаточно надёжные"


def init_research_llm():
    """Инициализируйте LLM для режима исследования (настраивается с помощью Tongyi Qianwen/ModelScope)"""
    if not LLM_AVAILABLE:
        print("⚠️  Предупреждение: модуль hello_agents не установлен, режим research недоступен")
        return None
    
    # Считайте конфигурацию LLM из переменных среды (порядок приоритетов соответствует главе 9).

    # Расстановка приоритетов с использованием конфигурации ModelScope (Тонги Цяньвэнь)

    llm_model = (
        os.getenv("LLM_MODEL") or 
        os.getenv("LLM_MODEL_ID") or
        "Qwen/Qwen2.5-7B-Instruct"  # Модель Тонги Цяньвэнь по умолчанию

    )
    llm_api_key = (
        os.getenv("LLM_API_KEY") or  # Установите приоритет использования LLM_API_KEY (Alibaba Cloud Tongyi Qianwen)

        os.getenv("MODELSCOPE_API_KEY") or 
        os.getenv("MODELSCOPE_API_TOKEN")
    )
    llm_base_url = (
        os.getenv("LLM_BASE_URL") or 
        "https://api-inference.modelscope.cn/v1/"  # Адрес ModelScope по умолчанию

    )
    llm_provider = os.getenv("LLM_PROVIDER", "modelscope")
    
    if not llm_api_key:
        print("⚠️  Предупреждение: LLM API Key не найден, для режима research нужна конфигурация LLM")
        print("💡 Задайте переменные окружения (рекомендуется в .env):")
        print("   MODELSCOPE_API_KEY=your-modelscope-token-here")
        print("   LLM_MODEL=Qwen/Qwen2.5-7B-Instruct")
        print("   LLM_BASE_URL=https://api-inference.modelscope.cn/v1/")
        print("   LLM_PROVIDER=modelscope")
        return None
    
    try:
        llm = HelloAgentsLLM(
            model=llm_model,
            api_key=llm_api_key,
            base_url=llm_base_url,
            provider=llm_provider
        )
        print(f"✅ LLM инициализирован: {llm_model} ({llm_provider})")
        return llm
    except Exception as e:
        print(f"⚠️  Ошибка инициализации LLM: {e}")
        return None


def prepare_sources_data(top3_videos: list):
    """Извлечение данных об источниках из топ3 видео"""
    sources = []
    for video in top3_videos:
        sources.append({
            "title": video['title'],
            "channel": video['channel_title'],
            "url": video['url'],
            "published_at": video['published_at'],
            "score": video['score']
        })
    return sources


def extract_json_from_text(text: str):
    """Извлечение содержимого JSON из текста (обработка форматированного текста, который может вернуть LLM)"""
    # Попробуйте разобрать напрямую

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    
    # Попробуйте извлечь блок кода JSON.

    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Попробуйте извлечь первый полный объект JSON.

    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def generate_research_report(top3_videos: list, themes: list, llm):
    """Research-отчёт через LLM"""
    if not top3_videos:
        return None
    
    # Создание информационного текста видео

    videos_info = []
    for i, video in enumerate(top3_videos, 1):
        videos_info.append(
            f"{i}. Заголовок: {video['title']}\n"
            f"   Канал: {video['channel_title']}\n"
            f"   Время публикации: {video['published_at']}\n"
            f"   Оценка: {video['score']}\n"
            f"   Ссылка: {video['url']}"
        )
    
    videos_text = "\n\n".join(videos_info)
    themes_text = ", ".join(themes)
    
    prompt = f"""На основе Top3 YouTube-видео сформируй структурированный research-отчёт.

Видео:
{videos_text}

Темы поиска: {themes_text}

Верни JSON (без другого текста):
{{
  "question": "ключевой вопрос",
  "key_findings": [
    "находка 1 (возможно/скорее)",
    "находка 2 (возможно/скорее)",
    "находка 3 (возможно/скорее)"
  ],
  "why_it_matters_to_me": "персональное объяснение",
  "next_steps": [
    "действие 1 (≤15 мин)",
    "действие 2 (≤15 мин)",
    "действие 3 (≤15 мин)"
  ]
}}"""

    messages = [
        {"role": "system", "content": "Ты — аналитик: инсайты из видео и практичные рекомендации. Всегда JSON."},
        {"role": "user", "content": prompt}
    ]
    
    try:
        print("\n🔬 Генерация research-отчёта...")
        response = llm.invoke(messages)
        
        if not response:
            print("⚠️  LLM вернул пустой ответ")
            return None
        
        # Извлечь JSON

        research_data = extract_json_from_text(response)
        
        if not research_data:
            print(f"⚠️  Не удалось разобрать ответ LLM как JSON: {response[:200]}...")
            return None
        
        # Проверьте обязательные поля

        required_fields = ["question", "key_findings", "why_it_matters_to_me", "next_steps"]
        missing_fields = [field for field in required_fields if field not in research_data]
        if missing_fields:
            print(f"⚠️  В ответе LLM нет полей: {', '.join(missing_fields)}")
            return None
        
        # Убедитесь, что key_findings представляет собой список и имеет 3 записи.

        if not isinstance(research_data.get("key_findings"), list):
            research_data["key_findings"] = []
        if len(research_data["key_findings"]) != 3:
            # Если элементов меньше 3, заполните или усеките.

            while len(research_data["key_findings"]) < 3:
                research_data["key_findings"].append("Пока нет находок")
            research_data["key_findings"] = research_data["key_findings"][:3]
        
        # Убедитесь, что next_steps представляет собой список, содержащий до 3 элементов.

        if not isinstance(research_data.get("next_steps"), list):
            research_data["next_steps"] = []
        research_data["next_steps"] = research_data["next_steps"][:3]
        
        print("✅ Research-отчёт сгенерирован")
        return research_data
        
    except Exception as e:
        print(f"⚠️  Ошибка генерации research-отчёта: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Главная функция"""
    # Анализ аргументов командной строки

    parser = argparse.ArgumentParser(description="Поиск YouTube — мультитематический поиск и ежедневный отчёт")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["daily_signal", "research"],
        default="research",
        help="Режим: research (по умолчанию, дневной отчёт + research) или daily_signal (только дневной отчёт)"
    )
    args = parser.parse_args()
    mode = args.mode
    
    print("=" * 70)
    print("YouTube — мультитематический поиск и ежедневный отчёт")
    if mode == "research":
        print("Режим: research (дневной отчёт + research-отчёт)")
    else:
        print("Режим: только дневной отчёт")
    print("=" * 70)
    
    # 1. Загрузить конфигурацию

    themes = load_themes()
    if not themes:
        print("❌ Не удалось загрузить список тем, выход")
        return
    
    whitelist_channels = load_whitelist_channels()
    api_key = load_youtube_api_key()
    if not api_key:
        print("❌ Не удалось загрузить API Key, выход")
        return
    
    # 2. Поиск по каждой теме

    print(f"\n🔍 Начало поиска по {len(themes)} темам...")
    all_videos = []
    
    for theme in themes:
        print(f"  Поиск по теме: {theme}")
        videos = search_youtube_videos(theme, max_results=10, api_key=api_key)
        if videos:
            all_videos.extend(videos)
            print(f"    ✅ Найдено {len(videos)} видео")
        else:
            print(f"    ⚠️  Видео не найдены или ошибка поиска")
    
    if not all_videos:
        print("❌ Видео не найдены, выход")
        return
    
    print(f"\n📊 До объединения найдено {len(all_videos)} видео")
    
    # 3. Объедините и удалите дубликаты

    unique_videos = merge_and_deduplicate_videos(all_videos)
    print(f"📊 После дедупликации осталось {len(unique_videos)} уникальных видео")
    
    # 4. Фильтрация временных окон: учитывать только видео за последние DAYS_WINDOW дн.

    print(f"\n⏰ Фильтр по временному окну ({DAYS_WINDOW} дн.)...")
    filtered_videos = [v for v in unique_videos if is_within_time_window(v['published_at'], DAYS_WINDOW)]
    excluded_count = len(unique_videos) - len(filtered_videos)
    if excluded_count > 0:
        print(f"   ⚠️  Отфильтровано {excluded_count} видео старше {DAYS_WINDOW} дн.")
    print(f"   ✅ Осталось {len(filtered_videos)} видео для сортировки")
    
    if not filtered_videos:
        print(f"❌ В окне {DAYS_WINDOW} дн. видео не найдены, выход")
        return
    
    # 5. Рейтинг

    print(f"\n⭐ Начало оценки...")
    for video in filtered_videos:
        score = score_video(video, themes, whitelist_channels)
        video['score'] = score
        video['scoring_details'] = {
            'whitelist_bonus': 10 if video['channel_title'] in whitelist_channels else 0,
            'keyword_matches': count_theme_keywords(video['title'], themes) + count_theme_keywords(video['description'], themes),
            'time_bonus': calculate_time_score(video['published_at'])
        }
    
    # 6. Отсортируйте и выберите топ-3

    sorted_videos = sorted(filtered_videos, key=lambda x: x['score'], reverse=True)
    top3_videos = sorted_videos[:3]
    
    print(f"\n🏆 Top 3 видео:")
    for i, video in enumerate(top3_videos, 1):
        print(f"  {i}. [{video['score']} б.] {video['title']}")
        print(f"     канал: {video['channel_title']}")
        print(f"     ссылка: {video['url']}")
    
    # 7. Создать строку даты

    today = datetime.now().strftime("%Y-%m-%d")
    
    # 8. Создайте выходной каталог.

    base_dir = Path(__file__).parent
    raw_dir = base_dir / "raw" / "youtube"
    archive_dir = base_dir / "archive" / "youtube"
    raw_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 9. Сохраните исходные данные

    raw_file = raw_dir / f"{today}_raw.json"
    raw_data = {
        "date": today,
        "themes_used": themes,
        "whitelist_channels": whitelist_channels,
        "days_window": DAYS_WINDOW,
        "total_videos_found": len(all_videos),
        "unique_videos": len(unique_videos),
        "filtered_videos_count": len(filtered_videos),
        "all_videos": sorted_videos  # Сохраняйте отфильтрованные видео, отсортированные по рейтингу.

    }
    
    try:
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Исходные данные сохранены: {raw_file}")
    except Exception as e:
        print(f"❌ Ошибка сохранения исходных данных: {e}")
        return
    
    # 10. Создавайте и сохраняйте ежедневные отчеты.

    action = generate_action(top3_videos)
    risk = generate_risk(sorted_videos, themes)
    
    daily_report = {
        "date": today,
        "themes_used": themes,
        "dimensions": [],  # Новое: выбираемые пользователем метки измерений (например: [«Здоровье», «Эмоции», «Работа»]), обратная совместимость.

        "top3": [
            {
                "title": video['title'],
                "channel": video['channel_title'],
                "url": video['url'],
                "score": video['score'],
                "published_at": video['published_at'],
                "scoring_details": video['scoring_details']
            }
            for video in top3_videos
        ],
        "action": action,
        "risk": risk
    }
    
    archive_file = archive_dir / f"{today}.json"
    try:
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(daily_report, f, indent=2, ensure_ascii=False)
        print(f"💾 Дневной сигнал сохранён: {archive_file}")
    except Exception as e:
        print(f"❌ Ошибка сохранения дневного сигнала: {e}")
        return
    
    # 11. Если выбран режим исследования, создайте отчет об исследовании.

    if mode == "research":
        llm = init_research_llm()
        if llm:
            try:
                research_report = generate_research_report(top3_videos, themes, llm)
                if research_report:
                    # Добавить поле источников

                    research_report["sources"] = prepare_sources_data(top3_videos)
                    research_report["date"] = today
                    research_report["themes_used"] = themes
                    
                    # Сохранить отчет об исследовании

                    research_file = archive_dir / f"{today}_research.json"
                    with open(research_file, 'w', encoding='utf-8') as f:
                        json.dump(research_report, f, indent=2, ensure_ascii=False)
                    print(f"\n💾 Research-отчёт сохранён: {research_file}")
                    
                    print("\n" + "=" * 70)
                    print("🔬 Сводка research-отчёта")
                    print("=" * 70)
                    print(f"Ключевой вопрос: {research_report.get('question', 'N/A')}")
                    print(f"\nКлючевые находки:")
                    for i, finding in enumerate(research_report.get('key_findings', []), 1):
                        print(f"  {i}. {finding}")
                    print(f"\nПочему это важно: {research_report.get('why_it_matters_to_me', 'N/A')}")
                    print(f"\nСледующие шаги:")
                    for i, step in enumerate(research_report.get('next_steps', []), 1):
                        print(f"  {i}. {step}")
                    print("=" * 70)
                else:
                    print("⚠️  Ошибка генерации research-отчёта, пропуск")
            except Exception as e:
                print(f"⚠️  Ошибка генерации research-отчёта: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️  LLM не настроен, режим research пропущен")
    
    # 12. Отображение ежедневной сводки

    print("\n" + "=" * 70)
    print("📄 Сводка дневного отчёта")
    print("=" * 70)
    print(f"дата: {daily_report['date']}")
    print(f"тема: {', '.join(daily_report['themes_used'])}")
    print(f"\nРекомендуемое действие (Action):")
    print(f"  {daily_report['action']}")
    print(f"\nОценка риска (Risk):")
    print(f"  {daily_report['risk']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
