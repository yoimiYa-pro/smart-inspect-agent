<script setup>
import { RouterLink } from 'vue-router'
import ReviewSummarySection from '../../components/ReviewSummarySection.vue'
import TrustBanner from '../../components/TrustBanner.vue'
import { useContractReview } from '../../composables/useContractReview'
import { buildReviewMarkdown, downloadTextFile } from '../../utils/exportMarkdown'

const { result, overallLevelClass, summaryCards } = useContractReview()

function exportMarkdown() {
  if (!result.value) {
    return
  }
  downloadTextFile('contract-review.md', buildReviewMarkdown(result.value))
}
</script>

<template>
  <div v-if="result" class="panel-stack">
    <TrustBanner :llm-mode="result.llm_mode" :mock-reason="result.mock_reason" />

    <ReviewSummarySection
      :result="result"
      :summary-cards="summaryCards"
      :overall-level-class="overallLevelClass"
    />

    <RouterLink :to="{ name: 'report-chat' }" class="report-chat-promo">
      <span class="report-chat-promo__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" width="28" height="28">
          <path
            stroke="currentColor"
            stroke-width="1.75"
            stroke-linejoin="round"
            d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
          />
          <path stroke="currentColor" stroke-width="1.75" stroke-linecap="round" d="M8 10h8M8 14h5" />
        </svg>
      </span>
      <div class="report-chat-promo__body">
        <p class="report-chat-promo__eyebrow">对话式追问</p>
        <strong class="report-chat-promo__title">智能追问</strong>
        <p class="report-chat-promo__text">
          结合本轮结论与合同原文继续提问：可改模型、看聚焦条款，回答区在底部输入框。
        </p>
      </div>
      <span class="report-chat-promo__cta">进入对话</span>
    </RouterLink>

    <div class="panel-card report-overview-cta">
      <p class="report-overview-cta__lead">继续查看</p>
      <div class="report-overview-cta__links">
        <button type="button" class="secondary-btn report-overview-cta__btn" @click="exportMarkdown">
          导出 Markdown
        </button>
        <RouterLink class="secondary-btn report-overview-cta__btn" :to="{ name: 'report-risks' }">
          风险分析
        </RouterLink>
        <RouterLink class="secondary-btn report-overview-cta__btn" :to="{ name: 'report-clauses' }">
          条款解读
        </RouterLink>
        <RouterLink class="primary-btn report-overview-cta__btn report-overview-cta__btn--chat" :to="{ name: 'report-chat' }">
          智能追问
        </RouterLink>
      </div>
    </div>
  </div>
</template>
