import { computed, nextTick, ref, watch } from 'vue'
import {
  askRiskFollowup,
  chatWithContract,
  enhanceReviewContract,
  fetchModelConfig,
  reviewContract,
  updateModelConfig,
} from '../api'
import { ensureReportChatRoute, pushReport, replaceHome } from '../navigate'
import {
  readReviewSession,
  removeReviewSession,
  scheduleReviewSessionPersist,
} from './reviewSessionStorage'
import { getErrorMessage } from '../utils/errorMessage'

export const exampleText = `第一条 服务内容
乙方负责为甲方完成智能巡检平台的开发、部署与上线支持，并提供上线后3个月运维服务。

第二条 费用与支付
合同总金额为人民币80万元。甲方在项目全部上线并最终验收合格后60个工作日内一次性支付全部服务费，付款时间以甲方内部审批结果为准。乙方需先行垫付全部实施成本。

第三条 知识产权
项目产生的全部源代码、接口文档、技术成果及衍生成果自形成之日起永久归甲方所有，甲方无需另行支付任何费用。

第四条 保密与数据
乙方在合作过程中可接触甲方用户数据并配合处理，但双方未约定加密、删除期限和访问控制措施。甲方有权永久无偿使用合作形成的全部数据。

第五条 违约责任
因本项目引发的任何争议、损失或第三方索赔，均由乙方承担全部责任，甲方不承担任何责任。

第六条 合同解除
甲方可根据业务需要随时单方解除合同，无需承担补偿责任。

第七条 争议解决
双方同意，因本合同产生的争议，由甲方所在地人民法院管辖。`

export const roleOptions = ['甲方', '乙方']

export const fallbackModelOptions = [
  'hunyuan-pro',
  'hunyuan-standard',
  'hunyuan-large',
  'hunyuan-turbos-latest',
]

export const suggestedQuestions = ['这份合同安全吗？', '哪些条款最危险？', '我应该注意什么？']

export const levelClassMap = {
  高: 'high',
  中: 'medium',
  低: 'low',
}

export const severityLabelMap = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
}

export const categoryLabelMap = {
  payment: '付款与结算',
  liability: '违约与责任',
  termination: '解除与终止',
  confidentiality: '保密与数据安全',
  intellectual_property: '知识产权',
  dispute: '争议解决',
  delivery: '交付与风险转移',
  quality: '质量保证与质保',
}

const REVIEW_DETAIL_PANEL_ID = 'review-detail-panel'
const REVIEW_CHAT_PANEL_ID = 'review-chat-panel'

function scrollElIntoView(id, block = 'start') {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block })
}

function riskCardElId(riskId) {
  return `risk-card-${riskId}`
}

const contractText = ref(exampleText)
/** 本轮已成功提交审查的合同正文快照；底部输入在成功后清空，追问/对话仍使用此文本。 */
const reviewedContractBody = ref('')
const selectedRole = ref('乙方')
const selectedModel = ref('hunyuan-turbos-latest')
const activeModel = ref('hunyuan-turbos-latest')
const modelOptions = ref([...fallbackModelOptions])
const modelSaving = ref(false)
const useLlm = ref(true)
const loading = ref(false)
/** 0-3：审查加载时示意进度（与后端阶段近似对齐的展示层） */
const loadingPhase = ref(0)
const errorMessage = ref('')
/** 两阶段审查：第一段已返回，第二段 LLM 增强进行中 */
const enhancing = ref(false)
const enhanceError = ref('')
const result = ref(null)
const selectedRiskId = ref('')
const chatInput = ref('')
const chatMessages = ref([])
const chatLoading = ref(false)
const chatError = ref('')

const _sessionSnap = readReviewSession()
if (_sessionSnap) {
  result.value = _sessionSnap.result
  reviewedContractBody.value =
    typeof _sessionSnap.reviewedContractBody === 'string' ? _sessionSnap.reviewedContractBody : ''
  contractText.value = typeof _sessionSnap.contractText === 'string' ? _sessionSnap.contractText : ''
  selectedRiskId.value = typeof _sessionSnap.selectedRiskId === 'string' ? _sessionSnap.selectedRiskId : ''
  if (Array.isArray(_sessionSnap.chatMessages)) {
    chatMessages.value = _sessionSnap.chatMessages
  }
  if (typeof _sessionSnap.selectedRole === 'string') {
    selectedRole.value = _sessionSnap.selectedRole
  }
  if (typeof _sessionSnap.useLlm === 'boolean') {
    useLlm.value = _sessionSnap.useLlm
  }
}

