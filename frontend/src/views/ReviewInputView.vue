<script setup>
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import ContractInputPanel from '../components/ContractInputPanel.vue'
import LoadingSkeleton from '../components/LoadingSkeleton.vue'
import ReviewPipelineProgress from '../components/ReviewPipelineProgress.vue'
import { useContractReview } from '../composables/useContractReview'

const {
  contractText,
  reviewedContractBody,
  errorMessage,
  selectedRole,
  selectedModel,
  activeModel,
  modelOptions,
  modelSaving,
  useLlm,
  loading,
  loadingPhase,
  result,
  handleModelChange,
  setExample,
  clearAll,
  submitReview,
} = useContractReview()

function setContractText(v) {
  contractText.value = v
}

function setSelectedRole(v) {
  selectedRole.value = v
}

function setUseLlm(v) {
  useLlm.value = v
}

const reviewedCharCount = computed(() => [...reviewedContractBody.value].length)

const pendingContractPreview = computed(() => contractText.value.trim())
</script>

<template>
  <div class="workspace-page review-workspace-page">
    <div class="review-workspace-page__main panel-stack">
      <template v-if="loading">
        <div class="panel-stack loading-panel-stack review-loading-stack">
          <div class="review-loading-layout">
            <div class="review-loading-layout__main">
              <section
                v-if="pendingContractPreview"
                class="panel-card report-reviewing-doc"
                aria-busy="true"
                aria-label="正在审查的合同正文"
              >
                <div class="report-ready-contract__head">
                  <span class="report-ready-contract__label">正在审查的合同正文</span>
                  <span class="report-ready-contract__meta" aria-live="polite">共 {{ [...contractText].length }} 字</span>
                </div>
                <div
                  class="report-ready-contract__body report-ready-contract__body--primary"
                  tabindex="0"
                  role="region"
                >
                  {{ contractText }}
                </div>
              </section>
              <LoadingSkeleton v-if="!pendingContractPreview" />
            </div>
            <aside class="review-loading-layout__rail" aria-label="审查进度">
              <ReviewPipelineProgress :active-step="loadingPhase" />
            </aside>
          </div>
        </div>
      </template>
      <section v-else-if="result" class="panel-card report-ready-card">
        <div v-if="reviewedContractBody" class="report-ready-contract report-ready-contract--primary">
          <div class="report-ready-contract__head">
            <span class="report-ready-contract__label">本轮审查的合同正文</span>
            <span class="report-ready-contract__meta" aria-live="polite">共 {{ reviewedCharCount }} 字</span>
          </div>
          <div
            class="report-ready-contract__body report-ready-contract__body--primary"
            tabindex="0"
            role="region"
            aria-label="本轮已审查的合同正文，可在框内滚动阅读"
          >
            {{ reviewedContractBody }}
          </div>
        </div>

        <div class="report-ready-hero report-ready-hero--footer">
          <div class="report-ready-icon" aria-hidden="true">✓</div>
          <div class="report-ready-hero__mid">
            <h2>本轮审查已完成</h2>
            <p class="report-ready-lead">{{ result.one_line_conclusion }}</p>
          </div>
          <RouterLink class="primary-btn report-ready-btn" to="/report">查看完整审查报告</RouterLink>
        </div>
      </section>
      <section v-else class="panel-card review-workspace-hint">
        <h2 class="review-workspace-hint__title">准备审查</h2>
        <p class="review-workspace-hint__lead">
          在页面底部<strong>悬浮式输入框</strong>粘贴合同正文；视角、模型与「API」选项在同一药丸卡片的底部一行；编辑完成后点击<strong>右侧蓝色圆形按钮</strong>开始审查。
        </p>
        <p class="review-workspace-hint__sub">
          操作说明见
          <RouterLink class="text-link" :to="{ name: 'help' }">使用说明</RouterLink>
          。
        </p>
      </section>
    </div>

    <div class="review-composer-dock" aria-label="合同输入">
      <ContractInputPanel
        :contract-text="contractText"
        :error-message="errorMessage"
        :selected-role="selectedRole"
        :selected-model="selectedModel"
        :active-model="activeModel"
        :model-options="modelOptions"
        :use-llm="useLlm"
        :loading="loading"
        :model-saving="modelSaving"
        @update:contract-text="setContractText"
        @update:selected-role="setSelectedRole"
        @update:use-llm="setUseLlm"
        @model-change="handleModelChange"
        @set-example="setExample"
        @clear-all="clearAll"
        @submit-review="submitReview"
      />
    </div>
  </div>
</template>
