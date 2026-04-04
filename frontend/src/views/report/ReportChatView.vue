<script setup>
import DetailGuideChatSection from '../../components/DetailGuideChatSection.vue'
import { useContractReview } from '../../composables/useContractReview'

const {
  result,
  selectedRisk,
  selectedRole,
  useLlm,
  selectedModel,
  activeModel,
  modelOptions,
  modelSaving,
  handleModelChange,
  chatInput,
  chatMessages,
  chatLoading,
  chatError,
  submitChat,
} = useContractReview()

function setChatInput(v) {
  chatInput.value = v
}
</script>

<template>
  <div class="panel-stack">
    <DetailGuideChatSection
      :selected-risk="selectedRisk"
      :review-result="result"
      :selected-role="selectedRole"
      :use-llm="useLlm"
      :selected-model="selectedModel"
      :active-model="activeModel"
      :model-options="modelOptions"
      :model-saving="modelSaving"
      :chat-input="chatInput"
      :chat-messages="chatMessages"
      :chat-loading="chatLoading"
      :chat-error="chatError"
      @update:chat-input="setChatInput"
      @submit-chat="submitChat"
      @model-change="handleModelChange"
    />
  </div>
</template>
