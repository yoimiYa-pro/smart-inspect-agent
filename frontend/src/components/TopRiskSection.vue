<script setup>
import { severityLabelMap } from '../composables/useContractReview'

defineProps({
  topRisks: { type: Array, required: true },
})

const emit = defineEmits(['pick-risk', 'ask-risk'])

</script>

<template>
  <section id="review-section-top3" class="panel-card top-risk-panel review-section-anchor">
    <div class="section-head compact">
      <div>
        <h2>🚨 优先处理 TOP3</h2>
        <p>按优先级展示最需要先谈判的 3 条，可能同时包含高风险和中风险项。</p>
      </div>
    </div>
    <div class="top-risk-grid">
      <article v-for="item in topRisks" :key="item.id" class="top-risk-item">
        <div class="top-risk-rank">TOP {{ item.priority_rank }}</div>
        <h3>{{ item.title }}</h3>
        <p>{{ item.priority_reason }}</p>
        <small>条款 {{ item.clause_index || '-' }} · {{ severityLabelMap[item.severity] }}</small>
        <div class="button-row top-risk-actions">
          <button type="button" class="secondary-btn tiny-btn" @click="emit('pick-risk', item.id)">查看详情</button>
          <button type="button" class="ghost-btn tiny-btn" @click="emit('ask-risk', item)">提问这条</button>
        </div>
      </article>
    </div>
  </section>
</template>
