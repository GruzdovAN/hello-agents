<script setup lang="ts">
import { ref, watch, computed, nextTick, onMounted } from 'vue'
import { Input, Button, message, Tag } from 'ant-design-vue'
import { SendOutlined, PlusOutlined, StopOutlined, LoadingOutlined } from '@ant-design/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { sessionApi } from '@/api/session'
import { chatApi } from '@/api/chat'
import { configApi } from '@/api/config'
import { renderMarkdown, formatTime } from '@/utils/markdown'
import { getToolConfig, formatToolArgs, formatToolResult } from '@/utils/toolDisplay'
import LobsterIcon from '@/assets/lobster.svg'

// localStorage key for saving current session
const SESSION_STORAGE_KEY = 'helloclaw.lastSessionId'

// 助手名字（从后端获取）
const assistantName = ref('HelloClaw')

// 消息段类型
interface TextSegment {
  type: 'text'
  id: number
  content: string
}

interface ToolSegment {
  type: 'tool'
  id: number
  tool: string
  args: Record<string, unknown>
  result?: string
  status: 'running' | 'done' | 'error'
}

type MessageSegment = TextSegment | ToolSegment

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string  // 用于从История加载的消息
  timestamp: Date
  segments?: MessageSegment[]  // 用于流式消息的分段
}

interface MessageGroup {
  role: 'user' | 'assistant'
  messages: Message[]
}

const router = useRouter()
const route = useRoute()
const inputMessage = ref('')
const messages = ref<Message[]>([])
const loading = ref(false)
const currentSessionId = ref<string | null>(null)
const messagesContainer = ref<HTMLElement | null>(null)
const abortController = ref<AbortController | null>(null)
const initializing = ref(true)
const collapsedTools = ref<Set<number>>(new Set())
// 默认所有Инструмент都是Развернуть的（用于新建的Инструмент）
const expandedTools = ref<Set<number>>(new Set())

// 消息分组（Slack 风格）
const messageGroups = computed<MessageGroup[]>(() => {
  const groups: MessageGroup[] = []

  for (const msg of messages.value) {
    const lastGroup = groups[groups.length - 1]

    if (lastGroup && lastGroup.role === msg.role) {
      lastGroup.messages.push(msg)
    } else {
      groups.push({
        role: msg.role,
        messages: [msg]
      })
    }
  }

  return groups
})

// 是否应该显示加载指示器（底部的独立指示器）
// шт.有当助手消息组完全没有可见内容时才显示
const shouldShowLoadingIndicator = computed(() => {
  if (messages.value.length === 0) {
    return true
  }

  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg?.role !== 'assistant') {
    return true
  }

  // шт.有当完全没有可见内容时才显示底部指示器
  // 如果有Инструмент卡片等可见内容，等待Статус会在消息组内部显示
  return !hasVisibleContent(lastMsg)
})

// 检查消息组是否有可见内容
const hasGroupVisibleContent = (group: MessageGroup): boolean => {
  for (const msg of group.messages) {
    if (hasVisibleContent(msg)) {
      return true
    }
  }
  return false
}

// 检查消息组是否有Текст内容
const hasGroupTextContent = (group: MessageGroup): boolean => {
  for (const msg of group.messages) {
    if (hasTextContent(msg)) {
      return true
    }
  }
  return false
}

// 检查消息组是否有正在执行或已Готово的Инструмент（但还没有Текст回复）
const hasGroupToolWithoutText = (group: MessageGroup): boolean => {
  if (group.role !== 'assistant') return false
  let hasTool = false
  let hasText = false
  for (const msg of group.messages) {
    if (!msg.segments) continue
    for (const segment of msg.segments) {
      if (segment.type === 'tool' && !getToolConfig(segment.tool).hidden) {
        hasTool = true
      }
      if (segment.type === 'text' && segment.content && segment.content.trim()) {
        hasText = true
      }
    }
  }
  return hasTool && !hasText
}

// Сохранить当前Сессии ID 到 localStorage
const saveCurrentSession = (sessionId: string) => {
  localStorage.setItem(SESSION_STORAGE_KEY, sessionId)
}

