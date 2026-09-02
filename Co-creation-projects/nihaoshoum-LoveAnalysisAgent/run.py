# %% [markdown]
# # ========================================
# # Помощник по анализу настроений
# # ========================================

# %% [markdown]
# 

# %%
from hello_agents import SimpleAgent, HelloAgentsLLM, ToolRegistry
from hello_agents.tools import Tool, ToolParameter, ToolRegistry
from typing import Dict, Any, List
import os
import pandas as pd
import re
from paddlenlp import Taskflow



# %%

os.environ["LLM_API_KEY"] = "" # Ваш собственный
os.environ["LLM_BASE_URL"] = "https://api-inference.modelscope.cn/v1"
os.environ["LLM_TIMEOUT"] = "60"


# %% [markdown]
# # ========================================
# # 1. Определить инструменты анализа кода
# # ========================================

# %% [markdown]
# Очистка текста

# %%
class ProcessChatHistoryTool(Tool):
    """
    导入并清洗微信或QQ的文本聊天记录
Наследуйте абстрактный класс Tool и реализуйте методы run и get_parameters.
    """
    def __init__(self):
        super().__init__(
            name="process_chat_history",
            description="读取微信/QQ聊天记录TXT文件，自动清洗，返回结构化DataFrame"
        )

    def run(self, parameters: Dict[str, Any]) -> pd.DataFrame:
        """
Запись об исполнении инструмента
        :param parameters: 外部传入参数 file_path, chat_type
:return: Очищенный DataFrame
        """
# Получаем значение из параметра
        file_path = parameters.get("file_path", "")
        chat_type = parameters.get("chat_type", "wechat")

        messages = []
        pattern = re.compile(r'(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s+(.+?):\s+(.+)')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    match = pattern.match(line)
                    if match:
                        time, sender, content = match.groups()

# Фильтровать системные сообщения
если есть (ключевое слово в контенте для ключевого слова в ['[Изображение]', '[Видео]', 'Отзыв сообщения', 'Сделал фото']):
                            continue

                        messages.append({
                            'time': time,
                            'sender': sender,
                            'content': content
                        })

            df = pd.DataFrame(messages)
print(f" ✅ Успешно импортировано {len(df)} действительных записей чата!")
            return df

        except Exception as e:
print(f"❌ Не удалось прочитать файл: {str(e)}")
            return pd.DataFrame()

    def get_parameters(self) -> List[ToolParameter]:
        """
Определить параметры инструмента
        """
        return [
            ToolParameter(
                name="file_path",
                type="string",
описание="Путь к текстовому файлу записи чата",
                required=True
            ),
            ToolParameter(
                name="chat_type",
                type="string",
описание="Тип чата: wechat или qq",
                required=False
            )
        ]

# %% [markdown]
#сентиментальныйанализ

# %%
class AnalyzeSentimentAndMoodTool(Tool):
"""Используйте модель СКЕПА-ЭРНИ для анализа эмоций и настроения в записях чата"""
    
    def __init__(self):
        super().__init__(
            name="analyze_sentiment_and_mood",
            description="分析聊天记录的情感倾向（正面/负面）与心情（开心/生气/平淡）"
        )
        # 初始化模型（只加载一次）
        self.sentiment_analyzer = Taskflow(
            "sentiment_analysis", 
            model="skep_ernie_1.0_large_ch",
        )

    def run(self, parameters: Dict[str, Any]) -> pd.DataFrame:
        df = parameters.get("df", pd.DataFrame())
        
        if df.empty:
            return df

        contents = df['content'].tolist()

        try:
            results = self.sentiment_analyzer(contents)

            sentiments = [res['sentiment_key'] for res in results]
            confidence = [
                res['positive_probs'] if res['sentiment_key'] == 'positive' 
                else 1 - res['positive_probs'] 
                for res in results
            ]

            moods = []
            for res in results:
                if res['sentiment_key'] == 'positive':
