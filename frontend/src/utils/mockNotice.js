export function buildMockNotice(reason, type = 'analysis') {
  const scene = type === 'chat' ? '当前对话' : '当前分析'
  if (!reason) {
    return `${scene}已切换为 mock 兜底模式。`
  }
  if (reason.includes('未配置') || reason.includes('mock 模式')) {
    return `${scene}未命中可用模型，已切换为 mock 兜底模式。`
  }
  return `${scene}调用真实模型失败，已切换为 mock 兜底模式。`
}
