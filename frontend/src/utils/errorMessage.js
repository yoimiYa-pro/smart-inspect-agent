/**
 * @param {unknown} error
 * @param {string} [fallback]
 */
export function getErrorMessage(error, fallback = '操作失败，请稍后重试。') {
  if (error == null) return fallback
  if (typeof error === 'string') {
    const t = error.trim()
    return t || fallback
  }
  const msg = error?.message
  if (typeof msg === 'string') {
    const t = msg.trim()
    if (t) return t
  }
  return fallback
}