// 从 localStorage 读取上次Сессии ID
const getLastSession = (): string | null => {
  return localStorage.getItem(SESSION_STORAGE_KEY)
}

// 加载СессииИстория（按照 OpenAI 标准格式解析）
const loadSessionHistory = async (sessionId: string) => {
  try {
    const res = await sessionApi.getHistory(sessionId)
    const rawMessages = res.messages

    // 用于存储Инструмент调用Результат（tool_call_id -> result）
    const toolResults: Map<string, string> = new Map()

    // 第一遍：收集所有 tool 消息的Результат
    for (const msg of rawMessages) {
      if (msg.role === 'tool' && msg.tool_call_id && msg.content) {
        toolResults.set(msg.tool_call_id, msg.content)
      }
    }

    // 第二遍：构建显示消息
    const displayMessages: Message[] = []
    let pendingAssistant: Message | null = null

    for (let i = 0; i < rawMessages.length; i++) {
      const msg = rawMessages[i]!

      if (msg.role === 'user') {
        // 如果有待处理的 assistant 消息，先添加
        if (pendingAssistant) {
          displayMessages.push(pendingAssistant)
          pendingAssistant = null
        }
        // 添加 user 消息
        displayMessages.push({
          id: Date.now() + i,
          role: 'user',
          content: msg.content || '',
          timestamp: new Date()
        })
      }
      else if (msg.role === 'assistant') {
        if (msg.tool_calls && msg.tool_calls.length > 0) {
          // 包含Инструмент调用的 assistant 消息
          const segments: MessageSegment[] = []

          // 添加Инструмент调用段
          msg.tool_calls.forEach((tc, tcIndex) => {
            const result = toolResults.get(tc.id)
            segments.push({
              type: 'tool',
              id: Date.now() + i * 1000 + tcIndex,
              tool: tc.function.name,
              args: JSON.parse(tc.function.arguments || '{}'),
              result: result,
              status: result?.startsWith('❌') ? 'error' : 'done'
            })
          })

          // 检查下一个消息是否是最终的 assistant 回答（没有 tool_calls）
          const nextMsg = rawMessages[i + 1]
          if (nextMsg && nextMsg.role === 'assistant' && !nextMsg.tool_calls && nextMsg.content) {
            // 有最终回答，添加Текст段
            segments.push({
              type: 'text',
              id: Date.now() + i * 1000 + 100,
              content: nextMsg.content
            })
            i++ // 跳过下一个消息
          }

          pendingAssistant = {
            id: Date.now() + i,
            role: 'assistant',
            content: '',
            timestamp: new Date(),
            segments
          }
        } else if (msg.content) {
          // 普通的 assistant Текст消息
          if (pendingAssistant) {
            // 追加到待处理的 assistant 消息
            if (!pendingAssistant.segments) {
              pendingAssistant.segments = []
            }
            pendingAssistant.segments.push({
              type: 'text',
              id: Date.now() + i,
              content: msg.content
            })
          } else {
            // 新的 assistant 消息
            displayMessages.push({
              id: Date.now() + i,
              role: 'assistant',
              content: msg.content,
              timestamp: new Date()
            })
          }
        }
      }
      // tool 消息在第一遍已经处理，跳过
    }

    // 添加最后的待处理消息
    if (pendingAssistant) {
      displayMessages.push(pendingAssistant)
    }

    messages.value = displayMessages
    await scrollToBottom()
  } catch (error) {
    // Сессии不存在或Ошибка загрузки，Очистить消息
    messages.value = []
  }
}

