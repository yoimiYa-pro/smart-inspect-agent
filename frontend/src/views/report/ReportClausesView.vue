<script setup>
import { RouterLink } from 'vue-router'
import ClauseSplitSection from '../../components/ClauseSplitSection.vue'
import SafeClausesSection from '../../components/SafeClausesSection.vue'
import { useContractReview } from '../../composables/useContractReview'

const { result, noRiskClauses } = useContractReview()
</script>

<template>
  <div v-if="result" class="panel-stack">
    <p class="report-page-chat-hint">
      对某条仍有疑问？
      <RouterLink :to="{ name: 'report-chat' }" class="report-page-chat-hint__link">去智能追问继续对话</RouterLink>
    </p>
    <SafeClausesSection :clauses="noRiskClauses" />
    <ClauseSplitSection :clauses="result.clauses" />
  </div>
</template>
