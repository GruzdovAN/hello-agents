"""
智能股票分析助手 — exe 打包脚本

использование:
# Упаковка в один клик (выполняется из корневого каталога проекта)
    python scripts/build_exe.py

# Проверяйте окружающую среду только без упаковки
    python scripts/build_exe.py --check

#Принудительно перезапустить сборку npm (по умолчанию пропускается, если интерфейс/dist уже существует, что может ускорить упаковку)
    python scripts/build_exe.py --rebuild-frontend
# Или переменные среды (PowerShell: $env:BUILD_EXE='1'; python scripts/build_exe.py)
# Если вы не хотите извлекать тензорную плату для автономной упаковки: BUILD_EXE_SKIP_TENSORBOARD=1 (может возникнуть ПРЕДУПРЕЖДЕНИЕ, связанное с факелом, которое можно игнорировать)

Результаты упаковки:
dist_exe/stock_analyzer.exe # Основная программа
    dist_exe/.env.example             # 配置模板（需重命名为 .env 并填入 API Key）
    dist_exe/data/                   # 数据目录（自动创建）
"""

import os
import sys
import platform
import shutil
import subprocess
from pathlib import Path

# Windows 控制台默认 GBK，直接 print Unicode 勾选符号会触发 UnicodeEncodeError
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DIST_DIR = PROJECT_ROOT / "dist_exe"
BACKEND_DIR = PROJECT_ROOT / "backend"

# npm в Windows на самом деле — это npm.cmd
_NPM_CMD = "npm.cmd" if platform.system() == "Windows" else "npm"


def ensure_tensorboard_for_pyinstaller_scan() -> None:
"""PyInstaller выполнит импорт torch.utils.tensorboard при анализе PyTorch, полагаясь на дополнительный пакет tensorboard.

    未安装时仅打印 WARNING，不影响生成的 exe（本应用运行时不需要 TensorBoard）。
По умолчанию pip install tensorboard пытается устранить предупреждение; автономную упаковку можно пропустить, установив переменную среды BUILD_EXE_SKIP_TENSORBOARD=1.
    """
    if os.getenv("BUILD_EXE_SKIP_TENSORBOARD", "").lower() in ("1", "true", "yes"):
        print(
            "[*] 已跳过 tensorboard 检查（BUILD_EXE_SKIP_TENSORBOARD）；"
            "若出现 torch.utils.tensorboard 相关 WARNING 可忽略"
        )
        return
    try:
        import tensorboard  # noqa: F401
        return
    except ImportError:
        pass
print("[*] Установка тензорной платы (используется PyInstaller при анализе torch для устранения предупреждений дополнительных модулей)...")
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", "tensorboard"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        print(
"[!] Установка Tensorboard не удалась, упаковка продолжится;"
«ModuleNotFoundError: может возникнуть ПРЕДУПРЕЖДЕНИЕ класса тензорной доски, которое не влияет на работу этой программы»
        )
    else:
print("[ОК] тензорная доска готова")


def _force_rebuild_frontend() -> bool:
    """frontend/dist 已存在时，是否仍执行 npm run build"""
    if "--rebuild-frontend" in sys.argv:
        return True
    v = os.getenv("BUILD_EXE", "").lower()
    return v in ("1", "true", "yes", "rebuild")


def check_env():
    """检查打包所需的工具是否可用"""
    issues = []

#Проверяем НПМ
    try:
        subprocess.run([_NPM_CMD, "--version"], capture_output=True, check=True)
print("[ОК] npm доступен")
    except (subprocess.CalledProcessError, FileNotFoundError):
        issues.append("npm 未安装或不在 PATH 中（需 Node.js）")

    # 检查 PyInstaller
    try:
        subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                       capture_output=True, check=True)
print("[OK] PyInstaller доступен")
    except (subprocess.CalledProcessError, FileNotFoundError):
        issues.append("PyInstaller 未安装，请执行: pip install pyinstaller")

# Проверяем, построен ли интерфейс
    if not (FRONTEND_DIR / "dist" / "index.html").exists():
Issues.append("Внешний интерфейс не создан, он будет построен автоматически")

    return issues


