<script setup>
import { computed, nextTick, onScopeDispose, ref, watch } from 'vue'
import { suggestedQuestions } from '../composables/useContractReview'
import { buildMockNotice } from '../utils/mockNotice'
import { buildAgentFollowupChats } from '../utils/agentSuggestions'
import { getChatAnswerSource } from '../utils/chatAnswerSource'
import { renderAssistantMarkdown } from '../utils/renderAssistantMarkdown'

const THINKING_STEPS = [
  '正在读取合同与本轮审查结论…',
  '正在对齐你的问题与聚焦条款…',
  '正在组织回答…',
]

const props = defineProps({
  selectedRisk: { type: Object, default: null },
  reviewResult: { type: Object, default: null },
  selectedRole: { type: String, default: '乙方' },
  useLlm: { type: Boolean, default: true },
  selectedModel: { type: String, default: '' },
  activeModel: { type: String, default: '' },
  modelOptions: { type: Array, default: () => [] },
  modelSaving: { type: Boolean, default: false },
  chatMessages: { type: Array, required: true },
  chatInput: { type: String, required: true },
  chatLoading: { type: Boolean, required: true },
  chatError: { type: String, default: '' },
})

const emit = defineEmits(['update:chatInput', 'submit-chat', 'model-change'])

const chatHistoryRef = ref(null)
const thinkingStepIndex = ref(0)
let thinkingTimer = null

watch(
  () => props.chatMessages,
  async () => {
    await nextTick()
    const el = chatHistoryRef.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  },
  { deep: true, flush: 'post' },
)

watch(
  () => props.chatLoading,
  (loading) => {
    if (thinkingTimer) {
      clearInterval(thinkingTimer)
      thinkingTimer = null
    }
    if (loading) {
      thinkingStepIndex.value = 0
      thinkingTimer = window.setInterval(() => {
        thinkingStepIndex.value = (thinkingStepIndex.value + 1) % THINKING_STEPS.length
      }, 2000)
    }
    nextTick().then(() => {
      const el = chatHistoryRef.value
      if (el) el.scrollTop = el.scrollHeight
    })
  },
  { flush: 'post' },
)

onScopeDispose(() => {
  if (thinkingTimer) clearInterval(thinkingTimer)
})

function onComposerEnter(e) {
  if (e.shiftKey) {
    return
  }
  e.preventDefault()
  emit('submit-chat', '')
}

function renderMd(text) {
  return renderAssistantMarkdown(text)
}

const followupChipsForPanel = computed(() => {
  if (props.chatLoading) return []
  const msgs = props.chatMessages
  if (!msgs.length) return []
  const last = msgs[msgs.length - 1]
  if (last.role !== 'assistant') return []
  const server = last.suggested_followups
  if (Array.isArray(server) && server.length > 0) {
    return server.slice(0, 4)
  }
  const lastUser = [...msgs].reverse().find((m) => m.role === 'user')
  return buildAgentFollowupChats({
    result: props.reviewResult,
    selectedRisk: props.selectedRisk,
    lastUserContent: lastUser?.content || '',
  })
})

const thinkingLabel = computed(() => THINKING_STEPS[thinkingStepIndex.value] || THINKING_STEPS[0])
</script>

