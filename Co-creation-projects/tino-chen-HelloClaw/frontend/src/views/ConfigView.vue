<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Card, List, Input, Button, message, Empty, Tag, Modal, Checkbox } from 'ant-design-vue'
import { configApi, type ConfigFile } from '@/api/config'
import { SaveOutlined, FileTextOutlined, ReloadOutlined } from '@ant-design/icons-vue'

const router = useRouter()

const configs = ref<string[]>([])
const selectedConfig = ref<ConfigFile | null>(null)
const editingContent = ref('')
const loading = ref(false)
const saving = ref(false)
const resetting = ref(false)
const showResetModal = ref(false)
const resetOptions = ref({
  reset_sessions: true,
  reset_memory: true,
  reset_global_config: false,
})

const configDescriptions: Record<string, string> = {
  CONFIG: 'Глобальные настройки',
  IDENTITY: 'Определение личности',
  USER: 'Данные пользователя',
  SOUL: 'Шаблон характера',
  MEMORY: 'Долгосрочная память',
  AGENTS: 'Правила рабочего пространства',
  HEARTBEAT: 'Задачи heartbeat',
  BOOTSTRAP: 'Начальная настройка',
}

// 获取Файлы конфигурации的后缀
const getConfigExtension = (name: string): string => {
  return name === 'CONFIG' ? '.json' : '.md'
}

const loadConfigs = async () => {
  loading.value = true
  try {
    const res = await configApi.list()
    configs.value = res.configs
  } catch (error) {
    message.error('Не удалось загрузить список настроек')
  } finally {
    loading.value = false
  }
}

const selectConfig = async (name: string) => {
  try {
    const res = await configApi.get(name)
    selectedConfig.value = res
    editingContent.value = res.content
  } catch (error) {
    message.error('Не удалось загрузить настройки')
  }
}

const saveConfig = async () => {
  if (!selectedConfig.value) return

  saving.value = true
  try {
    await configApi.update(selectedConfig.value.name, editingContent.value)
    message.success('Сохранено')
  } catch (error: any) {
    // 透传后端Сообщение об ошибке
    const errorMsg = error?.response?.data?.detail || error?.message || 'Не удалось сохранить'
    message.error(errorMsg)
  } finally {
    saving.value = false
  }
}

const confirmReset = () => {
  // 重置选项为默认值
  resetOptions.value = {
    reset_sessions: true,
    reset_memory: true,
    reset_global_config: false,
  }
  showResetModal.value = true
}