let modelConfigPromise = null
let persistWatchStarted = false

function ensureModelConfigLoaded() {
  if (!modelConfigPromise) {
    modelConfigPromise = (async () => {
      try {
        const config = await fetchModelConfig()
        modelOptions.value = config.available_models?.length ? config.available_models : [...fallbackModelOptions]
        activeModel.value = config.active_model || selectedModel.value
        selectedModel.value = config.active_model || selectedModel.value
      } catch {
        modelOptions.value = [...fallbackModelOptions]
      }
    })()
  }
  return modelConfigPromise
}

const selectedRisk = computed(() => {
  if (!result.value?.risk_items?.length) {
    return null
  }
  return result.value.risk_items.find((item) => item.id === selectedRiskId.value) || result.value.risk_items[0]
})

const riskyClauseIndexes = computed(() => {
  const clauses = result.value?.clauses || []
  const clauseIndexSet = new Set(clauses.map((clause) => clause.index))
  return new Set(
    (result.value?.risk_items || [])
      .map((item) => item.clause_index)
      .filter((index) => Number.isInteger(index) && clauseIndexSet.has(index)),
  )
})

const noRiskClauses = computed(() => {
  const clauses = result.value?.clauses || []
  if (!clauses.length) {
    return []
  }
  return clauses.filter((clause) => !riskyClauseIndexes.value.has(clause.index))
})

const riskyClauseCount = computed(() => riskyClauseIndexes.value.size)
const totalRiskCount = computed(() => result.value?.risk_items?.length || 0)

const groupedRiskSections = computed(() => {
  const riskItems = result.value?.risk_items || []
  if (!riskItems.length) {
    return []
  }
  return [
    {
      key: 'high',
      title: '🚨 高风险',
      emptyText: '暂无高风险项。',
      items: riskItems.filter((item) => item.severity === 'high'),
    },
    {
      key: 'medium',
      title: '🟡 中风险',
      emptyText: '暂无中风险项。',
      items: riskItems.filter((item) => item.severity === 'medium'),
    },
    {
      key: 'low',
      title: '🟢 低风险',
      emptyText: '暂无低风险项。',
      items: riskItems.filter((item) => item.severity === 'low'),
    },
  ]
})

const overallLevelClass = computed(() => levelClassMap[result.value?.overall_risk_level] || 'medium')

const summaryCards = computed(() => {
  if (!result.value) {
    return []
  }
  return [
    {
      icon: '🧠',
      title: 'AI一句话结论',
      value: result.value.one_line_conclusion,
      meta: `角色视角：${result.value.role}`,
      tone: overallLevelClass.value,
    },
    {
      icon: '⚠️',
      title: '合同总体风险结论',
      value: `总体${result.value.overall_risk_level}风险 · ${result.value.signing_advice}签署`,
      meta: result.value.lawyer_suggestion,
      tone: overallLevelClass.value,
    },
    {
      icon: '📊',
      title: '风险评分',
      value: `${result.value.risk_score}/100`,
      meta: result.value.risk_level_text,
      tone: overallLevelClass.value,
      progress: result.value.risk_score,
    },
  ]
})

function setExample() {
  contractText.value = exampleText
}

function sessionContractText() {
  const snap = reviewedContractBody.value
  if (snap) return snap
  return contractText.value
}

function clearAll() {
  contractText.value = ''
  reviewedContractBody.value = ''
  result.value = null
  selectedRiskId.value = ''
  errorMessage.value = ''
  chatInput.value = ''
  chatMessages.value = []
  chatError.value = ''
  removeReviewSession()
  replaceHome()
}

