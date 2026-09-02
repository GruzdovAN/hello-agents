# Интеллектуальный помощник по анализу акций — документация по развёртыванию (DEPLOY.md)

> **Версия**: v0.1.0  
> **Дата**: 2026-05-09  
> **Назначение**: развёртывание в production / development

---

## Содержание

1. [Требования к окружению](#1-требования-к-окружению)
2. [Локальное развёртывание для разработки](#2-локальное-развёртывание-для-разработки)
3. [Контейнеризация с Docker](#3-контейнеризация-с-docker)
4. [Сборка автономного exe](#4-сборка-автономного-exe)
5. [Описание конфигурации](#5-описание-конфигурации)
6. [Проверка работоспособности](#6-проверка-работоспособности)
7. [Частые вопросы](#7-частые-вопросы)

---

## 1. Требования к окружению

| Компонент | Минимальная версия | Описание |
|------|---------|------|
| Python | 3.10+ | Среда выполнения бэкенда |
| Node.js | 18+ | Сборка фронтенда |
| Docker | 24+ | Контейнерное развёртывание (опционально) |
| Docker Compose | 2.0+ | Оркестрация сервисов (опционально) |
| Git | 2.0+ | Контроль версий |

### Внешние сервисы

| Сервис | Назначение | Обязателен? |
|------|------|--------|
| DeepSeek API | LLM-инференс | Да (функции агента) |
| 东方财富妙想 API | Получение финансовых данных | Да (котировки/финансы/новости) |

---

## 2. Локальное развёртывание для разработки

### 2.1 Клонирование проекта

```bash
git clone <your-repo-url>
cd 智能股票分析器
```

### 2.2 Настройка переменных окружения

```bash
cp .env.example .env
# Отредактируйте .env: укажите LLM_API_KEY, MX_APIKEY
# Для локальной разработки используйте BACKEND_PORT=8000 (как в vite proxy)
```

### 2.3 Запуск бэкенда

```bash
# Создание виртуального окружения (рекомендуется)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Установка зависимостей
pip install -r backend/requirements.txt

# Запуск бэкенда (режим разработки, hot reload)
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Или из корня проекта
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Документация API: http://localhost:8000/docs

### 2.4 Запуск фронтенда

```bash
cd frontend
npm install
npm run dev
```

Фронтенд: http://localhost:5173

> В режиме разработки Vite автоматически проксирует `/api` на `http://localhost:8000` — дополнительная настройка не нужна.

### 2.5 Проверка

```bash
# Проверка работоспособности (порт совпадает с BACKEND_PORT, по умолчанию 8000)
curl http://localhost:8000/api/v1/system/health

# Проверка сборки фронтенда
cd frontend && npm run build
```

> **Подсказка по портам**: в `backend/app/config.py` порт бэкенда в режиме разработки по умолчанию **8000**, как и `proxy.target` в `frontend/vite.config.js` (`/api` → `http://localhost:8000`). При изменении `BACKEND_PORT` в `.env` синхронизируйте `proxy.target` в Vite, иначе фронтенд не сможет проксировать запросы к бэкенду.

---

## 3. Контейнеризация с Docker

### 3.1 Структура проекта

```
智能股票分析器/
├── backend/           # Бэкенд FastAPI
│   └── Dockerfile
├── frontend/          # Фронтенд Vue3
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml # Оркестрация сервисов
├── .dockerignore      # Исключения при сборке
└── .env               # Переменные окружения
```

### 3.2 Запуск одной командой

```bash
# Убедитесь, что .env настроен корректно
docker compose up -d
```

### 3.3 Пошаговая сборка

```bash
# Сборка образа бэкенда
docker build -t stock-analyzer-backend -f backend/Dockerfile .

# Сборка образа фронтенда
docker build -t stock-analyzer-frontend -f frontend/Dockerfile .

# Запуск бэкенда
docker run -d -p 8000:8000 \
  -v stock_data:/app/data \
  --name stock-backend \
  stock-analyzer-backend

# Запуск фронтенда
docker run -d -p 8080:80 \
  --name stock-frontend \
  stock-analyzer-frontend
```

### 3.4 Порты сервисов

| Сервис | Порт | Адрес |
|------|------|----------|
| API бэкенда | 8000 | http://localhost:8000/docs |
| Интерфейс | 8080 | http://localhost:8080 |

### 3.5 Частые команды

```bash
# Статус сервисов
docker compose ps

# Логи
docker compose logs -f backend
docker compose logs -f frontend

# Перезапуск
docker compose restart

# Остановка и очистка
docker compose down

# Пересборка и запуск
docker compose up -d --build
```

### 3.6 Персистентность данных

База SQLite сохраняется через Docker Volume:

- **Имя Volume**: `stock_analyzer_data`
- **Путь монтирования**: `/app/data`
- **Файл БД**: `/app/data/stock_analyzer.db`

```bash
# Просмотр Volume
docker volume ls | grep stock

# Резервное копирование БД
docker compose exec backend python -c "
import shutil
shutil.copy('/app/data/stock_analyzer.db', '/tmp/backup.db')
"
docker compose cp backend:/tmp/backup.db ./backup.db
```

---

## 4. Сборка автономного exe

Упаковка фронтенда и бэкенда в один `.exe` — без установки Python/Node.js.

### 4.1 Требования

| Компонент | Назначение | Только для сборки? |
|------|------|:---:|
| Python 3.10+ | Сборка PyInstaller | Да |
| Node.js 18+ | Сборка фронтенда | Да |
| PyInstaller | Python → exe | Да |

> Для запуска достаточно Windows, без дополнительных зависимостей.

### 4.2 Сборка одной командой

```bash
# 1. Установка зависимостей для сборки
pip install pyinstaller

# 2. Запуск скрипта сборки (из корня проекта)
python scripts/build_exe.py

# 3. Или принудительная пересборка фронтенда через переменную окружения
# Отредактируйте .env: BUILD_EXE=1, затем выполните команду выше
```

### 4.3 Результат сборки

```
dist_exe/
├── stock_analyzer.exe      # Основная программа (фронтенд + бэкенд)
├── .env.example             # Шаблон конфигурации
└── data/                    # Каталог данных (создаётся при запуске)
```

### 4.4 Использование

```bash
# 1. Скопируйте каталог dist_exe/ на целевую Windows-машину
# 2. Переименуйте .env.example в .env
# 3. Укажите API Key в .env (LLM_API_KEY, MX_APIKEY)
# 4. Запустите stock_analyzer.exe двойным щелчком
# 5. Откройте в браузере http://127.0.0.1:<BACKEND_PORT>/dashboard
#    (по умолчанию как в app.config: для exe часто 5174 — смотрите .env рядом с exe)
```

- После запуска браузер откроется автоматически (`NO_BROWSER=1` отключает автозапуск)
- Окно exe показывает логи работы
- Для выхода закройте окно

### 4.5 Переменная окружения BUILD_EXE

```bash
# Windows PowerShell
$env:BUILD_EXE="1"
python scripts/build_exe.py

# Или в .env
# BUILD_EXE=1
```

### 4.6 Настройка порта

В `.env`:
```
BACKEND_HOST=0.0.0.0
BACKEND_PORT=9000
```
Перезапустите exe.

---

## 5. Описание конфигурации

### 5.1 Полный список переменных окружения

| Переменная | Значение по умолчанию | Описание |
|--------|--------|------|
| `LLM_MODEL_ID` | `deepseek-chat` | Имя LLM-модели |
| `LLM_API_KEY` | — | **Обязательно** API-ключ LLM |
| `LLM_BASE_URL` | `https://api.deepseek.com` | Адрес LLM-сервиса |
| `LLM_TIMEOUT` | `60` | HTTP-таймаут LLM (с); бэкенд объединяет с более высоким нижним пределом, чтобы многошаговый Agent не обрывался преждевременно |
| `BUFFETT_MAX_REFLECTIONS` | `0` | Число раундов рефлексии после черновика оценки Баффета (опционально, см. `.env.example`) |
| `MX_APIKEY` | — | **Обязательно** API-ключ 东方财富妙想 |
| `MX_API_URL` | `https://mkapi2.dfcfs.com/finskillshub` | Адрес API 妙想 |
| `MX_CACHE_TTL_SECONDS` | `600` | TTL in-process кэша запросов 妙想 (с) |
| `MX_REPLAY_FIXTURES` | выкл. | При true — приоритетно воспроизводит fixture из `MX_FIXTURE_DIR`, без HTTP к 妙想 |
| `MX_FIXTURE_DIR` | `backend/fixtures/mx_raw` | Каталог воспроизведения |
| `BACKEND_HOST` | `0.0.0.0` | Адрес прослушивания бэкенда |
| `BACKEND_PORT` | **dev `8000`** / **exe по умолчанию `5174`** | Без переменной окружения выбирается в `config.py` по признаку frozen |
| `FRONTEND_PORT` | `5173` | Порт фронтенда в dev |
| `FRONTEND_DIR` | — | Опционально: явный путь к собранному `dist` фронтенда |
| `DATA_DIR` | — | Опционально: каталог данных; по умолчанию рядом с exe или `data` в корне проекта |
| `DATABASE_URL` | `sqlite:///./data/stock_analyzer.db` | Подключение к БД |
| `BUILD_EXE` | — | Для скрипта сборки: `1`/`true`/`rebuild` — принудительная пересборка фронтенда |
| `REDIS_*` | см. `.env.example` | **Зарезервировано**, в текущей версии не используется (redis в `requirements.txt` закомментирован) |
| `JWT_SECRET_KEY` | `dev-secret-key` | **Зарезервировано**, в текущей версии нет аутентификации |
| `JWT_EXPIRE_MINUTES` | `1440` | **Зарезервировано**, вступит в силу после подключения аутентификации |

Дополнение по путям API (согласовано со Swagger):

- Потоковый AI-анализ настроений: `POST /api/v1/sentiment/analyze/stream` (совместимость: `POST /api/v1/agent/sentiment/stream`)
- Потоковый AI-анализ данных: `POST /api/v1/data-analysis/analyze/stream` (совместимость: `POST /api/v1/agent/data-analysis/stream`)
- exe / desktop: `POST /api/v1/system/open-external-url` открывает разрешённые http(s) ссылки в браузере по умолчанию

### 5.2 Безопасность (production)

Текущая версия **не требует** JWT. При публичном доступе к API рекомендуется:

- ограничить IP через Nginx/шлюз или добавить отдельный слой аутентификации;
- не коммитить `LLM_API_KEY`, `MX_APIKEY` из `.env` в репозиторий;
- после реализации аутентификации (JWT) сгенерировать ключ:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Записать в .env: JWT_SECRET_KEY=<сгенерированный ключ>
```

### 5.3 Пример конфигурации Nginx reverse proxy (production)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Статика фронтенда
    location / {
        proxy_pass http://frontend:80;
    }

    # API бэкенда
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
```

---

## 6. Проверка работоспособности

### 6.1 Health check бэкенда

```bash
curl http://localhost:8000/api/v1/system/health
```

Нормальный ответ:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "ok",
    "version": "0.1.0",
    "agent_ready": true,
    "skills_ready": true
  }
}
```

- `agent_ready: false` → LLM_API_KEY не настроен
- `skills_ready: false` → MX_APIKEY не настроен

### 6.2 Health check в Docker

Docker Compose автоматически проверяет `/api/v1/system/health` каждые 30 с.

```bash
# Просмотр статуса
docker compose ps
# (healthy) в выводе означает успех
```

---

## 7. Частые вопросы

### В: Как получить API-ключи?

- **DeepSeek API**: https://platform.deepseek.com
- **东方财富妙想 API**: https://dl.dfcfs.com/m/itc4

### В: Фронтенд открывается, но данных нет?

Проверьте `MX_APIKEY` в `.env` и убедитесь, что health check показывает `skills_ready: true`.

### В: Docker-сборка медленная?

Настроен `.dockerignore` для исключения лишних файлов. Первый раз скачиваются базовые образы, далее используется кэш.

### В: Как мигрировать SQLite на PostgreSQL?

Измените `DATABASE_URL`:
```
DATABASE_URL=postgresql://user:password@host:5432/stock_analyzer
```
И замените в `requirements.txt` `aiosqlite` на `asyncpg`.

### В: Как масштабировать на несколько реплик?

Бэкенд stateless и поддерживает несколько реплик (для SQLite нужен PostgreSQL/MySQL):

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3
  frontend:
    deploy:
      replicas: 2
```

> При нескольких репликах переключите хранилище на сервер БД (PostgreSQL) и добавьте Redis-кэш.

---

## Приложение

### A. Сетевая архитектура

```
Браузер(8080)
    │
    ▼
Nginx(контейнер фронтенда:80)
    │ /           → dist/ (SPA статика)
    │ /api/*      → proxy_pass
    │
    ▼
FastAPI(контейнер бэкенда:8000)
    │
    ├── SQLite (/app/data)
    ├── HelloAgents (инференс агента)
    └── 东方财富妙想API (внешние финансовые данные)
```

### B. Сравнение dev и production

| Параметр | Разработка | Production |
|------|------|------|
| Запуск бэкенда | `uvicorn --reload` | `uvicorn` (без hot reload) |
| Запуск фронтенда | `vite dev` (5173) | Nginx (80) |
| Прокси API | Vite proxy | Nginx reverse proxy |
| База данных | локальный файл | Docker Volume |
| CORS | все источники | только домен фронтенда |
