/**
 * 去掉 API 返回标题里常见的 <em> 等高亮标签（纯文本展示，避免 v-html XSS）。
 * @param {unknown} s
 * @param {{ collapseWs?: boolean }} [opts] collapseWs 为 false 时保留换行（长正文）
 */
export function stripHtmlTags(s, opts = {}) {
  if (s == null || typeof s !== 'string') return s
  const { collapseWs = true } = opts
  let out = s.replace(/<[^>]+>/g, '')
  if (collapseWs) {
    out = out.replace(/\s+/g, ' ').trim()
  }
  return out
}