function resetChat(analysisResult) {
  chatMessages.value = analysisResult
    ? [
        {
          role: 'assistant',
          content: `分析完成：${analysisResult.one_line_conclusion}`,
          citations: analysisResult.top_risks?.map((item) => item.title) || [],
          llm_mode: analysisResult.llm_mode,
          mock_reason: analysisResult.mock_reason,
        },
      ]
    : []
}

async function syncModelSelection(targetModel = selectedModel.value, { silent = false } = {}) {
  modelSaving.value = true
  try {
    const config = await updateModelConfig(targetModel)
    modelOptions.value = config.available_models?.length ? config.available_models : [...fallbackModelOptions]
    activeModel.value = config.active_model || targetModel
    selectedModel.value = config.active_model || targetModel
    if (!silent) {
      errorMessage.value = ''
    }
  } finally {
    modelSaving.value = false
  }
}

async function handleModelChange(nextModel) {
  const targetModel = typeof nextModel === 'string' ? nextModel : nextModel?.target?.value || selectedModel.value
  selectedModel.value = targetModel
  try {
    await syncModelSelection(targetModel)
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '模型切换失败，请稍后重试。')
    selectedModel.value = activeModel.value
  }
}

async function submitReview() {
  await ensureModelConfigLoaded()
  if (loading.value) {
    return
  }
  const submittedBody = contractText.value.trim()
  if (!submittedBody) {
    errorMessage.value = '请先输入合同文本。'
    return
  }
  loading.value = true
  loadingPhase.value = 0
  errorMessage.value = ''
  enhanceError.value = ''
  chatInput.value = ''
  chatError.value = ''
  let phaseTimer = setInterval(() => {
    loadingPhase.value = Math.min(loadingPhase.value + 1, 2)
  }, 650)
  try {
    await syncModelSelection(selectedModel.value, { silent: true })
    // 默认单次请求内完成规则 + LLM 增强（与后端 enhance_with_llm 对齐）；两阶段 defer 仅适合显式传 deferLlm: true 的调用方
    const data = await reviewContract(submittedBody, selectedRole.value, useLlm.value, {
      deferLlm: false,
    })
    result.value = data
    selectedRiskId.value = data.risk_items?.[0]?.id || ''
    resetChat(data)
    reviewedContractBody.value = submittedBody
    contractText.value = submittedBody
    pushReport()

    if (useLlm.value && data.llm_mode === 'deferred') {
      clearInterval(phaseTimer)
      phaseTimer = null
      loading.value = false
      loadingPhase.value = 0
      enhancing.value = true
      try {
        const full = await enhanceReviewContract(submittedBody, selectedRole.value)
        result.value = full
        resetChat(full)
        const keep = selectedRiskId.value
        selectedRiskId.value = full.risk_items?.some((x) => x.id === keep) ? keep : full.risk_items?.[0]?.id || ''
      } catch (error) {
        enhanceError.value = getErrorMessage(error, 'LLM 增强失败，当前展示为规则与本地摘要版。')
      } finally {
        enhancing.value = false
      }
      return
    }
  } catch (error) {
    errorMessage.value = getErrorMessage(error, '审查失败，请稍后重试。')
  } finally {
    if (phaseTimer) {
      clearInterval(phaseTimer)
    }
    loading.value = false
    loadingPhase.value = 0
  }
}

async function pickRisk(riskId) {
  selectedRiskId.value = riskId
  await nextTick()
  const card = document.getElementById(riskCardElId(riskId))
  if (card) {
    card.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }
  scrollElIntoView(REVIEW_DETAIL_PANEL_ID, 'center')
}

function getRiskById(riskId) {
  return result.value?.risk_items?.find((item) => item.id === riskId) || null
}

function scrollChatPanelIntoView() {
  scrollElIntoView(REVIEW_CHAT_PANEL_ID, 'start')
}

