# Помощник изучения языка Language-Learn-Agent

> Агент для изучения языка через диалог на целевом языке: быт, профессия, энциклопедия, новости.

## 📝 О проекте

- **Проблема**: при изучении английского мало живого общения на языке.
- **Особенности**: направление и сложность по выбору пользователя; длина диалога гибкая — завершение по команде или по решению ИИ; после диалога — сводка ошибок орфографии, грамматики и сложной лексики.
- **Аудитория**: школьники и студенты, специалисты для профессиональной лексики.

## ✨ Основные возможности

- [X] Диалог с учётом предпочтений и уровня сложности.
- [X] Поиск актуальной информации при необходимости и ответы на её основе.
- [X] Сохранение текста диалога; по завершении — сводка ошибок.

## 🛠️ Стек

- HelloAgents
- Python3
- Поиск Tavily

## 🚀 Быстрый старт

### Требования

- Python 3.10+

### Установка зависимостей


pip install -r requirements.txt


### API-ключ


# Создать .env
cp .env.example .env

# Указать ключ в .env


### Запуск

- Запуск `main.py`
- Ввод фразы для начала диалога
- Досрочный выход: `bye` и подобные — диалог завершится автоматически

## 📖 Пример
```
Раунд 1
Введите фразу: Hi, you got anything new about RTX 60 series?
✅ Поиск Tavily инициализирован
⚠️ google-search-results не установлен — SerpApi недоступен
🔧 Гибридный поиск: tavily
INFO:openai._base_client:Retrying request to /chat/completions in 0.475520 seconds
That's a really interesting topic, and I'm glad you brought it up. So, based on the latest rumors,......
......
......
Раунд 4
Введите фразу: bye, i have to go.
Thanks for the reminder. I see that in your last message, "bey" should be "bye," and "i" should be capitalized as "I." So the correct sentence would be: "Bye, I have to go."

It was a pleasure chatting with you about the RTX 60 series and the 5070 Ti. Feel free to come back if you have more questions or want to practice English. Take care! 
Сводка диалога:
Ниже сводка по грамматике и сложной лексике (средний уровень, CET-4–CET-6).
---
### 【Грамматика и типичные ошибки】
1. **Неверная форма глагола в Present Perfect**  
   - Ошибка: `"I have not think"`  
   - Верно: `"I have not thought"` (past participle от think — thought)  
   - Подсказка: в Present Perfect (have/has + V3) нужна форма причастия прошедшего времени.

2. **Ошибка в отрицательном ответе**  
......
......
```

## 📄 Лицензия

MIT License

## 👤 Автор

- GitHub: [@zzuu222](https://github.com/zzuu222)
- Email: zl2891229@gmail.com

## 🙏 Благодарности

Сообществу Datawhale и проекту Hello-Agents!
