<template>
  <div class="panel">
    <div class="report-header">
      <div>
        <strong>{{ title }}</strong>
      </div>
      <span v-if="report" class="badge" :class="report.health_level">{{ report.health_level }}</span>
    </div>

    <div v-if="!report" class="empty">Выберите сайт для просмотра отчёта о здоровье</div>

    <div v-else class="report-body">
      <div class="kpis">
        <div class="kpi">
          <div class="label">Оценка здоровья</div>
          <div class="value">{{ report.health_score }}</div>
        </div>
        <div class="kpi">
          <div class="label">Доля устройств онлайн</div>
          <div class="value">{{ (report.sections.device_status.online_rate * 100).toFixed(2) }}%</div>
        </div>
        <div class="kpi">
          <div class="label">Соответствие терминалов</div>
          <div class="value">{{ (report.sections.user_status.compliant_rate * 100).toFixed(2) }}%</div>
        </div>
      </div>

      <div class="section">
        <h3>Агент анализа логов</h3>
        <p>{{ report.sections.log_analysis.summary }}</p>
      </div>

      <div class="section">
        <h3>Агент состояния устройств</h3>
        <p>{{ report.sections.device_status.summary }}</p>
      </div>

      <div class="section">
        <h3>Агент состояния пользователей</h3>
        <p>{{ report.sections.user_status.summary }}</p>
      </div>

      <div class="section">
        <h3>Рекомендации агента сетевого здоровья</h3>
        <ul class="recommendation-list">
          <li v-for="(item, idx) in report.recommendations" :key="idx">{{ item }}</li>
        </ul>
      </div>

      <div class="section" v-if="report.llm_insight">
        <h3>Комплексная оценка LLM</h3>
        <p>{{ report.llm_insight }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'ReportPanel' })

defineProps({
  title: {
    type: String,
    default: 'Отчёт о сетевом здоровье'
  },
  report: {
    type: Object,
    default: null
  }
})
</script>
