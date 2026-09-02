from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import json
import shutil
import uuid
import datetime
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from .agents.helper_agent import get_helper_agent

app = FastAPI(title="SoftwareDevHelper API")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов фронтенда
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend")
app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")

# Каталог данных
data_dir = os.path.join(os.path.dirname(__file__), "../data")
sessions_dir = os.path.join(data_dir, "sessions")
os.makedirs(sessions_dir, exist_ok=True)
user_memory_file = os.path.join(data_dir, "user_memory.json")

# Инициализация агента (для простоты восстанавливаем контекст при каждом запросе)
# SimpleAgent по умолчанию хранит историю в памяти; для нескольких сессий нужен экземпляр на сессию
# или инъекция истории при каждом запросе.
# Для совместимости с HelloAgents кэшируем экземпляры агентов в памяти.
agent_sessions = {}

def get_or_create_agent(session_id: str):
    if session_id not in agent_sessions:
        agent = get_helper_agent()
        # Попытка загрузить историю
        session_file = os.path.join(sessions_dir, f"{session_id}.json")
        if os.path.exists(session_file):
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                history = data.get("messages", [])
                # Простое восстановление истории в agent
                # SimpleAgent хранит сообщения во внутреннем списке _history
                for msg in history:
                    from hello_agents.core.message import Message
                    if msg.get("isUser"):
                        agent._history.append(Message(role="user", content=msg.get("text", "")))
                    else:
                        # Для упрощения восстанавливаем только текст,
                        # чтобы неполные tool_calls не ломали следующий вызов LLM
                        agent._history.append(Message(role="assistant", content=msg.get("text", "")))
        agent_sessions[session_id] = agent
    return agent_sessions[session_id]