<template>
  <section id="review-section-chat" class="report-chat-layout review-section-anchor">
    <article class="panel-card gemini-chat-fusion">
      <div class="gemini-chat-fusion__grid">
        <div
          :id="selectedRisk ? 'review-detail-panel' : undefined"
          class="gemini-chat-fusion__pane gemini-chat-fusion__pane--clause"
        >
          <template v-if="selectedRisk">
            <div class="section-head compact gemini-chat-fusion__head">
              <div>
                <h2 class="gemini-chat-fusion__title">当前聚焦条款</h2>
                <p class="detail-side-card__subtitle">{{ selectedRisk.title }}</p>
              </div>
              <span class="level-badge" :class="selectedRisk.severity">{{ selectedRisk.risk_level_text }}</span>
            </div>
            <div class="detail-box gemini-chat-fusion__body">
              <p><strong>条款位置：</strong>{{ selectedRisk.clause_index ? `第${selectedRisk.clause_index}条` : '综合判断' }}</p>
              <p><strong>风险判断：</strong>{{ selectedRisk.issue }}</p>
              <p><strong>规则依据：</strong>{{ selectedRisk.basis }}</p>
              <p><strong>修改建议：</strong>{{ selectedRisk.suggestion }}</p>
              <p><strong>推荐追问：</strong>{{ selectedRisk.followup_hint }}</p>
              <p><strong>角色建议：</strong>{{ selectedRisk.role_advice }}</p>
            </div>
          </template>
          <template v-else>
            <div class="gemini-chat-fusion__head">
              <h2 class="gemini-chat-fusion__title">当前聚焦条款</h2>
              <p class="gemini-chat-fusion__placeholder">
                在「风险分析」中选中一条风险后，此处展示条款摘要，便于与右侧对话对照。
              </p>
            </div>
          </template>
        </div>

        <div id="review-chat-panel" class="gemini-chat-fusion__pane gemini-chat-fusion__pane--chat">
          <header class="chat-panel__header gemini-chat-fusion__chat-head chat-panel__header--smart-chat">
            <div class="chat-panel__title-row">
              <span class="chat-panel__title-badge">对话式</span>
              <h2 class="chat-panel__title">智能追问 · 合同审查智能体</h2>
            </div>
            <p class="chat-panel__lede chat-panel__lede--accent">
              在页面底部输入问题并发送；可先选「风险分析」聚焦条款，左侧会同步显示摘要。
            </p>
          </header>

          <div class="agent-context-row" aria-label="智能体上下文">
            <span class="agent-context-chip">视角 {{ selectedRole }}</span>
            <span class="agent-context-chip" :title="activeModel || ''">
              模型 {{ activeModel || '—' }}
            </span>
            <span class="agent-context-chip">{{ useLlm ? '优先真实 API' : '允许 mock' }}</span>
            <span class="agent-context-chip agent-context-chip--focus">
              {{ selectedRisk ? `聚焦：${selectedRisk.title}`.slice(0, 48) : '未聚焦条款' }}
            </span>
          </div>
          <p class="agent-source-legend">
            助手每条回复旁有来源角标：
            <span class="agent-source-legend__live">大模型回答</span>
            <span class="agent-source-legend__mock">本地兜底</span>
            <span class="agent-source-legend__rules">审查结论摘要</span>
            （悬停角标可看说明）
          </p>

          <div class="suggestion-row suggestion-row--gemini" aria-label="推荐问题">
            <button
              v-for="question in suggestedQuestions"
              :key="question"
              type="button"
              class="chip-btn suggestion-row__chip"
              :disabled="chatLoading"
              @click="emit('submit-chat', question)"
            >
              {{ question }}
            </button>
          </div>

          <div ref="chatHistoryRef" class="chat-history chat-history--gemini">
            <div class="chat-history__inner">
              <transition-group name="list" tag="div" class="chat-history__messages">
                <article
                  v-for="(message, index) in chatMessages"
                  :key="`${message.role}-${index}-${(message.content || '').length}`"
                  class="chat-message gemini-msg"
                  :class="message.role"
                >
                  <div
                    class="gemini-msg__head"
                    :class="message.role === 'user' ? 'gemini-msg__head--user' : ''"
                  >
                    <div class="chat-role">{{ message.role === 'assistant' ? '智能体' : '你' }}</div>
                    <span
                      v-if="message.role === 'assistant'"
                      class="chat-source-tag"
                      :class="`chat-source-tag--${getChatAnswerSource(message).variant}`"
                      :title="getChatAnswerSource(message).title"
                    >{{ getChatAnswerSource(message).label }}</span>
                  </div>
                  <div
                    v-if="message.role === 'assistant'"
                    class="chat-message__body chat-message__body--md"
                    v-html="renderMd(message.content)"
                  />
                  <p v-else class="chat-message__body">{{ message.content }}</p>
                  <div v-if="message.citations?.length" class="citation-row">
                    <span
                      v-for="citation in message.citations"
                      :key="citation"
                      class="citation-pill citation-pill--soft"
                    >{{ citation }}</span>
                  </div>
                  <p v-if="message.llm_mode === 'mock'" class="hint-text mock-note gemini-msg__mock">
                    {{ buildMockNotice(message.mock_reason, 'chat') }}
                  </p>
                </article>
              </transition-group>

              <article
                v-if="chatLoading"
                class="chat-message gemini-msg assistant agent-thinking"
                aria-live="polite"
              >
                <div class="gemini-msg__head">
                  <div class="chat-role">智能体</div>
                  <span class="chat-source-tag chat-source-tag--pending" title="完成后将按本条实际来源标注"
                    >生成中…</span
                  >
                </div>
                <div class="chat-message__body chat-message__body--thinking">
                  {{ thinkingLabel }}
                </div>
              </article>

              <div
                v-if="followupChipsForPanel.length && !chatLoading"
                class="agent-followup-chips"
                aria-label="建议继续追问"
              >
                <span class="agent-followup-chips__label">下一步可问</span>
                <div class="agent-followup-chips__row">
                  <button
                    v-for="(chip, cidx) in followupChipsForPanel"
                    :key="cidx"
                    type="button"
                    class="chip-btn agent-followup-chip"
                    @click="emit('submit-chat', chip)"
                  >
                    {{ chip }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>

    <div class="report-chat-composer-dock" aria-label="智能追问输入区">
      <div class="report-chat-composer">
        <div class="report-chat-composer__row">
          <div class="report-chat-composer__model-wrap">
            <label class="report-chat-composer__model-label" for="report-chat-model-select">回答模型</label>
            <select
              id="report-chat-model-select"
              class="report-chat-composer__model-select"
              :value="selectedModel"
              :disabled="chatLoading || modelSaving"
              aria-describedby="report-chat-model-hint"
              @change="emit('model-change', $event)"
            >
              <option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</option>
            </select>
            <p id="report-chat-model-hint" class="report-chat-composer__model-hint">
              服务端生效：<strong>{{ activeModel || '—' }}</strong>
              <span v-if="modelSaving">（切换中…）</span>
            </p>
          </div>
          <textarea
            :value="chatInput"
            class="report-chat-composer__input"
            placeholder="向智能体提问…（Shift+Enter 换行，Enter 发送）"
            rows="1"
            @input="emit('update:chatInput', $event.target.value)"
            @keydown.enter="onComposerEnter"
          />
          <button
            type="button"
            class="primary-btn report-chat-composer__send"
            :disabled="chatLoading || modelSaving"
            @click="emit('submit-chat', '')"
          >
            {{ chatLoading ? '思考中…' : '发送' }}
          </button>
        </div>
        <p v-if="chatError" class="status-error report-chat-composer__error" role="alert">{{ chatError }}</p>
      </div>
    </div>
  </section>
</template>
