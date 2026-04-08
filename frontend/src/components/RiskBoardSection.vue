<script setup>
import { reactive, ref } from 'vue'
import { fetchDelilegalLawDetail } from '../api.js'
import { categoryLabelMap } from '../composables/useContractReview'
import { stripHtmlTags } from '../utils/stripHtmlTags.js'

defineProps({
  groupedRiskSections: { type: Array, required: true },
  selectedRiskId: { type: String, default: '' },
  totalRiskCount: { type: Number, required: true },
  riskyClauseCount: { type: Number, required: true },
  safeClauseCount: { type: Number, required: true },
})

const emit = defineEmits(['pick-risk', 'ask-risk'])

const lawLoading = ref(false)
const lawModal = reactive({
  open: false,
  title: '',
  content: '',
  error: '',
})

function closeLawModal() {
  lawModal.open = false
  lawModal.error = ''
  lawModal.content = ''
}

async function openLawDetail(lawId, fallbackTitle) {
  lawModal.open = true
  lawModal.title = stripHtmlTags(fallbackTitle || '法规详情')
  lawModal.content = ''
  lawModal.error = ''
  lawLoading.value = true
  try {
    const data = await fetchDelilegalLawDetail(lawId, { timeoutMs: 60000 })
    lawModal.title = stripHtmlTags(data.title || lawModal.title)
    lawModal.content = stripHtmlTags(data.law_detail_content || '', { collapseWs: false })
    if (!lawModal.content.trim()) {
      lawModal.error = '未返回法规正文。'
    }
  } catch (e) {
    lawModal.error = String(e?.message || e || '加载失败')
  } finally {
    lawLoading.value = false
  }
}
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
          <div
            v-if="risk.law_references && risk.law_references.length"
            class="law-refs-block"
          >
            <p class="law-refs-label"><strong>相关法规（得理检索）：</strong></p>
            <ul class="law-refs-list">
              <li v-for="law in risk.law_references" :key="law.law_id">
                <span class="law-ref-title">{{ stripHtmlTags(law.title) }}</span>
                <button
                  type="button"
                  class="ghost-btn tiny-btn law-ref-btn"
                  @click.stop="openLawDetail(law.law_id, law.title)"
                >
                  查看全文
                </button>
                <p v-if="law.excerpt" class="law-ref-excerpt">
                  {{ stripHtmlTags(law.excerpt, { collapseWs: false }) }}
                </p>
              </li>
            </ul>
          </div>
          <p><strong>类似案例：</strong>{{ risk.case_reference }}</p>
          <div
            v-if="risk.case_references && risk.case_references.length"
            class="case-refs-block"
          >
            <p class="case-refs-label"><strong>检索案例（得理）：</strong></p>
            <ul class="case-refs-list">
              <li v-for="c in risk.case_references" :key="c.case_id">
                <span class="case-ref-title">{{ stripHtmlTags(c.title) }}</span>
                <span v-if="c.court_name" class="case-ref-meta"> · {{ stripHtmlTags(c.court_name) }}</span>
                <span v-if="c.case_number" class="case-ref-meta"> · {{ stripHtmlTags(c.case_number) }}</span>
                <span v-if="c.judgment_date" class="case-ref-meta"> · {{ stripHtmlTags(c.judgment_date) }}</span>
              </li>
            </ul>
          </div>
          <p v-if="risk.clause_text"><strong>命中条款：</strong>{{ risk.clause_text }}</p>
        </button>
      </transition-group>
      <div v-else class="empty-box">{{ section.emptyText }}</div>
    </article>

    <Teleport to="body">
      <div
        v-if="lawModal.open"
        class="law-modal-backdrop"
        role="presentation"
        @click.self="closeLawModal"
      >
        <div class="law-modal-card panel-card" role="dialog" aria-modal="true">
          <div class="law-modal-head">
            <h3 class="law-modal-title">{{ lawModal.title }}</h3>
            <button type="button" class="ghost-btn tiny-btn" @click="closeLawModal">关闭</button>
          </div>
          <p v-if="lawLoading" class="law-modal-status">加载中…</p>
          <p v-else-if="lawModal.error" class="law-modal-error">{{ lawModal.error }}</p>
          <pre v-else class="law-modal-body">{{ lawModal.content }}</pre>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<style scoped>
.law-refs-block {
  margin: 0.5rem 0 0.35rem;
}
.law-refs-label {
  margin: 0 0 0.25rem;
}
.law-refs-list {
  margin: 0;
  padding-left: 1.1rem;
}
.law-refs-list li {
  margin-bottom: 0.5rem;
}
.law-ref-title {
  display: inline;
  margin-right: 0.35rem;
}
.law-ref-btn {
  vertical-align: baseline;
}
.law-ref-excerpt {
  margin: 0.25rem 0 0;
  font-size: 0.88rem;
  color: var(--color-text-muted, #5c6570);
  white-space: pre-wrap;
}
.law-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.45);
}
.law-modal-card {
  max-width: min(720px, 100%);
  max-height: min(85vh, 900px);
  width: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.law-modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}
.law-modal-title {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.35;
}
.law-modal-status,
.law-modal-error {
  margin: 0.5rem 0 0;
}
.law-modal-error {
  color: #b42318;
}
.law-modal-body {
  margin: 0.5rem 0 0;
  padding: 0.75rem;
  overflow: auto;
  flex: 1;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 0.9rem;
  line-height: 1.5;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
}
.case-refs-block {
  margin: 0.5rem 0 0.35rem;
}
.case-refs-label {
  margin: 0 0 0.25rem;
}
.case-refs-list {
  margin: 0;
  padding-left: 1.1rem;
}
.case-refs-list li {
  margin-bottom: 0.35rem;
}
.case-ref-title {
  font-weight: 500;
}
.case-ref-meta {
  font-size: 0.88rem;
  color: var(--color-text-muted, #5c6570);
}
</style>
