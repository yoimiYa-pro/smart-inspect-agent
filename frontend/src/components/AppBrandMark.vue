<script setup>
/**
 * 品牌徽标：中枢 + 三节点联结，表达「智能体 / 多步协同」；
 * 与侧栏「合同与审查」所用图标区分（该入口为编辑/撰写类图标）。
 */
</script>

<template>
  <svg class="app-brand-mark-svg" viewBox="0 0 32 32" width="32" height="32" aria-hidden="true" focusable="false">
    <rect width="32" height="32" rx="9" fill="#1a73e8" />
    <!-- 联结线：智能体中枢与多能力节点 -->
    <path
      d="M16 15.1V9.5M16 16.9l-5.9 3.4M16 16.9l5.9 3.4"
      stroke="#ffffff"
      stroke-width="1.25"
      stroke-linecap="round"
    />
    <circle cx="16" cy="8.4" r="2" fill="#ffffff" />
    <circle cx="10.1" cy="20.3" r="2" fill="#ffffff" />
    <circle cx="21.9" cy="20.3" r="2" fill="#ffffff" />
    <!-- 核心：外环实底 + 内点，略像「感知核」 -->
    <circle cx="16" cy="16" r="3.65" fill="#ffffff" />
    <circle cx="16" cy="16" r="1.45" fill="#1a73e8" />
  </svg>
</template>

<style scoped>
.app-brand-mark-svg {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
