<script setup>
import { contractExamples } from '../data/contractExamples.js'

defineProps({
  selectClass: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['pick'])

function onChange(e) {
  const raw = e.target.value
  if (raw === '') return
  emit('pick', Number(raw))
  e.target.value = ''
}
</script>

<template>
  <select
    :class="selectClass"
    aria-label="填入示例合同（节选，体例参考全国合同示范文本库）"
    :disabled="disabled"
    @change="onChange"
  >
    <option value="">示例合同…</option>
    <option
      v-for="(ex, i) in contractExamples"
      :key="ex.id"
      :value="String(i)"
      :title="ex.sourceNote"
    >
      {{ ex.title }}
    </option>
  </select>
</template>