// ИнициализацияСессии
const initSession = async () => {
  // 获取助手名字
  try {
    const agentInfo = await configApi.getAgentInfo()
    if (agentInfo.name) {
      assistantName.value = agentInfo.name
    }
  } catch (error) {
    // 获取Ошибка时Используется默认名字
    console.warn('获取助手名字Ошибка:', error)
  }

  const urlSession = route.query.session as string | undefined

  if (urlSession) {
    // URL 中有 session 参数，Используется它
    currentSessionId.value = urlSession
    saveCurrentSession(urlSession)
    await loadSessionHistory(urlSession)
    initializing.value = false
  } else {
    // URL 中没有 session 参数，尝试从 localStorage 读取
    const lastSession = getLastSession()
    if (lastSession) {
      // 有上次Сессии，设置 session 并加载История，然后更新 URL
      currentSessionId.value = lastSession
      saveCurrentSession(lastSession)
      await loadSessionHistory(lastSession)
      // Используется replace 更新 URL（不触发导航）
      window.history.replaceState({}, '', `/?session=${lastSession}`)
      initializing.value = false
    } else {
      // 没有上次Сессии，创建新Сессии
      try {
        const res = await sessionApi.create()
        saveCurrentSession(res.session_id)
        currentSessionId.value = res.session_id
        // Используется replace 更新 URL（不触发导航）
        window.history.replaceState({}, '', `/?session=${res.session_id}`)
        initializing.value = false
      } catch (error) {
        message.error('Не удалось создать сессию')
        initializing.value = false
      }
    }
  }
}

// 监听 session 参数变化（处理从Другое地方跳转过来的情况）
watch(
  () => route.query.session,
  async (newSession, oldSession) => {
    // 如果正在Инициализация，跳过
    if (initializing.value) return

    // 如果 session 没有实际变化，跳过
    if (newSession === oldSession) return

    const sessionId = (newSession as string) || null

    // 如果新 session 为空，不做处理（应该由 initSession 处理）
    if (!sessionId) return

    // 切换到新Сессии
    currentSessionId.value = sessionId
    saveCurrentSession(sessionId)
    inputMessage.value = ''
    await loadSessionHistory(sessionId)
  }
)

// 监听 refresh 参数变化（处理从Настройки页面Инициализация后跳转的情况）
watch(
  () => route.query.refresh,
  async (newRefresh) => {
    if (newRefresh) {
      // 重新获取助手名字
      try {
        const agentInfo = await configApi.getAgentInfo()
        if (agentInfo.name) {
          assistantName.value = agentInfo.name
        }
      } catch (error) {
        console.warn('获取助手名字Ошибка:', error)
      }

      // Очистить URL 中的 refresh 参数
      const currentQuery = { ...route.query }
      delete currentQuery.refresh
      router.replace({ query: currentQuery })
    }
  }
)

// 组件挂载时ИнициализацияСессии
onMounted(async () => {
  await initSession()
})

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 切换Инструмент折叠Статус
const toggleToolCollapse = (toolId: number) => {
  if (expandedTools.value.has(toolId)) {
    expandedTools.value.delete(toolId)
  } else {
    expandedTools.value.add(toolId)
  }
}

// 检查Инструмент是否Развернуть（默认折叠，只有点击后才Развернуть）
const isToolExpanded = (toolId: number): boolean => {
  return expandedTools.value.has(toolId)
}

// 检查消息是否有可见内容
const hasVisibleContent = (msg: Message): boolean => {
  if (!msg.segments || msg.segments.length === 0) {
    // 没有分段，检查普通内容
    return !!msg.content
  }

  // 有分段，检查是否有可见的段
  for (const segment of msg.segments) {
    if (segment.type === 'text' && segment.content) {
      return true
    }
    if (segment.type === 'tool' && !getToolConfig(segment.tool).hidden) {
      return true
    }
  }
  return false
}

// 检查消息是否有Текст内容（用于决定是否显示加载指示器）
const hasTextContent = (msg: Message): boolean => {
  if (!msg.segments || msg.segments.length === 0) {
    return !!msg.content
  }
  // шт.检查Текст段
  for (const segment of msg.segments) {
    if (segment.type === 'text' && segment.content) {
      return true
    }
  }
  return false
}

// 检查消息是否有可见的Инструмент调用（用于决定是否显示Инструмент卡片而非加载指示器）
const hasVisibleTools = (msg: Message): boolean => {
  if (!msg.segments) return false
  for (const segment of msg.segments) {
    if (segment.type === 'tool' && !getToolConfig(segment.tool).hidden) {
      return true
    }
  }
  return false
}

