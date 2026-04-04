/** 将单次审查结果导出为 Markdown 文本（便于粘贴到文档或工单）。 */
export function buildReviewMarkdown(result) {
  if (!result) {
    return ''
  }
  const lines = [
    `# 合同审查摘要`,
    ``,
    `- 视角：${result.role}`,
    `- 合同类型：${result.contract_type}`,
    `- 总体风险：${result.overall_risk_level}（${result.risk_level_text}）`,
    `- 评分：${result.risk_score}/100`,
    `- 结论：${result.one_line_conclusion}`,
    ``,
    `## 风险提示`,
    ``,
    ...(result.review_highlights || []).map((h) => `- ${h}`),
    ``,
    `## 风险条目（${(result.risk_items || []).length}）`,
    ``,
  ]
  for (const item of result.risk_items || []) {
    lines.push(
      `### ${item.title}`,
      ``,
      `- 等级：${item.risk_level_text} · 条款：${item.clause_index ?? '—'}`,
      `- 说明：${item.plain_explanation}`,
      `- 建议：${item.suggestion}`,
      ``,
    )
  }
  return lines.join('\n')
}

export function downloadTextFile(filename, text) {
  const blob = new Blob([text], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
