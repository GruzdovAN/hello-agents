"""
Портал приложений FastAPI — агент расширения английского предложения
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Добавьте текущий каталог (бэкэнд) в путь Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from routers.expand import router as expand_router

#Создаем приложение FastAPI
app = FastAPI(
title="API агента расширения английских предложений",
описание="Приложение для обучения письму на английском языке, основанное на многоагентном сотрудничестве",
    version="1.0.0"
)

# Настройте CORS
app.add_middleware(
    CORSMiddleware,
allow_origins=["*"], # Разрешить все источники (среда разработки)
    allow_credentials=True,
allow_methods=["*"], # Разрешить все методы HTTP
allow_headers=["*"], # Разрешить все заголовки запросов
)

# Содержит маршруты
app.include_router(expand_router)


# Унифицированная обработка исключений
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
"""Глобальный обработчик исключений"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


# корневой путь
@app.get("/")
async def root():
"""Корневой путь"""
    return {
"message": "API агента расширения предложений на английском языке",
        "version": "1.0.0",
        "docs": "/docs"
    }


#Проверка здоровья
@app.get("/health")
async def health_check():
"""Проверка здоровья"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