moods.append('счастлив/одобрено')
                else:
                    neg_prob = 1 - res['positive_probs']
                    if neg_prob > 0.8:
moods.append('злой/грустный')
                    else:
moods.append('беспомощный/безвкусный')

            df['sentiment'] = sentiments
            df['mood'] = moods
            df['confidence'] = confidence

print("Анализ эмоций и настроения завершен!")
            return df

        except Exception as e:
print(f"❌ Ошибка анализа тональности: {e}")
            return df

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="df",
                type="object",
                description="清洗后的聊天记录DataFrame",
                required=True
            )
        ]

# %% [markdown]
#статистика настроений

# %%
class SummarizeEmotionStatsTool(Tool):
"""Статистика данных об эмоциях в чате, создание отчетов и структурированных результатов"""
    
    def __init__(self):
        super().__init__(
            name="summarize_emotion_stats",
            description="统计情感分析结果，计算开心/生气数量与占比，返回报告字典"
        )

    def run(self, parameters: Dict[str, Any]) -> dict:
        df = parameters.get("df", pd.DataFrame())
        sender_name = parameters.get("sender_name", None)
        
        if df.empty or 'sentiment' not in df.columns:
print("❌ Данные пусты или анализ настроений еще не проводился, сначала запустите первые два инструмента!")
            return {}

        if sender_name:
            analysis_df = df[df['sender'] == sender_name].copy()
            if analysis_df.empty:
                print(f"⚠️ 未找到 {sender_name} 的聊天记录")
                return {}
            print(f"🔍 正在统计 {sender_name} 的情感数据...")
        else:
            analysis_df = df.copy()
print("🔍 Подсчет эмоциональных данных всех сотрудников...")

        total_messages = len(analysis_df)
        happy_count = len(analysis_df[analysis_df['sentiment'] == 'positive'])
        angry_count = len(analysis_df[analysis_df['sentiment'] == 'negative'])

        happy_ratio = round((happy_count / total_messages) * 100, 2) if total_messages > 0 else 0.0
        angry_ratio = round((angry_count / total_messages) * 100, 2) if total_messages > 0 else 0.0

        print("\n" + "="*30)
print(f"📊【Отчет по статистике эмоций】")
print(f"Общее количество действительных сообщений: {total_messages}")
        print(f"😄 开心/认可: {happy_count} 条 (占比 {happy_ratio}%)")
        print(f"😡 生气/难过: {angry_count} 条 (占比 {angry_ratio}%)")
print(f"😐 нейтральный/другой: {total_messages - Happy_count - Angry_count} элементов")
        print("="*30 + "\n")

        return {
            'total_messages': total_messages,
            'happy_count': happy_count,
            'angry_count': angry_count,
            'happy_ratio': happy_ratio,
            'angry_ratio': angry_ratio
        }

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="df",
                type="object",
                description="已完成情感分析的 DataFrame",
                required=True
            ),
            ToolParameter(
                name="sender_name",
                type="string",
описание="Необязательно, укажите имя докладчика",
                required=False
            )
        ]

# %%
class PlotEmotionChartTool(Tool):
"""Постройте статистические результаты настроений в виде гистограммы"""
    
    def __init__(self):
        super().__init__(
            name="plot_emotion_chart",
описание="Нарисуйте визуальную гистограмму на основе словаря статистики настроений"
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        stats = parameters.get("stats", {})
        
        if not stats:
return «⚠️ Нет статистических данных, невозможно создать диаграмму»

# Установить китайский шрифт
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

labels = ['счастливый/одобренный', 'злой/грустный']
        counts = [stats['happy_count'], stats['angry_count']]
        colors = ['#FF9999', '#66B2FF']

        plt.figure(figsize=(8, 5))
        bars = plt.bar(labels, counts, color=colors)
plt.title(f"Статистика распределения настроений (всего: {stats['total_messages']})", fontsize=15)
plt.ylabel('Количество выступлений', размер шрифта=12)

# Отображение значения
        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), ha='center', va='bottom', fontsize=12)

        plt.show()
