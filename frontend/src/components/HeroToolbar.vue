<script setup>
import { RouterLink } from 'vue-router'
import { roleOptions } from '../composables/useContractReview'

defineProps({
  variant: {
    type: String,
    default: 'full',
    validator: (v) => v === 'full' || v === 'workspace' || v === 'help',
  },
  modelOptions: { type: Array, required: true },
  selectedRole: { type: String, required: true },
  selectedModel: { type: String, required: true },
  activeModel: { type: String, required: true },
  useLlm: { type: Boolean, required: true },
  modelSaving: { type: Boolean, required: true },
  loading: { type: Boolean, required: true },
})

defineEmits(['update:selectedRole', 'update:useLlm', 'model-change', 'set-example', 'clear-all', 'submit-review'])
</script>

<template>
  <header
    class="hero-card"
    :class="{
      'hero-card--compact': variant === 'workspace' || variant === 'help',
      'hero-card--workspace-minimal': variant === 'workspace',
    }"
  >
    <template v-if="variant === 'full'">
      <div class="hero-copy">
        <p class="eyebrow">合同审查 · 角色视角 · 风险优先</p>
        <h1>智能合同审查助手</h1>
        <p class="hero-desc">
          粘贴合同文本后开始审查：条款切分、规则与模型分析、结构化报告；结果在<strong>报告页</strong>集中展示，并支持针对风险条款继续提问。
        </p>

        <div class="input-tips-box hero-tips-box">
          <h4>审查提示</h4>
          <ul class="hero-tips-list">
            <li>系统支持针对不同身份立场执行<strong>双向独立审查</strong>。</li>
            <li>模型异常时会自动 fallback，审查流程可继续。</li>
            <li>建议使用分段清晰、无乱码的合同正文，结果更稳。</li>
          </ul>
        </div>
      </div>

      <div class="hero-actions">
        <div class="control-grid">
          <label class="control-field">
            <span>审查视角</span>
            <select
              :value="selectedRole"
              class="select-input"
              @change="$emit('update:selectedRole', $event.target.value)"
            >
              <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
            </select>
          </label>

          <label class="control-field">
            <span>审查模型</span>
            <select
              :value="selectedModel"
              class="select-input"
              :disabled="modelSaving || loading"
              @change="$emit('model-change', $event)"
            >
              <option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</option>
            </select>
          </label>

          <label class="switch-row">
            <input :checked="useLlm" type="checkbox" @change="$emit('update:useLlm', $event.target.checked)" />
            <span>优先调用真实模型，失败自动 fallback 到 mock</span>
          </label>
        </div>

        <p class="hint-text">当前生效模型：{{ activeModel }}<span v-if="modelSaving">（切换中...）</span></p>

        <div class="button-row">
          <button type="button" class="secondary-btn" @click="$emit('set-example')">填充示例</button>
          <button type="button" class="ghost-btn" @click="$emit('clear-all')">清空</button>
          <button type="button" class="primary-btn" :disabled="loading || modelSaving" @click="$emit('submit-review')">
            {{ loading ? '审查中...' : '开始审查' }}
          </button>
        </div>
      </div>
    </template>

    <template v-else-if="variant === 'workspace'">
      <div class="hero-compact hero-workspace hero-workspace--minimal">
        <div class="hero-compact__lead">
          <h2 class="hero-workspace__minimal-title">智能合同审查</h2>
          <p class="hero-workspace__minimal-hint">
            在底部输入框粘贴正文，用右侧圆形按钮开始审查。视角、模型与 API 在输入框下方一行即可调整。更多说明见
            <RouterLink class="text-link hero-workspace__inline-link" :to="{ name: 'help' }">使用说明</RouterLink>。
          </p>
        </div>
      </div>
    </template>

    <template v-else-if="variant === 'help'">
      <div class="hero-compact hero-workspace">
        <div class="hero-compact__lead">
          <p class="eyebrow hero-workspace__eyebrow">使用说明</p>
          <h2 class="hero-compact__title">操作指引与风险提示</h2>
          <p class="hero-compact__hint">
            正式审查在
            <RouterLink class="text-link hero-workspace__inline-link" :to="{ name: 'review' }">合同与审查</RouterLink>
            完成；本页为步骤说明、mock 与隐私提示。修改模型与视角请前往<strong>合同与审查</strong>，在底部悬浮式输入药丸内调整。
          </p>
        </div>

        <details class="hero-workspace__tips">
          <summary class="hero-compact__summary">快速要点（展开）</summary>
          <div class="hero-workspace__tips-body input-tips-box">
            <ul class="hero-tips-list hero-workspace__tips-list">
              <li>粘贴合同全文后选择视角与模型，再开始审查。</li>
              <li>未配置密钥或模型不可用时会走 mock，界面会有提示。</li>
              <li>请勿粘贴涉密或超出授权范围的正文。</li>
            </ul>
          </div>
        </details>

        <div class="hero-compact__toolbar hero-compact__toolbar--chips-only">
          <div class="hero-compact__chips" aria-label="当前审查条件摘要">
            <span class="hero-compact__chip">视角 {{ selectedRole }}</span>
            <span class="hero-compact__chip">模型 {{ selectedModel }}</span>
            <span class="hero-compact__chip">{{ useLlm ? '优先真实 API' : '允许 mock' }}</span>
          </div>
        </div>

        <details class="hero-compact__details">
          <summary class="hero-compact__summary">调整审查条件</summary>
          <div class="hero-compact__panel">
            <div class="control-grid">
              <label class="control-field">
                <span>审查视角</span>
                <select
                  :value="selectedRole"
                  class="select-input"
                  @change="$emit('update:selectedRole', $event.target.value)"
                >
                  <option v-for="role in roleOptions" :key="role" :value="role">{{ role }}</option>
                </select>
              </label>

              <label class="control-field">
                <span>审查模型</span>
                <select
                  :value="selectedModel"
                  class="select-input"
                  :disabled="modelSaving || loading"
                  @change="$emit('model-change', $event)"
                >
                  <option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</option>
                </select>
              </label>

              <label class="switch-row switch-row--compact">
                <input :checked="useLlm" type="checkbox" @change="$emit('update:useLlm', $event.target.checked)" />
                <span title="优先调用真实大模型接口；失败时自动 fallback 到 mock，审查仍可完成">优先真实模型（失败自动 fallback mock）</span>
              </label>
            </div>
            <p class="hint-text hero-compact__model-hint">
              当前生效模型：{{ activeModel }}<span v-if="modelSaving">（切换中...）</span>
            </p>
            <div class="button-row hero-workspace__utility-row">
              <button type="button" class="secondary-btn" @click="$emit('set-example')">填充示例</button>
              <button type="button" class="ghost-btn" @click="$emit('clear-all')">清空</button>
            </div>
          </div>
        </details>
      </div>
    </template>
  </header>
</template>
