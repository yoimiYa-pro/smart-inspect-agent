<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import ExampleContractPicker from './ExampleContractPicker.vue'
import { roleOptions } from '../composables/useContractReview'

const props = defineProps({
  contractText: { type: String, required: true },
  errorMessage: { type: String, default: '' },
  selectedRole: { type: String, required: true },
  selectedModel: { type: String, required: true },
  activeModel: { type: String, required: true },
  modelOptions: { type: Array, required: true },
  useLlm: { type: Boolean, required: true },
  loading: { type: Boolean, default: false },
  modelSaving: { type: Boolean, default: false },
})

defineEmits([
  'update:contractText',
  'update:selectedRole',
  'update:useLlm',
  'model-change',
  'set-example',
  'clear-all',
  'submit-review',
])

const charCount = computed(() => [...props.contractText].length)

const textareaRef = ref(null)
const TEXTAREA_MAX_PX = 200

function syncTextareaHeight() {
  nextTick(() => {
    const el = textareaRef.value
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, TEXTAREA_MAX_PX)}px`
  })
}

function onTextInput() {
  syncTextareaHeight()
}

watch(
  () => props.contractText,
  () => syncTextareaHeight(),
)

onMounted(() => syncTextareaHeight())
</script>

<template>
  <section class="contract-composer gemini-composer">
    <div class="gemini-composer__pill">
      <textarea
        ref="textareaRef"
        :value="contractText"
        class="contract-input gemini-composer__textarea"
        placeholder="粘贴或输入合同全文…"
        aria-label="合同全文输入"
        rows="1"
        spellcheck="false"
        :aria-invalid="errorMessage ? 'true' : 'false'"
        :aria-describedby="errorMessage ? 'contract-input-error' : undefined"
        @input="
          $emit('update:contractText', $event.target.value);
          onTextInput();
        "
      />

      <div class="gemini-composer__toolbar" aria-label="审查选项">
        <div class="gemini-composer__toolbar-main">
          <select
            :value="selectedRole"
            class="gemini-composer__mini-select gemini-composer__mini-select--role"
            aria-label="审查视角"
            @change="$emit('update:selectedRole', $event.target.value)"
          >
            <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
          </select>

          <select
            :value="selectedModel"
            class="gemini-composer__mini-select gemini-composer__mini-select--model"
            aria-label="审查模型"
            :disabled="modelSaving || loading"
            @change="$emit('model-change', $event)"
          >
            <option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</option>
          </select>

          <label
            class="gemini-composer__chip"
            title="优先调用真实大模型；失败时自动 fallback mock"
          >
            <input
              :checked="useLlm"
              type="checkbox"
              @change="$emit('update:useLlm', $event.target.checked)"
            />
            <span>API</span>
          </label>

          <ExampleContractPicker
            class="gemini-composer__example-picker"
            select-class="gemini-composer__mini-select gemini-composer__mini-select--example"
            :disabled="loading || modelSaving"
            @pick="$emit('set-example', $event)"
          />
          <button type="button" class="gemini-composer__tool" title="清空正文" @click="$emit('clear-all')">
            <span class="gemini-composer__tool-glyph" aria-hidden="true">×</span>
            <span class="gemini-composer__tool-txt">清空</span>
          </button>

          <span
            class="gemini-composer__model-hint"
            :title="`当前服务端生效模型：${activeModel}`"
          >
            <span class="gemini-composer__model-hint-label">生效</span>
            <span class="gemini-composer__model-hint-val">{{ activeModel }}</span>
            <template v-if="modelSaving">…</template>
          </span>
        </div>

        <button
          type="button"
          class="gemini-composer__send"
          :disabled="loading || modelSaving"
          :aria-busy="loading ? 'true' : undefined"
          aria-label="开始审查"
          :title="loading ? '审查中' : '开始审查'"
          @click="$emit('submit-review')"
        >
          <svg class="gemini-composer__send-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M12 5v12M12 5l4 4M12 5L8 9"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>
      </div>
    </div>

    <p class="gemini-composer__fineprint">
      <span class="gemini-composer__fineprint-meta" aria-live="polite">{{ charCount }} 字</span>
      <span class="gemini-composer__fineprint-sep" aria-hidden="true">·</span>
      <span>结论由模型生成，仅供参考，不构成法律意见。</span>
    </p>

    <p
      v-if="errorMessage"
      id="contract-input-error"
      class="status-error gemini-composer__error"
      role="alert"
      aria-live="assertive"
    >
      {{ errorMessage }}
    </p>
  </section>
</template>