const handleReset = async () => {
  resetting.value = true
  try {
    const res = await configApi.reset(resetOptions.value)
    message.success(res.message)
    showResetModal.value = false
    selectedConfig.value = null
    editingContent.value = ''

    // 如果Очистить了СессииИстория，也要Очистить localStorage 中的上次Сессии ID
    if (resetOptions.value.reset_sessions) {
      localStorage.removeItem('helloclaw.lastSessionId')
    }

    await loadConfigs()

    // 导航到Чат页面并传递Обновить参数，让 ChatView 重新获取 agent 信息
    router.push({ name: 'chat', query: { refresh: Date.now().toString() } })
  } catch (error) {
    message.error('重置Ошибка')
  } finally {
    resetting.value = false
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<template>
  <div class="config-view">
    <div class="config-header">
      <h1>Управление настройками</h1>
      <p>Управление конфигурацией и идентичностью агента</p>
    </div>

    <div class="config-content">
      <!-- Настройки列表 -->
      <div class="config-list">
        <Card :loading="loading" class="list-card">
          <template #title>
            <FileTextOutlined /> Файлы конфигурации
          </template>
          <template #extra>
            <button
              class="reset-btn"
              @click="confirmReset"
              title="Сбросить к шаблону"
            >
              <ReloadOutlined /> Инициализация
            </button>
          </template>
          <List :data-source="configs" :locale="{ emptyText: 'Нет файлов конфигурации' }">
            <template #renderItem="{ item }">
              <List.Item
                @click="selectConfig(item)"
                :class="['config-item', { active: selectedConfig?.name === item }]"
              >
                <div class="config-item-content">
                  <span class="config-name">{{ item }}</span>
                  <Tag color="error" v-if="configDescriptions[item]">
                    {{ configDescriptions[item] }}
                  </Tag>
                </div>
              </List.Item>
            </template>
          </List>
        </Card>
      </div>

      <!-- 编辑区域 -->
      <div class="config-editor">
        <Card v-if="selectedConfig" class="editor-card">
          <template #title>
            <span>{{ selectedConfig.name }}</span>
            <Tag color="green" style="margin-left: 8px">{{ getConfigExtension(selectedConfig.name) }}</Tag>
          </template>
          <template #extra>
            <Button
              type="primary"
              :loading="saving"
              @click="saveConfig"
            >
              <SaveOutlined /> Сохранить
            </Button>
          </template>
          <Input.TextArea
            v-model:value="editingContent"
            :auto-size="{ minRows: 18, maxRows: 30 }"
            class="editor-textarea"
          />
        </Card>

        <Card v-else class="empty-card">
          <Empty
            description="Выберите файл конфигурации слева"
            :image-style="{ height: '80px' }"
          />
        </Card>
      </div>
    </div>

    <!-- 重置Подтвердить弹窗 -->
    <Modal
      v-model:open="showResetModal"
      title="Подтвердить инициализацию"
      :confirm-loading="resetting"
      @ok="handleReset"
      okText="Подтвердить инициализацию"
      cancelText="Отмена"
      okType="danger"
    >
      <div class="reset-warning">
        <p style="color: #ff4d4f; font-weight: 500;">⚠️ Внимание: действие необратимо!</p>
        <p>Инициализация восстановит все файлы к шаблону:</p>
        <ul>
          <li>AGENTS.md — правила рабочего пространства</li>
          <li>IDENTITY.md — идентичность</li>
          <li>USER.md — данные пользователя</li>
          <li>SOUL.md — шаблон характера</li>
          <li>MEMORY.md — долгосрочная память</li>
          <li>HEARTBEAT.md — задачи heartbeat</li>
          <li>BOOTSTRAP.md — начальная настройка</li>
        </ul>

        <div class="reset-options">
          <p style="font-weight: 500; margin-bottom: 8px;">Дополнительные опции очистки:</p>
          <Checkbox v-model:checked="resetOptions.reset_sessions">
            Очистить всю историю сессий
          </Checkbox>
          <Checkbox v-model:checked="resetOptions.reset_memory">
            Очистить ежедневные файлы памяти
          </Checkbox>
          <Checkbox v-model:checked="resetOptions.reset_global_config">
            Сбросить глобальные настройки (LLM, Agent и т.д.)
          </Checkbox>
        </div>

        <p style="margin-top: 16px;">Продолжить?</p>
      </div>
    </Modal>
  </div>
</template>

<style scoped>
.config-view {
  min-height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 24px;
  box-sizing: border-box;
}

.config-header {
  flex-shrink: 0;
  margin-bottom: 24px;
}

.config-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 500;
}

.config-header p {
  margin: 0;
  color: #999;
}

.config-content {
  display: flex;
  gap: 24px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.config-list {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
}

.list-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.list-card :deep(.ant-card-body) {
  flex: 1;
  padding: 0;
  overflow-y: auto;
}

.config-item {
  cursor: pointer;
  padding: 12px 16px;
  transition: all 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.config-item:hover {
  background-color: #f5f5f5;
}

.config-item.active {
  background-color: #fff1f0;
  border-left: 3px solid #ff4d4f;
}

.config-item-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-name {
  font-weight: 500;
}

.config-editor {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.editor-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-card :deep(.ant-card-head) {
  flex-shrink: 0;
}

.editor-card :deep(.ant-card-body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-textarea {
  flex: 1;
  width: 100%;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  resize: none;
}

.empty-card {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Инициализация按钮 - 纯红色背景 + 白色字体（可Действие） */
.reset-btn {
  padding: 4px 12px;
  font-size: 13px;
  border: none;
  border-radius: 6px;
  background: #ff4d4f;
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.reset-btn:hover {
  background: #ff7875;
}

.reset-warning {
  padding: 8px 0;
}

.reset-warning ul {
  margin: 12px 0;
  padding-left: 24px;
}

.reset-warning li {
  margin: 4px 0;
  color: #666;
}

.reset-options {
  margin-top: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
