<template>
  <div class="app-root min-h-screen">
    <!-- View 1: Setup -->
    <SetupView
      v-if="currentView === 'setup'"
      v-model:topic="form.topic"
      @start="startProduction"
    />

    <!-- View 2: Production -->
    <ProductionView
      v-else-if="currentView === 'producing'"
      ref="productionRef"
      :logs="logs"
      :is-waiting="isWaiting"
      :waiting-dots="waitingDots"
      :production-stage="productionStage"
      :progress-percent="progressPercent"
      :report-ready="reportReady"
      :podcast-ready="podcastReady"
      :audio-url="audioUrl"
      @cancel="cancelProduction"
      @download-report="downloadReport"
      @go-player="currentView = 'player'"
    />

    <!-- View 3: Player -->
    <PlayerView
      v-else-if="currentView === 'player'"
      :topic="form.topic"
      :audio-url="audioUrl"
      :report-markdown="reportMarkdown"
      @reset="resetApp"
      @download-report="downloadReport"
    />
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, nextTick } from "vue";
import { runResearchStream, cancelResearch, type ResearchStreamEvent } from "./services/api";

import SetupView from "./components/SetupView.vue";
import ProductionView from "./components/ProductionView.vue";
import PlayerView from "./components/PlayerView.vue";
import type { LogEntry } from "./components/TerminalLog.vue";
import type { ProductionStage } from "./components/ProductionView.vue";

// --- Types ---
type ViewState = "setup" | "producing" | "player";

// --- State ---
const currentView = ref<ViewState>("setup");
const productionStage = ref<ProductionStage>("research");
const form = reactive({ topic: "" });

const logs = ref<LogEntry[]>([]);
const reportReady = ref(false);
const podcastReady = ref(false);

const audioProgress = reactive({ current: 0, total: 0, role: "" });
const taskProgress = reactive({ completed: 0, total: 0 });
const progressPercent = ref(0);
const currentStatusMessage = ref("");
const isWaiting = ref(false);
const waitingDots = ref(".");
let waitingInterval: ReturnType<typeof setInterval> | null = null;

const reportMarkdown = ref("");
const audioUrl = ref("");

let abortController: AbortController | null = null;

const productionRef = ref<InstanceType<typeof ProductionView> | null>(null);

// --- Helpers ---

function startWaitingAnimation() {
  stopWaitingAnimation();
  isWaiting.value = true;
  waitingDots.value = ".";
  waitingInterval = setInterval(() => {
    waitingDots.value = waitingDots.value.length >= 3 ? "." : waitingDots.value + ".";
  }, 500);
}

function stopWaitingAnimation() {
  isWaiting.value = false;
  if (waitingInterval) {
    clearInterval(waitingInterval);
    waitingInterval = null;
  }
}

function addLog(message: string) {
  const time = new Date().toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
  logs.value.push({ time, message });
  nextTick(() => {
    productionRef.value?.scrollTerminal();
  });
}

// --- Actions ---

async function startProduction() {
  if (!form.topic.trim()) return;

  currentView.value = "producing";
  productionStage.value = "research";
  logs.value = [];
  reportMarkdown.value = "";
  audioUrl.value = "";
  audioProgress.current = 0;
  audioProgress.total = 0;
  taskProgress.completed = 0;
  taskProgress.total = 0;
  progressPercent.value = 2;
  currentStatusMessage.value = "Инициализация...";
  reportReady.value = false;
  podcastReady.value = false;

  abortController = new AbortController();
  startWaitingAnimation();

  addLog("🚀 Запуск DeepCast...");
  addLog(`📌 Тема: ${form.topic}`);

  try {
    await runResearchStream(
      { topic: form.topic },
      handleStreamEvent,
      { signal: abortController.signal }
    );
  } catch (err: any) {
    if (err.name === "AbortError" || err.message?.includes("aborted")) {
      addLog("🛑 Создание отменено.");
    } else {
      addLog(`❌ Ошибка: ${err.message || err}`);
      console.error(err);
    }
  } finally {
    stopWaitingAnimation();
  }
}

