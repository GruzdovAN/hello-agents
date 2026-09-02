/**
 * Агент расширения английских предложений - СессииСтатус管理
 * Используется Pinia 管理СессииСтатус
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type {
  SessionState,
  AgentResponse,
  Mode,
  Stage,
  RoundRecord
} from '../types/expand';
import { startSession, submitSentence, getSession } from '../api/expand';

export const useSessionStore = defineStore('session', () => {
  // Статус
  const session = ref<SessionState | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const currentQuestion = ref<string | null>(null);

  // 计算属性
  const currentStage = computed<Stage>(() => session.value?.current_stage || 'stage1');
  const mode = computed<Mode>(() => session.value?.mode || 'manual');
  const seedSentence = computed(() => session.value?.seed_sentence || '');
  const rounds = computed<RoundRecord[]>(() => session.value?.rounds || []);
  const finalPolished = computed(() => session.value?.final_polished || null);
  const isDone = computed(() => session.value?.current_stage === 'done');
  const sessionId = computed(() => session.value?.session_id || '');

  /**
   * 开始新的Сессии
   */
  async function startNewSession(seedSentence: string, mode: Mode) {
    loading.value = true;
    error.value = null;

    try {
      session.value = {
        session_id: "",
        mode,
        seed_sentence: seedSentence,
        current_stage: null,
        rounds: [],
        final_polished: null,
      };

      const response = await startSession({
        seed_sentence: seedSentence,
        mode,
      });

      // 更新Статус
      session.value = {
        session_id: response.session_id,
        mode,
        seed_sentence: seedSentence,
        current_stage: response.stage,
        rounds: [],
        final_polished: response.final_polished || null,
      };

      // Сохранить当前提问
      currentQuestion.value = response.question || null;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start session';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Отправить用户句子（Ручной режим）
   */
  async function submitUserSentence(userSentence: string) {
    if (!session.value) {
      throw new Error('No active session');
    }

    loading.value = true;
    error.value = null;

    try {
      const response = await submitSentence({
        session_id: session.value.session_id,
        user_sentence: userSentence,
      });

      // 直接从响应中获取信息，不调用 refreshSession
      // 首先，需要手动更新СессииСтатус
      if (session.value && response.evaluation && response.expanded_sentence) {
        // 创建新的 round 记录
        const newRound = {
          stage: session.value.current_stage,
          question: currentQuestion.value || '',
          user_answer: userSentence,
          evaluation: response.evaluation,
          expanded_sentence: response.expanded_sentence
        };
        
        // 添加到 rounds 数组
        session.value.rounds.push(newRound);
        
        // 更新当前阶段
        if (response.stage) {
          session.value.current_stage = response.stage;
        }
        
        // 更新最终润色Результат
        if (response.final_polished) {
          session.value.final_polished = response.final_polished;
        }
      }

      // Сохранить当前提问
      currentQuestion.value = response.question || null;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to submit sentence';
      throw e;
    } finally {
      loading.value = false;
    }
  }

  /**
   * ОбновитьСессииСтатус
   */
  async function refreshSession() {
    if (!session.value) {
      throw new Error('No active session');
    }

    try {
      const updatedSession = await getSession(session.value.session_id);
      session.value = updatedSession;
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to refresh session';
      throw e;
    }
  }

  /**
   * 添加轮次记录（用于Автоматический режим）
   */
  function addRound(round: RoundRecord) {
    if (!session.value) {
      throw new Error('No active session');
    }
    session.value.rounds.push(round);
  }

  /**
   * 更新当前阶段
   */
  function updateStage(stage: Stage) {
    if (!session.value) {
      throw new Error('No active session');
    }
    session.value.current_stage = stage;
  }

  /**
   * 设置最终润色Версия
   */
  function setFinalPolished(polished: string) {
    if (!session.value) {
      throw new Error('No active session');
    }
    session.value.final_polished = polished;
  }

  /**
   * 设置当前提问
   */
  function setCurrentQuestion(question: string | null) {
    currentQuestion.value = question;
  }

  /**
   * ОчиститьСессии
   */
  function clearSession() {
    session.value = null;
    currentQuestion.value = null;
    error.value = null;
    loading.value = false;
  }

  /**
   * 获取当前阶段的标题
   */
  function getStageTitle(stage: Stage): string {
    const titles: Record<Stage, string> = {
      stage1: 'Этап 1: время и место',
      stage2: 'Этап 2: персонажи и причины',
      stage3: 'Этап 3: способ и детали',
      done: 'Готово',
    };
    return titles[stage];
  }

  return {
    // Статус
    session,
    loading,
    error,
    currentQuestion,

    // 计算属性
    currentStage,
    mode,
    seedSentence,
    rounds,
    finalPolished,
    isDone,
    sessionId,

    // 方法
    startNewSession,
    submitUserSentence,
    refreshSession,
    addRound,
    updateStage,
    setFinalPolished,
    setCurrentQuestion,
    clearSession,
    getStageTitle,
  };
});