// 检查消息组是否正在等待响应（用于隐藏 group-footer）
const isGroupWaiting = (group: MessageGroup): boolean => {
  if (group.role !== 'assistant' || !loading.value) return false
  // 检查组内所有消息是否都没有Текст内容
  return group.messages.every(msg => !hasTextContent(msg))
}

// Остановить генерацию
const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
    loading.value = false
  }
}

// 更新消息段（触发 Vue 响应性）
const updateMessageSegments = (msgIndex: number, segments: MessageSegment[]) => {
  if (msgIndex >= 0 && msgIndex < messages.value.length) {
    const existingMsg = messages.value[msgIndex]!
    messages.value[msgIndex] = {
      id: existingMsg.id,
      role: existingMsg.role,
      content: existingMsg.content,
      timestamp: existingMsg.timestamp,
      segments: [...segments]
    }
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  const userMessage = inputMessage.value
  const userMsg: Message = {
    id: Date.now(),
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  }

  messages.value.push(userMsg)
  inputMessage.value = ''
  loading.value = true

  // 创建 AbortController
  abortController.value = new AbortController()

  // 助手消息的索引和段
  let assistantMsgIndex = -1
  let currentSegments: MessageSegment[] = []
  let currentTextSegmentId = -1

  await scrollToBottom()

  try {
    await chatApi.sendMessageStream(
      userMessage,
      currentSessionId.value || undefined,
      (event) => {
        if (event.type === 'session') {
          // 收到Сессии ID
          if (event.session_id) {
            currentSessionId.value = event.session_id
            saveCurrentSession(event.session_id)
          }
        } else if (event.type === 'step_start') {
          // 新步骤开始 - 创建新的Текст段
          currentTextSegmentId = Date.now()
          currentSegments.push({
            type: 'text',
            id: currentTextSegmentId,
            content: ''
          })

          // 如果还没有助手消息，创建一个
          if (assistantMsgIndex === -1) {
            assistantMsgIndex = messages.value.length
            messages.value.push({
              id: Date.now(),
              role: 'assistant',
              content: '',
              timestamp: new Date(),
              segments: currentSegments
            })
          } else {
            updateMessageSegments(assistantMsgIndex, currentSegments)
          }
          scrollToBottom()
        } else if (event.type === 'chunk' && event.content) {
          // 更新当前Текст段
          const textSegment = currentSegments.find(s => s.type === 'text' && s.id === currentTextSegmentId) as TextSegment | undefined
          if (textSegment) {
            textSegment.content += event.content
            updateMessageSegments(assistantMsgIndex, currentSegments)
          }
          scrollToBottom()
        } else if (event.type === 'tool_start') {
          // Инструмент调用开始 - 创建Инструмент段
          currentSegments.push({
            type: 'tool',
            id: Date.now(),
            tool: event.tool || '',
            args: event.args || {},
            status: 'running'
          })

          // 如果还没有助手消息，创建一个
          if (assistantMsgIndex === -1) {
            assistantMsgIndex = messages.value.length
            messages.value.push({
              id: Date.now(),
              role: 'assistant',
              content: '',
              timestamp: new Date(),
              segments: currentSegments
            })
          } else {
            updateMessageSegments(assistantMsgIndex, currentSegments)
          }
          scrollToBottom()
        } else if (event.type === 'tool_finish') {
          // Инструмент调用结束 - 查找或创建Инструмент段
          const lastToolSegment = [...currentSegments].reverse().find(s => s.type === 'tool' && s.status === 'running') as ToolSegment | undefined
          if (lastToolSegment) {
            // 更新现有的运行中Инструмент
            lastToolSegment.result = event.result
            lastToolSegment.status = 'done'
          } else {
            // 没有对应的 tool_start，直接添加为Готово的Инструмент
            currentSegments.push({
              type: 'tool',
              id: Date.now(),
              tool: event.tool || '',
              args: {},
              result: event.result,
              status: 'done'
            })
          }
          updateMessageSegments(assistantMsgIndex, currentSegments)
          scrollToBottom()
        } else if (event.type === 'done') {
          // Готово
          if (event.session_id) {
            currentSessionId.value = event.session_id
          }
          // 对话结束后重新获取助手名字（可能在对话中更新了 IDENTITY.md）
          configApi.getAgentInfo().then(agentInfo => {
            if (agentInfo.name) {
              assistantName.value = agentInfo.name
            }
          }).catch(() => {
            // 忽略错误，保持当前名字
          })
        } else if (event.type === 'error') {
          message.error(event.error || 'Не удалось отправить сообщение')
        }
      },
      abortController.value.signal
    )

    await scrollToBottom()
  } catch (error: unknown) {
    // 如果是用户主动Отмена，不显示错误
    if (error instanceof Error && error.name === 'AbortError') {
      console.log('用户Отмена了请求')
      // Отмена时保留已生成的内容
    } else {
      console.error('Не удалось отправить сообщение:', error)
      message.error('Не удалось отправить сообщение')
      // 移除用户消息
      messages.value.pop()
    }
  } finally {
    loading.value = false
    abortController.value = null
  }
}

const createNewSession = async () => {
  try {
    const res = await sessionApi.create()
    saveCurrentSession(res.session_id)
    router.push({ name: 'chat', query: { session: res.session_id } })
  } catch (error) {
    message.error('Не удалось создать сессию')
  }
}
</script>

<template>
  <div class="chat-view">
    <!-- 消息区域 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- Инициализация加载Статус -->
      <div v-if="initializing" class="empty-state">
        <img :src="LobsterIcon" alt="HelloClaw" class="empty-icon loading" />
        <p class="empty-hint">Загрузка...</p>
      </div>
      <template v-else-if="messages.length > 0">
        <div
          v-for="(group, groupIndex) in messageGroups"
          :key="groupIndex"
          v-show="group.role !== 'assistant' || hasGroupVisibleContent(group)"
          :class="['message-group', group.role]"
        >
          <!-- 头像 -->
          <div class="group-avatar">
            <img v-if="group.role === 'assistant'" :src="LobsterIcon" alt="HelloClaw" />
            <div v-else class="user-avatar">Вы</div>
          </div>

          <!-- 消息内容 -->
          <div class="group-content">
            <!-- 遍历每条消息 -->
            <template v-for="(msg, msgIndex) in group.messages" :key="msg.id">
              <!-- 如果有分段，按分段显示 -->
              <template v-if="msg.segments && msg.segments.length > 0">
                <template v-for="segment in msg.segments" :key="segment.id">
                  <!-- Текст段 -->
                  <div v-if="segment.type === 'text' && segment.content" class="message-bubble">
                    <div
                      class="message-text"
                      v-html="renderMarkdown(segment.content)"
                    ></div>
                  </div>
                  <!-- Инструмент调用段 - шт.显示非隐藏的Инструмент -->
                  <div
                    v-if="segment.type === 'tool' && !getToolConfig(segment.tool).hidden"
                    :class="['tool-card', segment.status]"
                  >
                    <div
                      class="tool-header"
                      @click="segment.status !== 'running' && toggleToolCollapse(segment.id)"
                    >
                      <span class="tool-icon">{{ getToolConfig(segment.tool).icon }}</span>
                      <span class="tool-name">
                        <template v-if="!isToolExpanded(segment.id)">Использован</template>
                        {{ getToolConfig(segment.tool).name }}
                      </span>
                      <Tag v-if="segment.status === 'running'" color="processing" class="tool-tag">
                        <LoadingOutlined /> Выполняется
                      </Tag>
                      <Tag v-else-if="segment.status === 'done'" color="success" class="tool-tag">Готово</Tag>
                      <Tag v-else-if="segment.status === 'error'" color="error" class="tool-tag">Ошибка</Tag>
                      <span
                        v-if="segment.status !== 'running'"
                        class="collapse-indicator"
                      >
                        {{ isToolExpanded(segment.id) ? '▼' : '▶' }}
                      </span>
                    </div>
                    <!-- Развернуть后显示Входные данные和Результат -->
                    <div v-if="isToolExpanded(segment.id)" class="tool-details">
                      <!-- Входные данные -->
                      <div v-if="segment.args && Object.keys(segment.args).length > 0" class="tool-args">
                        <div class="tool-detail-label">Входные данные</div>
                        <pre class="tool-detail-content">{{ formatToolArgs(segment.args) }}</pre>
                      </div>
                      <!-- Результат -->
                      <div v-if="segment.result" class="tool-result-wrapper">
                        <div class="tool-detail-label">Результат</div>
                        <pre class="tool-detail-content">{{ formatToolResult(segment.result) }}</pre>
                      </div>
                    </div>
                  </div>
                </template>
              </template>
              <!-- 如果没有分段，显示普通内容（История消息） -->
              <div v-else-if="msg.content" class="message-bubble">
                <div
                  class="message-text"
                  v-html="renderMarkdown(msg.content)"
                ></div>
              </div>
            </template>

            <!-- 消息组内部的等待Статус（有Инструмент调用但没有Текст回复时） -->
            <div v-if="loading && hasGroupToolWithoutText(group)" class="message-bubble">
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>

            <!-- 组底部：Название和Время（加载等待时隐藏） -->
            <div v-if="!isGroupWaiting(group)" class="group-footer">
              <span class="group-name">{{ group.role === 'user' ? 'Вы' : assistantName }}</span>
              <span class="group-time">{{ formatTime(group.messages[group.messages.length - 1]?.timestamp || new Date()) }}</span>
            </div>
          </div>
        </div>
      </template>

      <!-- 空Статус -->
      <div v-else class="empty-state">
        <img :src="LobsterIcon" alt="HelloClaw" class="empty-icon" />
        <p class="empty-hint">Отправьте сообщение, чтобы начать диалог</p>
      </div>

      <!-- 加载指示器（助手消息组样式）- 等待响应时显示 -->
      <div v-if="loading && shouldShowLoadingIndicator" class="message-group assistant loading-group">
        <div class="group-avatar">
          <img :src="LobsterIcon" alt="HelloClaw" />
        </div>
        <div class="group-content">
          <div class="message-bubble">
            <div class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-wrapper">
      <div class="chat-input">
        <!-- 输入框 -->
        <Input.TextArea
          v-model:value="inputMessage"
          placeholder="Введите сообщение... (Enter — отправить, Shift+Enter — новая строка)"
          :auto-size="{ minRows: 1, maxRows: 4 }"
          @press-enter="(e: KeyboardEvent) => { if (!e.shiftKey) { e.preventDefault(); sendMessage() } }"
        />
        <!-- 按钮区域（固定宽度） -->
        <div class="input-actions">
          <!-- Новая сессия按钮 -->
          <Button
            class="icon-btn"
            @click="createNewSession"
            title="Новая сессия"
          >
            <template #icon>
              <PlusOutlined />
            </template>
          </Button>
          <!-- Стоп按钮（loading 时显示） -->
          <button
            v-if="loading"
            class="stop-btn"
            @click="stopGeneration"
            title="Остановить генерацию"
          >
            <div class="stop-icon"></div>
          </button>
          <!-- Отправить按钮（有文字时显示） -->
          <button
            v-else-if="inputMessage.trim()"
            class="send-btn active"
            @click="sendMessage"
            title="Отправить"
          >
            <SendOutlined />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  box-sizing: border-box;
  background-color: var(--color-background);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 消息组样式 */
.message-group {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message-group.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-group.assistant {
  align-self: flex-start;
}

/* 头像 */
.group-avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
}

.group-avatar img {
  width: 36px;
  height: 36px;
  border-radius: 8px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background-color: var(--color-primary);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 消息组内容 */
.group-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

/* 消息气泡 */
.message-bubble {
  display: inline-block;
  max-width: 100%;
}

.message-text {
  padding: 10px 14px;
  border-radius: 12px;
  background-color: var(--color-surface);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  line-height: 1.6;
  word-wrap: break-word;
}

.message-group.user .message-text {
  background-color: var(--color-primary-light);
  border: 1px solid rgba(255, 92, 92, 0.2);
}

/* Markdown 样式 */
.message-text :deep(p) {
  margin: 0;
}

.message-text :deep(p + p) {
  margin-top: 8px;
}

.message-text :deep(code) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.message-text :deep(pre) {
  background-color: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) {
  background-color: transparent;
  padding: 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--color-text-secondary);
}

.message-text :deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
}

