<script setup>
import { RouterView } from 'vue-router'
import { useContractReview } from '../composables/useContractReview'

const { result, enhancing, enhanceError } = useContractReview()
</script>

<template>
  <div v-if="result" class="workspace-page report-workspace">
    <p v-if="enhancing" class="report-sidebar-status report-sidebar-status--pending report-workspace__status" role="status">
      正在完成 AI 增强，完成后将自动更新本页结论与风险表述…
    </p>
    <p
      v-else-if="enhanceError"
      class="report-sidebar-status report-sidebar-status--warn report-workspace__status"
      role="alert"
    >
      {{ enhanceError }}
    </p>

    <div class="panel-stack report-stack">
      <RouterView v-slot="{ Component }">
        <Transition name="fade-up" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </div>
  </div>
</template>