async function askRiskQuestion(risk) {
  if (!risk) {
    return
  }
  if (chatLoading.value) {
    return
  }
  const fullRisk =
    result.value?.risk_items?.find((item) => item.id === risk.id) || null
  if (!fullRisk) {
    chatError.value = '找不到该风险的完整信息（TOP3 摘要字段不足），请从下方「风险分类」列表中点击对应条目后再提问。'
    return
  }
  const riskPayload = fullRisk
  const question = `请详细解释${riskPayload.clause_index ? `第${riskPayload.clause_index}条` : '该条款'}“${riskPayload.title}”，并告诉我最应该怎么改。`
  const nextMessages = [...chatMessages.value, { role: 'user', content: question }]
  selectedRiskId.value = riskPayload.id
  chatMessages.value = nextMessages
  chatInput.value = ''
  chatLoading.value = true
  chatError.value = ''
  await ensureReportChatRoute()
  await nextTick()
  scrollChatPanelIntoView()
  try {
    const reply = await askRiskFollowup(
      sessionContractText(),
      riskPayload,
      question,
      selectedRole.value,
      useLlm.value,
    )
    chatMessages.value = [
      ...nextMessages,
      {
        role: 'assistant',
        content: reply.answer,
        citations: [riskPayload.title],
        llm_mode: reply.llm_mode,
        mock_reason: reply.mock_reason,
        suggested_followups: Array.isArray(reply.suggested_followups)
          ? reply.suggested_followups
          : [],
      },
    ]
  } catch (error) {
    chatMessages.value = nextMessages
    chatError.value = getErrorMessage(error, '对话失败，请稍后重试。')
  } finally {
    chatLoading.value = false
  }
}

async function submitChat(presetQuestion = '') {
  if (chatLoading.value) {
    return
  }
  if (!result.value) {
    chatError.value = '请先完成合同分析。'
    return
  }
  const question = (presetQuestion || chatInput.value).trim()
  if (!question) {
    chatError.value = '请输入你的问题。'
    return
  }
  const nextMessages = [...chatMessages.value, { role: 'user', content: question }]
  chatMessages.value = nextMessages
  chatInput.value = ''
  chatLoading.value = true
  chatError.value = ''
  try {
    const reply = await chatWithContract(
      sessionContractText(),
      result.value,
      question,
      selectedRole.value,
      nextMessages,
      useLlm.value,
    )
    chatMessages.value = [
      ...nextMessages,
      {
        role: 'assistant',
        content: reply.answer,
        citations: reply.citations || [],
        llm_mode: reply.llm_mode,
        mock_reason: reply.mock_reason,
        suggested_followups: Array.isArray(reply.suggested_followups)
          ? reply.suggested_followups
          : [],
      },
    ]
  } catch (error) {
    chatMessages.value = nextMessages
    chatError.value = getErrorMessage(error, '对话失败，请稍后重试。')
  } finally {
    chatLoading.value = false
  }
}

/** For router guards — shared ref with useContractReview(). */
export { result as reviewResult }

export function useContractReview() {
  ensureModelConfigLoaded()
  if (!persistWatchStarted) {
    persistWatchStarted = true
    watch(
      [result, reviewedContractBody, contractText, selectedRiskId, chatMessages, selectedRole, useLlm],
      () => {
        scheduleReviewSessionPersist(() => {
          if (!result.value) return null
          return {
            result: result.value,
            reviewedContractBody: reviewedContractBody.value,
            contractText: contractText.value,
            selectedRiskId: selectedRiskId.value,
            chatMessages: chatMessages.value,
            selectedRole: selectedRole.value,
            useLlm: useLlm.value,
          }
        })
      },
      { deep: true, immediate: true },
    )
  }
  return {
    contractText,
    reviewedContractBody,
    selectedRole,
    selectedModel,
    activeModel,
    modelOptions,
    modelSaving,
    useLlm,
    loading,
    loadingPhase,
    enhancing,
    enhanceError,
    errorMessage,
    result,
    selectedRiskId,
    selectedRisk,
    chatInput,
    chatMessages,
    chatLoading,
    chatError,
    riskyClauseIndexes,
    noRiskClauses,
    riskyClauseCount,
    totalRiskCount,
    groupedRiskSections,
    overallLevelClass,
    summaryCards,
    setExample,
    clearAll,
    handleModelChange,
    submitReview,
    pickRisk,
    getRiskById,
    askRiskQuestion,
    submitChat,
  }
}
