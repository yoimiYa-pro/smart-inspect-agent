<script setup>
defineProps({
  version: { type: String, default: '0.1.0' },
})
</script>

<template>
  <footer class="app-footer" role="contentinfo">
    <p class="app-footer__line">
      <strong>智能合同审查</strong>
      · 演示与内部试用环境 · v{{ version }}
    </p>
    <p class="app-footer__muted">输出仅供参考，请以专业法律审查为准。</p>
  </footer>
</template>
