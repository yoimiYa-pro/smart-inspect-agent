<script setup>
import { computed } from 'vue'
import { buildMockNotice } from '../utils/mockNotice'

const props = defineProps({
  llmMode: { type: String, default: '' },
  mockReason: { type: String, default: '' },
})

const visible = computed(() => {
  const m = (props.llmMode || '').toLowerCase()
  return m === 'mock' || Boolean(props.mockReason)
})

const text = computed(() => buildMockNotice(props.mockReason || '', 'analysis'))
</script>

<template>
  <div v-if="visible" class="trust-banner" role="status">
    <span class="trust-banner__icon" aria-hidden="true">i</span>
    <p class="trust-banner__text">{{ text }}</p>
  </div>
</template>
