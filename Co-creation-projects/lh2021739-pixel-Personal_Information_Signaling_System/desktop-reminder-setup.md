# Настройка напоминания на рабочем столе через Планировщик заданий Windows

## Описание функции

Настройка Планировщика заданий Windows для ежедневного всплывающего окна в 23:30 с напоминанием написать ежедневный отчёт.

## 📋 Рекомендуемые варианты конфигурации

### Вариант 1: Виртуальное окружение проекта (рекомендуется)

Если у проекта есть собственное виртуальное окружение (каталог `.venv`):

**Параметры:**

- **Программа или сценарий**: 
  ```
  C:\Python\pythonprogram\Personal_Information_Signaling_System\.venv\Scripts\python.exe
  ```

- **Добавить аргументы (необязательно)**: 
  ```
  daily_reminder.py
  ```

- **Рабочая папка (необязательно)**: 
  ```
  C:\Python\pythonprogram\Personal_Information_Signaling_System
  ```

### Вариант 2: Системный Python

Если используется системный Python (добавлен в PATH):

**Параметры:**

- **Программа или сценарий**: 
  ```
  python.exe
  ```

- **Добавить аргументы (необязательно)**: 
  ```
  daily_reminder.py
  ```

- **Рабочая папка (необязательно)**: 
  ```
  C:\Python\pythonprogram\Personal_Information_Signaling_System
  ```

### Вариант 3: Прямой запуск скрипта (при настроенной ассоциации файлов)

**Параметры:**

- **Программа или сценарий**: 
  ```
  C:\Python\pythonprogram\Personal_Information_Signaling_System\daily_reminder.py
  ```

- **Рабочая папка (необязательно)**: 
  ```
  C:\Python\pythonprogram\Personal_Information_Signaling_System
  ```

## 🔍 Как определить путь к Python

### Способ 1: Проверка виртуального окружения проекта

```bash
cd C:\Python\pythonprogram\Personal_Information_Signaling_System
dir .venv\Scripts\python.exe
```

Если файл есть, используйте:
```
C:\Python\pythonprogram\Personal_Information_Signaling_System\.venv\Scripts\python.exe
```

### Способ 2: Проверка системного Python

В командной строке:
```bash
where python
```

Будет показан полный путь, например:
```
C:\Python\python311\python.exe
```

### Способ 3: Создание виртуального окружения (если ещё нет)

