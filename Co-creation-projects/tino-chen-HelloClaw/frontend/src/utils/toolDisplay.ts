// Инструмент显示Настройки
export interface ToolDisplayConfig {
  name: string         // 友好Название
  icon: string         // emoji 图标
  hidden?: boolean     // 是否隐藏
}

export const TOOL_DISPLAY_CONFIG: Record<string, ToolDisplayConfig> = {
  // 内置Инструмент - 隐藏
  Thought: { name: 'Размышление', icon: '💭', hidden: true },
  Finish: { name: 'Готово', icon: '✅', hidden: true },

  // 文件ДействиеИнструмент（HelloAgents 内置）
  Read: { name: 'Чтение файла', icon: '📄' },
  Write: { name: 'Запись файла', icon: '✏️' },
  Edit: { name: 'Редактирование файла', icon: '📝' },
  MultiEdit: { name: 'Массовое редактирование', icon: '📝' },

  // 计算Инструмент
  python_calculator: { name: 'Калькулятор', icon: '🔢' },

  // ПамятьИнструмент（HelloClaw 自定义）
  memory: { name: 'Операции с памятью', icon: '🧠' },
  memory_search: { name: 'Поиск в памяти', icon: '🔍' },
  memory_get: { name: 'Чтение памяти', icon: '📖' },
  memory_add: { name: 'Добавление в память', icon: '📝' },
  memory_update_longterm: { name: 'Обновление долгосрочной памяти', icon: '📚' },
  memory_list: { name: 'Список файлов памяти', icon: '📋' },
  memory_cleanup: { name: 'Очистка устаревшей памяти', icon: '🧹' },

  // 任务Инструмент
  Task: { name: 'Подзадача', icon: '📋' },

  // Команда执行Инструмент
  execute_command: { name: 'Выполнение команды', icon: '💻' },
  exec_run: { name: 'Выполнение команды', icon: '💻' },
  exec_allowed_commands: { name: 'Разрешённые команды', icon: '📋' },
  exec_dangerous_patterns: { name: 'Опасные команды', icon: '⚠️' },

  // 网络Инструмент
  web_search: { name: 'Веб-поиск', icon: '🌐' },
  search_web: { name: 'Веб-поиск', icon: '🌐' },
  web_fetch: { name: 'Загрузка страницы', icon: '📡' },
  fetch_url: { name: 'Загрузка страницы', icon: '📡' },
}

// 默认Настройки（неизвестноИнструмент）
export const DEFAULT_TOOL_CONFIG: ToolDisplayConfig = {
  name: 'Инструмент',
  icon: '🔧',
}

// 获取Инструмент显示Настройки
export function getToolConfig(toolName: string): ToolDisplayConfig {
  return TOOL_DISPLAY_CONFIG[toolName] || DEFAULT_TOOL_CONFIG
}

// 格式化Инструмент参数显示
export function formatToolArgs(args: Record<string, unknown>): string {
  if (!args || Object.keys(args).length === 0) {
    return ''
  }

  const parts: string[] = []
  for (const [key, value] of Object.entries(args)) {
    let displayValue: string
    if (typeof value === 'string') {
      // 截断长字符串
      displayValue = value.length > 100 ? value.slice(0, 100) + '...' : value
    } else if (typeof value === 'object') {
      displayValue = JSON.stringify(value)
      if (displayValue.length > 100) {
        displayValue = displayValue.slice(0, 100) + '...'
      }
    } else {
      displayValue = String(value)
    }
    parts.push(`${key}: ${displayValue}`)
  }
  return parts.join('\n')
}

// 格式化ИнструментРезультат显示
export function formatToolResult(result: string | undefined): string {
  if (!result) return ''
  // 截断长Результат
  return result.length > 500 ? result.slice(0, 500) + '...' : result
}