/* 组底部 */
.group-footer {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 4px;
  padding-left: 4px;
}

.group-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
}

.group-time {
  font-size: 11px;
  color: var(--color-text-secondary);
}

/* 空Статус */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.empty-icon {
  width: 100px;
  height: 100px;
  opacity: 0.5;
}

.empty-icon.loading {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(0.95);
  }
  50% {
    opacity: 0.6;
    transform: scale(1);
  }
}

.empty-hint {
  color: var(--color-text-secondary);
  font-size: 14px;
}

/* 加载指示器 */
.loading-group .message-bubble,
.message-bubble:has(.loading-dots) {
  padding: 14px 12px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.loading-dots {
  display: flex;
  gap: 4px;
  align-items: center;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--color-primary);
  animation: loading-pulse 1.4s ease-in-out infinite;
}

.loading-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.loading-dots span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes loading-pulse {
  0%, 100% {
    opacity: 0.4;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1);
  }
}

/* 输入区域 */
.chat-input-wrapper {
  padding: 16px 24px 32px;
  background-color: var(--color-surface);
  border-top: 1px solid var(--color-border);
}

.chat-input {
  display: flex;
  gap: 12px;
  align-items: center;
  max-width: 800px;
  margin: 0 auto;
}

.chat-input :deep(.ant-input) {
  flex: 1;
  border-radius: 16px;
  padding: 10px 16px;
  resize: none;
}

