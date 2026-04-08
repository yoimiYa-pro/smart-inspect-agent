<script setup>
import { buildMockNotice } from '../utils/mockNotice'

defineProps({
  result: { type: Object, required: true },
  summaryCards: { type: Array, required: true },
  overallLevelClass: { type: String, required: true },
})
</script>

<template>
  <div id="review-section-summary" class="review-section-anchor">
    <section class="summary-grid">
      <article
        v-for="card in summaryCards"
        :key="card.title"
        class="summary-tile"
        :class="card.tone"
      >
        <div class="tile-head">
          <span class="tile-icon" aria-hidden="true">{{ card.icon }}</span>
          <strong>{{ card.title }}</strong>
        </div>
        <p class="tile-value">{{ card.value }}</p>
        <p class="tile-meta">{{ card.meta }}</p>
        <div v-if="card.progress !== undefined" class="score-track">
          <div class="score-fill" :style="{ width: `${card.progress}%` }"></div>
        </div>
      </article>
    </section>

    <section class="panel-card">
      <div class="section-head compact">
        <div>
          <h2>核心结论</h2>
          <p>{{ result.summary }}</p>
        </div>
        <div class="badge-row">
          <span class="mode-badge" :class="result.llm_mode">{{ result.llm_mode }}</span>
          <span class="level-badge" :class="overallLevelClass">{{ result.overall_risk_level }}风险</span>
        </div>
      </div>

      <div class="meta-grid">
        <article class="meta-card emphasis">
          <strong>角色视角判断</strong>
          <p>
            对{{ result.role }}
            <span :class="result.role_analysis.is_unfavorable ? 'warning-text' : 'safe-text'">
              {{ result.role_analysis.is_unfavorable ? '明显不利' : '暂无明显单边失衡' }}
            </span>
          </p>
          <ul>
            <li v-for="item in result.role_analysis.biggest_risks" :key="item">{{ item }}</li>
          </ul>
        </article>

        <article class="meta-card">
          <strong>如果只能改3条</strong>
          <p>{{ result.priority_notice }}</p>
          <ul>
            <li v-for="item in result.top_risks" :key="item.id">
              #{{ item.priority_rank }} {{ item.title }}
            </li>
          </ul>
        </article>

        <article class="meta-card">
          <strong>签约建议</strong>
          <p>{{ result.signing_advice }}签署</p>
          <p>{{ result.lawyer_suggestion }}</p>
          <p class="hint-text">识别依据：{{ result.contract_type }} / {{ result.contract_type_reason }}</p>
          <p v-if="result.llm_mode === 'mock'" class="hint-text mock-note">
            {{ buildMockNotice(result.mock_reason, 'analysis') }}
          </p>
        </article>
      </div>
    </section>
  </div>
</template>
