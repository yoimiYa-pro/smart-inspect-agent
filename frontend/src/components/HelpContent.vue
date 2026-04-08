<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="help-body help-body--minimal">
    <p class="help-lead">
      在
      <RouterLink class="text-link" :to="{ name: 'review' }">合同与审查</RouterLink>
      粘贴正文，在底部选择视角、模型后提交；侧栏进入报告。模型与 API 亦在底部药丸内调整。
    </p>
    <ul class="help-min-list">
      <li>密钥未配或接口异常时可能使用 mock，界面会标明。</li>
      <li>输出仅供辅助，不构成法律意见；勿粘贴涉密或未授权内容。</li>
    </ul>
  </div>
</template>
