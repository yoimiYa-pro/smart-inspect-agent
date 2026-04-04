<script setup>
import { RouterLink } from 'vue-router'
import RiskBoardSection from '../../components/RiskBoardSection.vue'
import TopRiskSection from '../../components/TopRiskSection.vue'
import { useContractReview } from '../../composables/useContractReview'

const {
  result,
  selectedRiskId,
  noRiskClauses,
  riskyClauseCount,
  totalRiskCount,
  groupedRiskSections,
  pickRisk,
  askRiskQuestion,
} = useContractReview()
</script>

<template>
  <div v-if="result" class="panel-stack">
    <p class="report-page-chat-hint">
      需要边看风险边问「为什么、怎么改」？
      <RouterLink :to="{ name: 'report-chat' }" class="report-page-chat-hint__link">打开智能追问（底部输入）</RouterLink>
    </p>
    <TopRiskSection :top-risks="result.top_risks" @pick-risk="pickRisk" @ask-risk="askRiskQuestion" />

    <RiskBoardSection
      :grouped-risk-sections="groupedRiskSections"
      :selected-risk-id="selectedRiskId"
      :total-risk-count="totalRiskCount"
      :risky-clause-count="riskyClauseCount"
      :safe-clause-count="noRiskClauses.length"
      @pick-risk="pickRisk"
      @ask-risk="askRiskQuestion"
    />
  </div>
</template>