function handleStreamEvent(event: ResearchStreamEvent) {
  console.log("Event:", event.type, event);

  if (event.type === "log") {
    const msg = String((event as any).message || "");
    const cleanMsg = msg.replace(/\u001b\[\d+m/g, "");
    addLog(`INFO: ${cleanMsg}`);

    const ttsMatch = cleanMsg.match(/\[TTS (\d+)\/(\d+)\]/);
    if (ttsMatch) {
      audioProgress.current = parseInt(ttsMatch[1], 10);
      audioProgress.total = parseInt(ttsMatch[2], 10);
      currentStatusMessage.value = `Генерация аудио: ${audioProgress.current}/${audioProgress.total}`;
    }
    return;
  }

  if (event.type === "stage_change") {
    const payload = event as any;
    const stage = payload.stage;
    const message = payload.message || "";
    currentStatusMessage.value = message;

    addLog("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    addLog(`📌 [STAGE] ${stage.toUpperCase()} - ${message}`);
    addLog("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    if (stage === "report") {
      productionStage.value = "research";
      progressPercent.value = 40;
    } else if (stage === "script") {
      productionStage.value = "script";
      progressPercent.value = 55;
    } else if (stage === "audio") {
      productionStage.value = "audio";
      progressPercent.value = 70;
    } else if (stage === "synthesis") {
      productionStage.value = "audio";
      progressPercent.value = 95;
    }
  }

  if (event.type === "tool_call") {
    const p = event as any;
    addLog(`🔧 [TOOL] ${p.tool} - ${p.agent || "Agent"}`);
  }

  if (event.type === "todo_list") {
    const p = event as any;
    const tasks = p.tasks || [];
    taskProgress.total = tasks.length;
    taskProgress.completed = 0;
  }

  if (event.type === "task_status") {
    const p = event as any;
    if (p.status === "completed") {
      taskProgress.completed++;
      if (taskProgress.total > 0) {
        progressPercent.value = Math.round((taskProgress.completed / taskProgress.total) * 40);
      }
      addLog(`✅ [TASK ${p.task_id}] ${p.title}`);
    } else if (p.status === "in_progress") {
      addLog(`🚀 [TASK ${p.task_id}] ${p.title} (In Progress)`);
    } else if (p.status === "failed") {
      addLog(`❌ [TASK ${p.task_id}] Failed: ${p.title}`);
    }
  }

  if (event.type === "final_report") {
    reportMarkdown.value = String((event as any).report);
    reportReady.value = true;
    addLog("📄 [REPORT] Отчёт сгенерирован");
  }

  if (event.type === "podcast_script") {
    productionStage.value = "audio";
    addLog("🎙️ [SCRIPT] Сценарий готов");
  }

  if (event.type === "audio_start") {
    const p = event as any;
    audioProgress.total = p.total || 0;
    addLog(`🎵 [AUDIO] Начало генерации аудио, всего ${audioProgress.total} сегм.`);
  }

  if (event.type === "audio_progress") {
    const p = event as any;
    audioProgress.current = p.current;
    audioProgress.total = p.total;
    currentStatusMessage.value = `Генерация аудио: ${p.role} (${p.current}/${p.total})`;
    if (p.total > 0) {
      progressPercent.value = 70 + Math.round((p.current / p.total) * 25);
    }
  }

  if (event.type === "podcast_ready") {
    const p = event as any;
    const filename = String(p.file).split(/[\\/]/).pop();
    if (filename) {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      audioUrl.value = `${baseUrl}/output/audio/${filename}`;
      podcastReady.value = true;
      productionStage.value = "done";
      progressPercent.value = 100;
      currentStatusMessage.value = "🎉 Подкаст готов!";
      stopWaitingAnimation();
      addLog(`🎉 [PODCAST] Готово: ${filename}`);
    }
  }

  if (event.type === "cancelled") {
    const msg = (event as any).message || "Исследование отменено";
    addLog(`🛑 [CANCELLED] ${msg}`);
    stopWaitingAnimation();
    productionStage.value = "cancelled";
    currentStatusMessage.value = "Задача отменена";
    return;
  }

  if (event.type === "done") {
    addLog("✅ [DONE] Все задачи завершены");
    stopWaitingAnimation();
    productionStage.value = "done";
    progressPercent.value = 100;

    if (!podcastReady.value && audioProgress.total > 0) {
      const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      fetch(`${baseUrl}/api/audio/latest`)
        .then(res => res.json())
        .then(data => {
          if (data.file) {
            audioUrl.value = `${baseUrl}${data.url}`;
            podcastReady.value = true;
            currentStatusMessage.value = "🎉 Подкаст готов!";
            addLog(`🎉 [PODCAST] Найден аудиофайл: ${data.file}`);
          } else {
            currentStatusMessage.value = "Задача завершена (аудио не создано)";
            addLog(`⚠️ Аудиофайл не найден: ${data.error || "неизвестная ошибка"}`);
          }
        })
        .catch(err => {
          currentStatusMessage.value = "Задача завершена (аудио недоступно)";
          addLog(`⚠️ Не удалось получить аудио: ${err.message}`);
        });
    } else if (podcastReady.value) {
      currentStatusMessage.value = "🎉 Подкаст готов!";
    } else {
      currentStatusMessage.value = "Задача завершена (аудио могло не создаться)";
    }
  }
}

function cancelProduction() {
  if (confirm("Отменить создание?")) {
    addLog("🛑 Запрос на отмену...");

    // 1. 立即中断 SSE 连接 — 后端 monitor_disconnect 会自动检测并设置 cancel_event
    if (abortController) {
      abortController.abort();
      abortController = null;
    }

    // 2. 显式调用 cancel API 作为后备（防止 disconnect 检测延迟）
    cancelResearch().catch(() => {});

    stopWaitingAnimation();
    productionStage.value = "cancelled";
    addLog("🛑 Создание отменено");

    setTimeout(() => {
      currentView.value = "setup";
      currentStatusMessage.value = "";
    }, 1000);
  }
}

function resetApp() {
  currentView.value = "setup";
  form.topic = "";
  currentStatusMessage.value = "";
  reportReady.value = false;
  podcastReady.value = false;
  audioUrl.value = "";
  stopWaitingAnimation();
}

function downloadReport() {
  if (!reportMarkdown.value) return;
  const blob = new Blob([reportMarkdown.value], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "DeepCast-research-report.md";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.app-root {
  background: linear-gradient(145deg, #0c0e14 0%, #111420 30%, #0e1018 60%, #0a0c12 100%);
  background-attachment: fixed;
}
</style>