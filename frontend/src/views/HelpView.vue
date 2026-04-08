<script setup>
import { RouterLink } from 'vue-router'
import HelpContent from '../components/HelpContent.vue'
</script>

<template>
  <div class="workspace-page help-view">
    <p class="help-view-kicker">
      <RouterLink class="text-link" :to="{ name: 'review' }">← 合同与审查</RouterLink>
    </p>
    <h1 class="help-view-title help-view-title--minimal">说明</h1>
    <HelpContent />
  </div>
</template>
