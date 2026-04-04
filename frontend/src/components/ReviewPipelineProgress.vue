<script setup>
defineProps({
  activeStep: {
    type: Number,
    default: 0,
  },
})

const STEPS = [
  { id: 0, title: '条款切分', desc: '结构化拆条与类型推断' },
  { id: 1, title: '规则引擎', desc: '命中风险、排序与本地摘要' },
  { id: 2, title: '快路径返回', desc: '规则版报告已可阅读（若开启 AI）' },
  { id: 3, title: 'LLM 增强', desc: '后台润色与结论合并（第二阶段）' },
]
</script>

<template>
  <div class="review-pipeline panel-card" role="status" aria-live="polite">
    <div class="review-pipeline__head">
      <span class="review-pipeline__title">审查流水线</span>
      <span class="review-pipeline__hint">与后端阶段大致对齐；开启 AI 时第二段在报告页后台继续</span>
    </div>
    <ol class="review-pipeline__steps">
      <li
        v-for="(s, i) in STEPS"
        :key="s.id"
        class="review-pipeline__step"
        :class="{
          'review-pipeline__step--done': i < activeStep,
          'review-pipeline__step--current': i === activeStep,
        }"
      >
        <span class="review-pipeline__idx">{{ i + 1 }}</span>
        <span class="review-pipeline__text">
          <strong>{{ s.title }}</strong>
          <small>{{ s.desc }}</small>
        </span>
      </li>
    </ol>
  </div>
</template>
