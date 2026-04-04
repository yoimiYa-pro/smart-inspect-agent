<script setup>
import { categoryLabelMap } from '../composables/useContractReview'

defineProps({
  groupedRiskSections: { type: Array, required: true },
  selectedRiskId: { type: String, default: '' },
  totalRiskCount: { type: Number, required: true },
  riskyClauseCount: { type: Number, required: true },
  safeClauseCount: { type: Number, required: true },
})

const emit = defineEmits(['pick-risk', 'ask-risk'])
</script>

<template>
  <section id="review-section-risks" class="review-section-anchor risk-board">
    <article class="panel-card risk-board-summary">
      <div class="section-head compact">
        <div>
          <h2>风险分类</h2>
          <p>
            当前识别 {{ totalRiskCount }} 项风险，覆盖 {{ riskyClauseCount }} 条条款；无风险条款 {{ safeClauseCount }} 条。一个条款可能命中多项风险，因此数量不一定与条款总数一一对应。
          </p>
        </div>
      </div>
    </article>

    <article v-for="section in groupedRiskSections" :key="section.key" class="panel-card">
      <div class="section-head compact">
        <div>
          <h2>{{ section.title }}</h2>
          <p>{{ section.items.length }} 项</p>
        </div>
      </div>

      <transition-group v-if="section.items.length" name="list" tag="div" class="risk-list">
        <button
          v-for="risk in section.items"
          :key="risk.id"
          :id="'risk-card-' + risk.id"
          type="button"
          class="risk-card"
          :class="[risk.severity, { active: risk.id === selectedRiskId }]"
          @click="emit('pick-risk', risk.id)"
        >
          <div class="risk-card-head">
            <div class="risk-badge-row">
              <span class="severity-pill" :class="risk.severity">{{ risk.risk_level_text }}</span>
              <span class="priority-pill">优先级 #{{ risk.priority_rank }}</span>
              <span class="mini-badge">{{ categoryLabelMap[risk.category] || risk.category }}</span>
            </div>
            <button type="button" class="ghost-btn tiny-btn" @click.stop="emit('ask-risk', risk)">提问这条</button>
          </div>

          <h3>{{ risk.title }}</h3>
          <p class="risk-meta">条款 {{ risk.clause_index || '综合判断项' }} · {{ risk.priority_reason }}</p>

          <p><strong>风险：</strong>{{ risk.reason }}</p>
          <p><strong>解释：</strong>{{ risk.plain_explanation }}</p>
          <p><strong>建议：</strong>{{ risk.suggestion }}</p>
          <p><strong>角色影响：</strong>{{ risk.role_impact }}</p>
          <p><strong>法律依据：</strong>{{ risk.legal_basis }}</p>
          <p><strong>类似案例：</strong>{{ risk.case_reference }}</p>
          <p v-if="risk.clause_text"><strong>命中条款：</strong>{{ risk.clause_text }}</p>
        </button>
      </transition-group>
      <div v-else class="empty-box">{{ section.emptyText }}</div>
    </article>
  </section>
</template>
