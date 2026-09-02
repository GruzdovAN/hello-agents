"""
Инструмент управления темами — работа с файлом themes.yaml
"""

import sys
import yaml
from pathlib import Path
from typing import List

# Кодировка консоли UTF-8 (Windows)
# Только при запуске как основной скрипт, чтобы не конфликтовать при импорте
if sys.platform == 'win32' and __name__ == "__main__":
    import io
    if not isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if not isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def load_themes(themes_file: Path) -> List[str]:
    """Загрузить themes из themes.yaml"""
    if not themes_file.exists():
        return []
    
    try:
        with open(themes_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data is None:
                return []
            return data.get('themes', [])
    except Exception as e:
        print(f"⚠️  Ошибка чтения themes.yaml: {e}")
        return []


def save_themes(themes_file: Path, themes: List[str]):
    """Сохранить themes в themes.yaml"""
    themes_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {'themes': themes}
    
    try:
        with open(themes_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"✅ themes сохранены в: {themes_file}")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False


def add_theme(themes_file: Path, theme: str) -> bool:
    """Добавить theme"""
    themes = load_themes(themes_file)
    
    if theme in themes:
        print(f"⚠️  theme '{theme}' уже существует")
        return False
    
    themes.append(theme)
    return save_themes(themes_file, themes)


def remove_theme(themes_file: Path, theme: str) -> bool:
    """Удалить theme"""
    themes = load_themes(themes_file)
    
    if theme not in themes:
        print(f"⚠️  theme '{theme}' не существует")
        return False
    
    themes.remove(theme)
    return save_themes(themes_file, themes)


def list_themes(themes_file: Path):
    """Вывести список всех themes"""
    themes = load_themes(themes_file)
    
    if not themes:
        print("📋 Сейчас нет themes")
        return
    
    print(f"📋 Текущие themes ({len(themes)}):")
    print("-" * 70)
    for i, theme in enumerate(themes, 1):
        print(f"  {i}. {theme}")
    print("-" * 70)


def interactive_theme_management(base_dir: Path):
    """Интерактивное управление темами"""
    themes_file = base_dir / "themes.yaml"
    
    while True:
        print("\n" + "=" * 70)
        print("Управление темами")
        print("=" * 70)
        list_themes(themes_file)
        
        print("\nВыберите действие:")
        print("  1. Добавить theme")
        print("  2. Удалить theme")
        print("  3. Показать themes")
        print("  0. Выход")
        
        choice = input("\nВыбор (0-3): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            theme = input("Введите theme для добавления: ").strip()
            if theme:
                if add_theme(themes_file, theme):
                    print(f"✅ theme добавлен: {theme}")
        elif choice == "2":
            theme = input("Введите theme для удаления: ").strip()
            if theme:
                confirm = input(f"Подтвердить удаление '{theme}'? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', 'да']:
                    if remove_theme(themes_file, theme):
                        print(f"✅ theme удалён: {theme}")
        elif choice == "3":
            list_themes(themes_file)
        else:
            print("⚠️  Неверный выбор, попробуйте снова")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Инструмент управления темами")
    parser.add_argument("--add", type=str, help="Добавить theme")
    parser.add_argument("--remove", type=str, help="Удалить theme")
    parser.add_argument("--list", action="store_true", help="Список всех themes")
    parser.add_argument("--interactive", action="store_true", help="Интерактивный режим")
    parser.add_argument("--base-dir", type=str, help="Базовый каталог (по умолчанию — каталог скрипта)")
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir) if args.base_dir else Path(__file__).parent
    themes_file = base_dir / "themes.yaml"
    
    if args.list:
        list_themes(themes_file)
    elif args.add:
        add_theme(themes_file, args.add)
    elif args.remove:
        remove_theme(themes_file, args.remove)
    elif args.interactive:
        interactive_theme_management(base_dir)
    else:
        # По умолчанию — интерактивный режим
        interactive_theme_management(base_dir)