```bash
cd C:\Python\pythonprogram\Personal_Information_Signaling_System
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Затем используйте конфигурацию варианта 1.

## Шаги настройки

### 1. Открыть Планировщик заданий

- `Win + R` → введите `taskschd.msc` → Enter
- Или: меню «Пуск» → поиск «Планировщик заданий»

### 2. Создать простую задачу

1. В панели «Действия» справа нажмите «Создать простую задачу»
2. Имя: `每日写日报提醒`
3. Описание: `每天23:30提醒写日报`
4. «Далее»

### 3. Настроить триггер

1. Выберите «Ежедневно»
2. «Далее»
3. Время начала: `23:30:00`
4. Дата начала: сегодня или завтра
5. «Далее»

### 4. Настроить действие

1. Выберите «Запуск программы»
2. «Далее»
3. В «Программа или сценарий» укажите полный путь к Python:
   ```
   C:\Python\pythonprogram\Personal_Information_Signaling_System\.venv\Scripts\python.exe
   ```
   (если есть виртуальное окружение проекта)
   
   Или системный Python:
   ```
   python.exe
   ```
   (Python должен быть в системном PATH)

4. В «Добавить аргументы»:
   ```
   daily_reminder.py
   ```

5. В «Рабочая папка»:
   ```
   C:\Python\pythonprogram\Personal_Information_Signaling_System
   ```
   (измените на ваш фактический путь)

6. «Далее»

### 5. Завершить настройку

1. Отметьте «Открыть свойства этой задачи при нажатии кнопки «Готово»»
2. «Готово»

### 6. Дополнительные настройки (опционально)

В окне свойств задачи:

1. Вкладка **Общие**:
   - «Выполнять вне зависимости от регистрации пользователя» (опционально)
   - «Выполнять с наивысшими правами» (опционально)

2. Вкладка **Условия**:
   - Снимите «Запускать только при питании от электросети» (для ноутбука)
   - «Пробуждать компьютер для выполнения задачи» (опционально)

3. Вкладка **Параметры**:
   - «Разрешить выполнение задачи по требованию»
   - «Если задача уже выполняется, остановить существующий экземпляр»

4. «ОК» для сохранения

## Тестирование задачи

### Способ 1: Немедленный запуск

1. Найдите задачу в Планировщике заданий
2. ПКМ → «Выполнить»
3. Проверьте, появилось ли окно напоминания

### Способ 2: Изменение времени для теста

1. ПКМ по задаче → «Свойства»
2. Вкладка «Триггеры» → измените триггер
3. Установите время на текущее + 1 минута
4. Подождите минуту и проверьте окно
5. После теста верните время 23:30

## Частые проблемы

### 1. Задача не выполняется

- Проверьте путь к Python
- Проверьте путь к скрипту
- Проверьте рабочую папку («Начать в»)
- Посмотрите ошибки в журнале задачи

### 2. Окно не отображается

- Установлен ли Pillow: `pip install Pillow`
- Есть ли файл изображения: `assets/person.png`
- Есть ли сообщения об ошибках

### 3. После клика не открывается написание отчёта

- Существует ли `write_report.py`
- Корректно ли настроено окружение Python

## Автозапуск при включении ПК (опционально)

Для фонового сервиса напоминаний при загрузке:

1. Создайте `start_reminder_service.bat`:
   ```batch
   @echo off
   cd /d C:\Python\pythonprogram\Personal_Information_Signaling_System
   C:\Python\pythonprogram\Personal_Information_Signaling_System\.venv\Scripts\python.exe daily_reminder_service.py
   ```

2. Добавьте в папку автозагрузки:
   - `Win + R` → `shell:startup`
   - Поместите ярлык `start_reminder_service.bat` в эту папку

## Примечания

1. **Путь к Python**: используйте Python из venv или полный путь
2. **Рабочая папка**: должна быть указана верно
3. **Права**: может потребоваться запуск Планировщика от администратора
4. **Изображение**: должен существовать `assets/person.png` или `assets/person.jpg`

## Удаление

1. Откройте Планировщик заданий
2. Найдите задачу «每日写日报提醒»
3. ПКМ → «Удалить»

---

## 📝 Обновление существующей задачи (если путь проекта изменился)

Если напоминание уже было настроено, но путь к проекту изменился:

### Что обновить

#### Старая конфигурация

- **Программа или сценарий**: `C:\Python\pythonprogram\datawhale_Agent\PersonalizationMCP-main\daily_reminder.py`
- **Рабочая папка**: `C:\Python\pythonprogram\datawhale_Agent\PersonalizationMCP-main`
- **Python**: например `C:\Python\pythonprogram\datawhale_Agent\.venv\Scripts\python.exe`

#### Новая конфигурация

- **Программа или сценарий**: `C:\Python\pythonprogram\Personal_Information_Signaling_System\daily_reminder.py`
- **Рабочая папка**: `C:\Python\pythonprogram\Personal_Information_Signaling_System`
- **Python**: 
  - venv проекта: `C:\Python\pythonprogram\Personal_Information_Signaling_System\.venv\Scripts\python.exe`
  - системный: `python.exe` (если в PATH)

### Подробные шаги обновления

#### Шаг 1: Открыть Планировщик заданий

1. `Win + R` → `taskschd.msc` → Enter
2. Или: «Пуск» → «Планировщик заданий»

#### Шаг 2: Найти задачу

Имя может быть:
- `每日写日报提醒`
- `Daily Report Reminder`
- `写日报提醒`
- или ваше пользовательское имя

#### Шаг 3: Свойства задачи

ПКМ → «Свойства» (или двойной щелчок) → вкладка **«Действия»**

#### Шаг 4: Обновить действие

1. **Программа или сценарий**:
   ```
   Старое: C:\Python\pythonprogram\datawhale_Agent\PersonalizationMCP-main\daily_reminder.py
   Новое: C:\Python\pythonprogram\Personal_Information_Signaling_System\daily_reminder.py
   ```
   
   Или при запуске через интерпретатор:
   ```
   Старое: C:\Python\pythonprogram\datawhale_Agent\.venv\Scripts\python.exe
   Новое: C:\Python\pythonprogram\Personal_Information_Signaling_System\.venv\Scripts\python.exe
   ```

2. **Добавить аргументы** (если в поле «Программа» указан python.exe):
   ```
   daily_reminder.py
   ```

3. **Рабочая папка**:
   ```
   Старое: C:\Python\pythonprogram\datawhale_Agent\PersonalizationMCP-main
   Новое: C:\Python\pythonprogram\Personal_Information_Signaling_System
   ```

#### Шаг 5: Сохранить

«ОК» — при необходимости введите пароль администратора.

#### Шаг 6: Тест

ПКМ → «Выполнить». При ошибке смотрите вкладку «Журнал».

### Обновление через командную строку (продвинутый уровень)

```powershell
# 1. Список задач
Get-ScheduledTask | Where-Object {$_.TaskName -like "*日报*" -or $_.TaskName -like "*reminder*"}

# 2. Текущее действие
$task = Get-ScheduledTask -TaskName "你的任务名称"
$task.Actions

# 3. Обновление (нужны права администратора)
$action = New-ScheduledTaskAction -Execute "C:\Python\pythonprogram\Personal_Information_Signaling_System\daily_reminder.py" -WorkingDirectory "C:\Python\pythonprogram\Personal_Information_Signaling_System"
Set-ScheduledTask -TaskName "你的任务名称" -Action $action
```

---

## ✅ Контрольный список

После настройки или обновления проверьте:

- [ ] Путь **Программа или сценарий** существует
- [ ] **Рабочая папка** существует
- [ ] **Аргументы** верны (при запуске через python.exe)
- [ ] **Триггер** настроен (обычно ежедневно 23:30)
- [ ] **Тестовый запуск** успешен (ПКМ → Выполнить)

---

## 🎯 Быстрое копирование

### Вариант 1 (venv проекта)

```
Программа или сценарий: C:\Python\pythonprogram\Personal_Information_Signaling_System\.venv\Scripts\python.exe
Аргументы: daily_reminder.py
Рабочая папка: C:\Python\pythonprogram\Personal_Information_Signaling_System
```

### Вариант 2 (системный Python)

```
Программа или сценарий: python.exe
Аргументы: daily_reminder.py
Рабочая папка: C:\Python\pythonprogram\Personal_Information_Signaling_System
```