/* 按钮区域（固定宽度，防止输入框抖动） */
.input-actions {
  flex-shrink: 0;
  display: flex;
  gap: 12px;
  align-items: center;
  width: 92px;
}

/* Новая сессия按钮 */
.input-actions .icon-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
}

.input-actions .icon-btn:hover {
  background: var(--color-primary-light);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

/* Отправить按钮 - 白底 + 黑色图标，输入后红底 + 白色图标 */
.input-actions .send-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #333;
}

.input-actions .send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

/* 输入文字后：红底 + 白色图标 */
.input-actions .send-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.input-actions .send-btn.active:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

/* Стоп按钮 - 红底 + 白色圆角方块图标 */
.input-actions .stop-btn {
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 8px;
  background: var(--color-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.input-actions .stop-btn:hover {
  background: var(--color-primary-hover);
}

.stop-icon {
  width: 14px;
  height: 14px;
  background: #fff;
  border-radius: 3px;
}

/* Инструмент调用卡片 */
.tool-calls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.tool-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  transition: all 0.2s ease;
}

/* ВыполняетсяСтатус - 龙虾红主题 */
.tool-card.running {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
}

.tool-card.running .tool-icon,
.tool-card.running .tool-name {
  color: var(--color-primary);
}

/* ГотовоСтатус - 灰色调 */
.tool-card.done {
  border-color: var(--color-border);
  background: var(--color-surface);
}

/* ОшибкаСтатус - 红色调 */
.tool-card.error {
  border-color: var(--color-primary);
  background: #fff1f0;
}

.tool-card.error .tool-icon,
.tool-card.error .tool-name {
  color: var(--color-primary);
}

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.tool-header:hover {
  opacity: 0.8;
}

.tool-icon {
  font-size: 14px;
  line-height: 1;
}

.tool-name {
  font-weight: 500;
  color: var(--color-text);
  flex: 1;
}

.tool-tag {
  font-size: 11px;
  padding: 0 6px;
  line-height: 18px;
  border-radius: 4px;
}

.collapse-indicator {
  font-size: 10px;
  color: var(--color-text-secondary);
  margin-left: auto;
  transition: transform 0.2s ease;
}

/* Инструмент详情区域 */
.tool-details {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--color-border);
}

.tool-args,
.tool-result-wrapper {
  margin-bottom: 8px;
}

.tool-result-wrapper:last-child {
  margin-bottom: 0;
}

.tool-detail-label {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-bottom: 4px;
  font-weight: 500;
}

.tool-detail-content {
  margin: 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-text);
  max-height: 150px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-monospace, 'SF Mono', Monaco, 'Andale Mono', monospace;
}

.step-info {
  color: var(--color-text-secondary);
  font-size: 11px;
}
</style>
