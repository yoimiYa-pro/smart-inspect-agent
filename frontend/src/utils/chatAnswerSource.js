/**
 * 智能追问 / 条款追问中，助手消息的「回答来源」展示（基于后端 llm_mode）。
 * @param {{ llm_mode?: string }} message
 * @returns {{ label: string, variant: 'live' | 'mock' | 'rules' | 'unknown', title: string }}
 */
export function getChatAnswerSource(message) {
  const mode = String(message?.llm_mode ?? '')
    .trim()
    .toLowerCase()

  if (mode === 'live') {
    return {
      label: '大模型回答',
      variant: 'live',
      title: '本条由当前配置的 API 模型生成。',
    }
  }
  if (mode === 'mock') {
    return {
      label: '本地兜底',
      variant: 'mock',
      title: '未使用或未成功调用大模型：由本地规则与模板生成，仅供示意。',
    }
  }
  if (mode === 'rules_only' || mode === 'deferred') {
    return {
      label: '审查结论摘要',
      variant: 'rules',
      title: '来自本轮审查结果（规则/结构化摘要），并非本条单独发起的大模型对话输出。',
    }
  }
  if (!mode) {
    return {
      label: '来源未标注',
      variant: 'unknown',
      title: '缺少 llm_mode 字段，无法判断来源。',
    }
  }
  return {
    label: `来源：${message.llm_mode}`,
    variant: 'unknown',
    title: '非预期的 llm_mode，请以后端约定为准。',
  }
}
