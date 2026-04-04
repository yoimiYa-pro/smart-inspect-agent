<script setup>
defineProps({
  clauses: { type: Array, required: true },
})
</script>

<template>
  <section id="review-section-safe" class="panel-card review-section-anchor">
    <div class="section-head compact">
      <div>
        <h2>无风险条款</h2>
        <p>共 {{ clauses.length }} 条未识别出明显风险，可优先作为相对安全条款查看。</p>
      </div>
    </div>

    <div v-if="clauses.length" class="clause-list">
      <article v-for="clause in clauses" :key="`safe-${clause.index}`" class="clause-item safe-clause-item">
        <div class="clause-index">条款 {{ clause.index }}</div>
        <p>{{ clause.text }}</p>
      </article>
    </div>
    <div v-else class="empty-box">当前未识别出明确的无风险条款。</div>
  </section>
</template>
