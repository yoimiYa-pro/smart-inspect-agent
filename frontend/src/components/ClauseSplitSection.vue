<script setup>
defineProps({
  clauses: { type: Array, required: true },
})
</script>

<template>
  <section id="review-section-clauses" class="panel-card review-section-anchor">
    <div class="section-head compact">
      <div>
        <h2>条款切分</h2>
        <p>{{ clauses.length }} 条</p>
      </div>
    </div>
    <div class="clause-list clause-list--grid">
      <article v-for="clause in clauses" :key="clause.index" class="clause-item">
        <div class="clause-index">条款 {{ clause.index }}</div>
        <p>{{ clause.text }}</p>
      </article>
    </div>
  </section>
</template>