def save_session_history(session_id: str, title: str, text: str, is_user: bool, tool_calls: list = None):
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    history = []
    if os.path.exists(session_file):
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            history = data.get("messages", [])
            title = data.get("title", title)

    msg_data = {
        "text": text,
        "isUser": is_user,
        "timestamp": datetime.datetime.now().isoformat()
    }
    if tool_calls:
        msg_data["tool_calls"] = tool_calls

    history.append(msg_data)

    with open(session_file, "w", encoding="utf-8") as f:
        json.dump({"title": title, "messages": history, "updated_at": datetime.datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)

class ChatRequest(BaseModel):
    message: str
    session_id: str

class UserLevelRequest(BaseModel):
    level: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open(os.path.join(frontend_dir, "templates/index.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/sessions")
async def get_sessions():
    sessions = []
    for filename in os.listdir(sessions_dir):
        if filename.endswith(".json"):
            session_id = filename[:-5]
            with open(os.path.join(sessions_dir, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
                sessions.append({
                    "id": session_id,
                    "title": data.get("title", "Новая сессия"),
                    "updated_at": data.get("updated_at", "")
                })
    # Сортировка по времени обновления (новые первыми)
    sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    return {"sessions": sessions}

@app.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    if not os.path.exists(session_file):
        return {"messages": []}
    with open(session_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        return {"messages": data.get("messages", [])}

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    session_file = os.path.join(sessions_dir, f"{session_id}.json")
    if os.path.exists(session_file):
        os.remove(session_file)
    if session_id in agent_sessions:
        del agent_sessions[session_id]
    return {"status": "success"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            
        agent = get_or_create_agent(session_id)
        
        # Заголовок сессии — первые 15 символов первого сообщения
        title = request.message[:15] + "..." if len(request.message) > 15 else request.message
        
        # Сохранить сообщение пользователя
        save_session_history(session_id, title, request.message, True)
        
        # Получить ответ
        # Запомнить длину истории до запуска
        history_len_before = len(agent.get_history())
        response = agent.run(request.message)
        
        # Извлечь новые записи истории и информацию о вызовах инструментов
        tool_calls_info = []
        current_history = agent.get_history()
        new_messages = current_history[history_len_before:]
        
        for msg in new_messages:
            # Сообщения assistant с tool_calls
            if msg.role == "assistant" and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    # Получить объект function
                    func = getattr(tc, "function", None)
                    if func:
                        # Убедиться, что arguments — строка
                        args = getattr(func, "arguments", "{}")
                        if not isinstance(args, str):
                            try:
                                args = json.dumps(args, ensure_ascii=False)
                            except:
                                args = str(args)
                        tool_calls_info.append({
                            "id": getattr(tc, "id", ""),
                            "name": getattr(func, "name", ""),
                            "arguments": args,
                            "result": ""
                        })
            # Сообщения роли tool (результат выполнения инструмента)
            elif msg.role == "tool":
                tool_call_id = getattr(msg, "tool_call_id", None)
                if tool_call_id:
                    for tc_info in tool_calls_info:
                        if tc_info["id"] == tool_call_id:
                            tc_info["result"] = msg.content
                            break

        # Сохранить ответ ассистента (вместе с вызовами инструментов)
        save_session_history(session_id, title, response, False, tool_calls=tool_calls_info)

        return {"response": response, "session_id": session_id, "tool_calls": tool_calls_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_project")
async def upload_project(session_id: str = Form(...), file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Принимаются только архивы в формате .zip")

    upload_dir = os.path.join(os.path.dirname(__file__), "../outputs/uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        agent = get_or_create_agent(session_id)
        
        prompt = f"Пользователь загрузил архив проекта по пути: {file_path}. По текущему заданию напиши pytest-тесты, используй инструмент code_test для проверки и оценки, затем дай обратную связь и обнови запись об уровне пользователя."

        save_session_history(session_id, "Тест загруженного проекта", f"[Загрузка проекта] {file.filename}", True)

        history_len_before = len(agent.get_history())
        response = agent.run(prompt)
        
        tool_calls_info = []
        current_history = agent.get_history()
        new_messages = current_history[history_len_before:]
        
        for msg in new_messages:
            if msg.role == "assistant" and getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    func = getattr(tc, "function", None)
                    if func:
                        # Убедиться, что arguments — строка
                        args = getattr(func, "arguments", "{}")
                        if not isinstance(args, str):
                            try:
                                args = json.dumps(args, ensure_ascii=False)
                            except:
                                args = str(args)
                        tool_calls_info.append({
                            "id": getattr(tc, "id", ""),
                            "name": getattr(func, "name", ""),
                            "arguments": args,
                            "result": ""
                        })
            elif msg.role == "tool":
                tool_call_id = getattr(msg, "tool_call_id", None)
                if tool_call_id:
                    for tc_info in tool_calls_info:
                        if tc_info["id"] == tool_call_id:
                            tc_info["result"] = msg.content
                            break

        save_session_history(session_id, "Тест загруженного проекта", response, False, tool_calls=tool_calls_info)

        return {"response": response, "file_path": file_path, "session_id": session_id, "tool_calls": tool_calls_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user_memory")
async def get_user_memory():
    if not os.path.exists(user_memory_file):
        return {"level": "beginner", "history": []}
    with open(user_memory_file, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/api/user_memory/level")
async def update_user_level(request: UserLevelRequest):
    memory = {"level": "beginner", "history": []}
    if os.path.exists(user_memory_file):
        with open(user_memory_file, "r", encoding="utf-8") as f:
            memory = json.load(f)
            
    memory["level"] = request.level
    
    with open(user_memory_file, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)
        
    return {"status": "success", "level": memory["level"]}

@app.delete("/api/user_memory")
async def reset_user_memory():
    """Сбросить память пользователя (очистить историю и вернуть beginner)"""
    default_memory = {"level": "beginner", "history": []}
    
    os.makedirs(os.path.dirname(user_memory_file), exist_ok=True)
    with open(user_memory_file, "w", encoding="utf-8") as f:
        json.dump(default_memory, f, ensure_ascii=False, indent=2)
        
    return {"status": "success"}
