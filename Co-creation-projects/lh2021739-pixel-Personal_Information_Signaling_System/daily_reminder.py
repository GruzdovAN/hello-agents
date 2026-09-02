"""
Ежедневное напоминание — в 23:30 показывает персонажа с напоминанием написать отчёт
Красивое всплывающее окно
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime

# Кодировка консоли UTF-8 (Windows)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("❌ Ошибка: tkinter не установлен (обычно входит в состав Python)")

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  Предупреждение: Pillow не установлен, изображение не отобразится")
    print("💡 Выполните: pip install Pillow")


class DailyReminder:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or Path(__file__).parent
        self.window = None
        self.canvas = None
        self.photo = None
        self.original_image = None
        
        # Настройки окна
        self.window_width = 160
        self.window_height = 160
        self.image_size = (150, 150)  # размер изображения под окно
        
    def load_image(self):
        """Загрузить изображение персонажа"""
        # Попробовать разные пути и форматы
        image_paths = [
            self.base_dir / "assets" / "person.png",
            self.base_dir / "assets" / "person.jpg",
            self.base_dir / "assets" / "person.jpeg",
            self.base_dir / "assets" / "reminder.png",
            self.base_dir / "assets" / "reminder.jpg",
        ]
        
        for img_path in image_paths:
            if img_path.exists():
                try:
                    img = Image.open(img_path)
                    # RGBA для прозрачного фона
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    # Масштабировать
                    img = img.resize(self.image_size, Image.Resampling.LANCZOS)
                    self.original_image = img
                    return True
                except Exception as e:
                    print(f"⚠️  Не удалось загрузить {img_path}: {e}")
                    continue
        
        print("❌ Файл изображения персонажа не найден")
        print("💡 Положите изображение в assets/ с именем person.png или person.jpg")
        return False
    
    def show_reminder(self):
        """Показать окно напоминания"""
        if not TKINTER_AVAILABLE:
            self.show_system_notification()
            return
        
        if not PIL_AVAILABLE:
            try:
                messagebox.showerror("Ошибка", "Pillow не установлен, изображение недоступно\nВыполните: pip install Pillow")
            except:
                print("❌ Ошибка: Pillow не установлен\n💡 Выполните: pip install Pillow")
            return
        
        if not self.load_image():
            try:
                messagebox.showerror("Ошибка", "Файл изображения не найден\nПоложите файл в assets/\nИмена: person.png, person.jpg, reminder.png")
            except:
                print("❌ Ошибка: файл изображения не найден\n💡 Положите файл в assets/")
            return
        
        # Главное окно
        self.window = tk.Toplevel()
        self.window.title("📝 Напоминание о дневном отчёте")
        
        # Свойства окна
        self.window.attributes('-topmost', True)  # поверх всех
        self.window.attributes('-alpha', 0.95)   # полупрозрачность
        
        # Без рамки (опционально)
        # self.window.overrideredirect(True)
        
        # Позиция — правый нижний угол
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = screen_width - self.window_width - 20  # 20 px от правого края
        y = screen_height - self.window_height - 60  # 60 px от низа (панель задач)
        
        self.window.geometry(f"{self.window_width}x{self.window_height}+{x}+{y}")
        
        self.window.configure(bg='#f0f0f0')
        
        self.canvas = tk.Canvas(
            self.window,
            width=self.window_width,
            height=self.window_height,
            bg='#f0f0f0',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.update_image()
        
        self.canvas.bind('<Button-1>', self.on_click)
        self.window.bind('<Button-1>', self.on_click)
        
        self.fade_in()
        
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def update_image(self):
        """Обновить отображаемое изображение"""
        if not self.original_image:
            return
        
        self.photo = ImageTk.PhotoImage(self.original_image)
        
        self.canvas.delete("image")
        x = (self.window_width - self.image_size[0]) // 2
        y = (self.window_height - self.image_size[1]) // 2  # по центру
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo, tags="image")
    
    def fade_in(self):
        """Анимация появления"""
        if not self.window:
            return
        
        alpha = 0.0
        step = 0.05
        
        def fade():
            nonlocal alpha
            if alpha < 0.95:
                alpha += step
                self.window.attributes('-alpha', alpha)
                self.window.after(20, fade)
        
        fade()
    
    def on_click(self, event=None):
        """Обработка клика"""
        self.on_close()
        self.start_write_report()
    
    def on_close(self):
        """Закрыть окно"""
        if self.window:
            alpha = 0.95
            def fade_out():
                nonlocal alpha
                if alpha > 0:
                    alpha -= 0.1
                    try:
                        self.window.attributes('-alpha', alpha)
                        self.window.after(30, fade_out)
                    except:
                        pass
                else:
                    if self.window:
                        self.window.destroy()
            fade_out()
    
    def start_write_report(self):
        """Запустить написание отчёта"""
        try:
            write_report_script = self.base_dir / "write_report.py"
            if not write_report_script.exists():
                error_msg = f"write_report.py не найден\nПуть: {write_report_script}"
                try:
                    messagebox.showerror("Ошибка", error_msg)
                except:
                    print(f"❌ {error_msg}")
                return
            
            python_exe = sys.executable
            subprocess.Popen(
                [python_exe, str(write_report_script), "--daily"],
                cwd=str(self.base_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
        except Exception as e:
            error_msg = f"Не удалось запустить отчёт: {e}"
            try:
                messagebox.showerror("Ошибка", error_msg)
            except:
                print(f"❌ {error_msg}")
    
    def show_system_notification(self):
        """Системное уведомление (запасной вариант)"""
        try:
            from plyer import notification
            notification.notify(
                title="📝 Напоминание о дневном отчёте",
                message="Пора написать дневной отчёт! Нажмите на уведомление.",
                timeout=10
            )
        except:
            print("📝 Напоминание: пора написать дневной отчёт!")


def main():
    """Главная функция"""
    base_dir = Path(__file__).parent
    
    # Проверка «уже напоминали сегодня» (опционально)
    
    reminder = DailyReminder(base_dir)
    reminder.show_reminder()
    
    if TKINTER_AVAILABLE:
        root = tk.Tk()
        root.withdraw()  # скрыть главное окно
        root.mainloop()


if __name__ == "__main__":
    main()