def build_frontend():
"""Создайте интерфейс Vue3 в виде статических файлов"""
print("\n[1/3] Создание интерфейса...")
    env = os.environ.copy()
    result = subprocess.run(
        [_NPM_CMD, "run", "build"],
        cwd=str(FRONTEND_DIR),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
print(f"[ERR] Ошибка сборки внешнего интерфейса:\n{result.stderr}")
        return False
    print(f"[OK] 前端构建完成 -> {FRONTEND_DIR / 'dist'}")
    return True


def build_exe():
"""Используйте PyInstaller для упаковки в формате exe"""
print("\n[2/3] Упаковка PyInstaller...")
    ensure_tensorboard_for_pyinstaller_scan()

# Очистка старых продуктов сборки
    for _d in [DIST_DIR, PROJECT_ROOT / "build"]:
        if _d.exists():
            shutil.rmtree(_d)

    # PyInstaller 参数
    pyi_args = [
        sys.executable, "-m", "PyInstaller",
        "--name", "stock_analyzer",
        "--onefile",
        "--console",
        "--clean",
        "--noconfirm",
        f"--distpath={DIST_DIR}",
        f"--workpath={PROJECT_ROOT / 'build' / 'pyinstaller'}",
        f"--specpath={PROJECT_ROOT / 'build'}",
# Включите этап анализа PyInstaller для анализа пакета app.* в бэкэнде (в противном случае скрытый импорт сообщит, что он не найден)
        f"--paths={BACKEND_DIR}",
# Вход
        str(PROJECT_ROOT / "run_exe.py"),
#Добавляем каталог данных
        "--add-data", f"{FRONTEND_DIR / 'dist'}{os.pathsep}frontend/dist",
        "--add-data", f"{PROJECT_ROOT / 'skills'}{os.pathsep}skills",
        "--add-data", f"{PROJECT_ROOT / 'agents'}{os.pathsep}agents",
        "--add-data", f"{PROJECT_ROOT / 'HelloAgents Optimized' / 'hello_agents'}{os.pathsep}hello_agents",
        "--add-data", f"{BACKEND_DIR}{os.pathsep}backend",
# Скрытый импорт (динамически импортируемые модули)
        "--hidden-import", "app.api.market",
        "--hidden-import", "app.api.financial",
        "--hidden-import", "app.api.news",
        "--hidden-import", "app.api.screener",
        "--hidden-import", "app.api.watchlist",
        "--hidden-import", "app.api.simulation",
        "--hidden-import", "app.api.analysis",
        "--hidden-import", "app.api.buffett",
        "--hidden-import", "app.api.preferences",
        "--hidden-import", "app.services.market_service",
        "--hidden-import", "app.services.news_service",
        "--hidden-import", "app.services.screener_service",
        "--hidden-import", "app.services.analysis_service",
        "--hidden-import", "app.services.watchlist_service",
        "--hidden-import", "app.services.simulation_service",
        "--hidden-import", "app.services.buffett_service",
        "--hidden-import", "app.services.preference_service",
        "--hidden-import", "app.services.mx_timed_cache",
        "--hidden-import", "app.services.dashboard_warmup",
        "--hidden-import", "app.models.database",
        "--hidden-import", "app.models.preference",
        "--hidden-import", "app.models.report",
        "--hidden-import", "app.utils.response",
        "--hidden-import", "app.utils.mx_http",
        "--hidden-import", "app.utils.mx_quota",
        "--hidden-import", "app.utils.mx_fixture",
        "--hidden-import", "app.utils.mock_trading_normalize",
        "--hidden-import", "agents.agent_system",
        "--hidden-import", "agents.coordinator_agent",
        "--hidden-import", "agents.data_analysis_agent",
        "--hidden-import", "agents.sentiment_agent",
        "--hidden-import", "agents.advisor_agent",
        "--hidden-import", "agents.general_advisor_agent",
        "--hidden-import", "agents.tools.mx_data_tool",
        "--hidden-import", "agents.tools.mx_search_tool",
# Общие зависимости
        "--hidden-import", "fastapi",
        "--hidden-import", "uvicorn",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "pydantic",
        "--hidden-import", "sqlalchemy",
        "--hidden-import", "aiosqlite",
        "--hidden-import", "httpx",
        "--hidden-import", "pandas",
        "--hidden-import", "dotenv",
        "--collect-all", "openpyxl",
    ]

    result = subprocess.run(pyi_args, cwd=str(PROJECT_ROOT))
    if result.returncode != 0:
print("[ERR] Упаковка PyInstaller не удалась")
        return False
    print(f"[OK] 打包完成 -> {DIST_DIR / 'stock_analyzer.exe'}")
    return True


def copy_assets():
"""Скопируйте шаблон конфигурации в выходной каталог"""
print("\n[3/3] Копировать файл конфигурации...")

# Копируем шаблон .env
    env_template = PROJECT_ROOT / ".env"
    if env_template.exists():
# Очистка конфиденциальной информации
        import re
        content = env_template.read_text(encoding="utf-8")
# Очистите настоящий ключ API
        content = re.sub(r'(LLM_API_KEY=).+', r'\1your-deepseek-api-key-here', content)
        content = re.sub(r'(MX_APIKEY=).+', r'\1your-mx-apikey-here', content)
        content = re.sub(r'(JWT_SECRET_KEY=).+', r'\1change-this-to-a-random-secret-key', content)
        # 与 exe 默认端口、自动打开的浏览器地址一致（127.0.0.1:5174/dashboard）
        content = re.sub(r'^BACKEND_PORT=.*$', 'BACKEND_PORT=5174', content, flags=re.MULTILINE)
        (DIST_DIR / ".env.example").write_text(content, encoding="utf-8")
        print("[OK] .env.example 已生成（请重命名为 .env 并填入 API Key）")

#Создаем каталог данных
    (DIST_DIR / "data").mkdir(exist_ok=True)
print("[OK] каталог данных/ создан")


def main():
    print("=" * 50)
print("Интеллектуальный помощник по анализу запасов — инструмент для упаковки exe")
    print("=" * 50)

# Переходим в корневой каталог проекта
    os.chdir(str(PROJECT_ROOT))

# Проверка среды
    issues = check_env()
    if "--check" in sys.argv:
        if issues:
            print(f"\n[!] 发现 {len(issues)} 个问题:")
            for i in issues:
                print(f"  - {i}")
        else:
print("\n[OK] Среда упаковки готова")
        return

# Автоматически установить PyInstaller
    for i in issues:
        if "PyInstaller" in i:
print("[*] Установка PyInstaller...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                           check=True)
            issues.remove(i)
            break

    if issues:
        non_critical = [i for i in issues if "未构建" not in i]
        if non_critical:
print(f"\n[ERR] Сначала решите следующие проблемы:")
            for i in non_critical:
                print(f"  - {i}")
            return

# Создаем интерфейс
    if not (FRONTEND_DIR / "dist" / "index.html").exists():
        if not build_frontend():
            return
    else:
        if _force_rebuild_frontend():
            if not build_frontend():
                return
        else:
            print("\n[1/3] 前端已有构建产物，跳过 npm build（加快打包）")
print("Чтобы принудительно перестроить интерфейс:")
            print("        python scripts/build_exe.py --rebuild-frontend")
            if platform.system() == "Windows":
print(" 或 PowerShell:$env:BUILD_EXE='1'; скрипты Python/build_exe.py")
print(" 或 CMD: set BUILD_EXE=1 && скрипты Python/build_exe.py")
            else:
print(" 或：BUILD_EXE=1 скрипты Python/build_exe.py")

# Упаковка PyInstaller
    if not build_exe():
        return

#Копировать конфигурацию
    copy_assets()

    print("\n" + "=" * 50)
print("[ОК] Упаковка завершена!")
print(f"Выходной каталог: {DIST_DIR}")
    print(f"  主程序:   {DIST_DIR / 'stock_analyzer.exe'}")
    print(f"")
print(f" Шаги использования:")
print(f" 1. Скопируйте каталог {DIST_DIR.name}/ на целевой компьютер")
print(f" 2. Переименуйте .env.example в .env")
print(f" 3. Отредактируйте .env и заполните ключ API")
print(f" 4. Дважды щелкните stock_analyzer.exe, чтобы запустить")
print(f" 5. В браузере откроется http://127.0.0.1:5174/dashboard (если BACKEND_PORT не настроен)")
    print("=" * 50)


if __name__ == "__main__":
    main()