return " ✅ Диаграмма построена успешно!"

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="stats",
                type="object",
                description="summarize_emotion_stats 函数返回的统计字典",
                required=True
            )
        ]

# %% [markdown]
# # ========================================
# # 2. Создайте реестр инструментов и агент
# # ========================================

# %%
tool_registry = ToolRegistry()

tool_registry.register_tool(ProcessChatHistoryTool())
tool_registry.register_tool(AnalyzeSentimentAndMoodTool())
tool_registry.register_tool(SummarizeEmotionStatsTool())
tool_registry.register_tool(PlotEmotionChartTool())

print(" ✅Все инструменты анализа настроений успешно зарегистрированы!")

# %% [markdown]
# # ========================================
# # 3. Инициализируем большую модель
# # ========================================

# %%
print(">>> 实际读取到的 Base URL 是：", repr(os.getenv("LLM_BASE_URL")))
llm = HelloAgentsLLM(
	 model_id="Qwen/Qwen2.5-72B-Instruct",  # ✅ 使用支持的 72B 模型，注意大写 Q
	 api_key="",
	base_url="https://api-inference.modelscope.cn/v1"
	)
# Распечатайте реальный URL-адрес базового клиента, чтобы подтвердить, вступит ли он в силу
print("Базовый URL-адрес базового клиента:", llm._client.base_url)

# %% [markdown]
# # ========================================
# # 4. Определить слова системных подсказок
# # ========================================

# %%
system_prompt = """Вы являетесь экспертом в области психологии интимных отношений с 10-летним опытом, а также эмоционально интеллектуальным коммуникативным тренером. Ваша задача — глубоко анализировать записи чата, предоставленные пользователями, и предоставлять подробные отчеты по анализу настроений.

Пожалуйста, строго следуйте инструкциям ниже:
1. **Контекстное понимание**. В сочетании с контекстом точно определите этапы отношений сторон диалога (например, период двусмысленности, период любви и период холодной войны).
2. **Исследование подтекста**: не просто читайте поверхностный текст, но глубоко поймите истинные эмоции, потребности и невысказанный подтекст, стоящий за словами собеседника.
3. **情感量化**：基于对话的亲密度、回应速度和情绪价值,给出一个0-100分的“心动指数”。
4. **回复建议**：针对当前的对话僵局或话题,提供3种不同风格(如:幽默风趣、深情走心、推拉试探）的高情商回复话术。

Пожалуйста, выведите отчет в формате Markdown. Структура отчета должна содержать:
- **Сердечный индекс**: (дайте конкретные оценки и краткие комментарии)
- **Углубленная интерпретация**: (проанализируйте психологическое состояние и потенциальные намерения другой стороны)
- **Перевод подтекста**: (Выберите 1–2 ключевые строки диалога для «перевода»)
- **Ответ с высоким EQ**: (предоставьте 3 конкретных варианта ответа)
"""

# %% [markdown]
# # ========================================
# # 5. Создать агент
# # ========================================

# %%
agent = SimpleAgent(
name="Ассистент по анализу настроений",
llm=llm,
system_prompt=system_prompt,
tool_registry=tool_registry
)

# %% [markdown]
# # ========================================
# # 6. Запустите пример
# # ========================================

# %%
with open("data/1.txt","r",encoding="utf-8") as f:
  talktxt=f.read()

print('---------------История чата---------------')
print(talktxt)

print('--------------Начать анализ записей--------------')
print("当前 LLM_BASE_URL:", repr(os.environ["LLM_BASE_URL"]))
result=agent.run(talktxt)
print(result)
print('---------------Сохранить результаты ---------------')
with open("outputs/review_report.md", "w", encoding="utf-8") as f:
  f.write(result)
print("\nОтчет о проверке сохранен в файле outputs/review_report.md")


