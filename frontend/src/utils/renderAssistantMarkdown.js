import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
})

/**
 * 将助手纯文本转为可安全展示的 HTML（Markdown 子集 + 净化）。
 * @param {string} text
 * @returns {string}
 */
export function renderAssistantMarkdown(text) {
  if (text == null || text === '') return ''
  const raw = md.render(String(text))
  return DOMPurify.sanitize(raw, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'b', 'i', 'ul', 'ol', 'li', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'a'],
    ALLOWED_ATTR: ['href', 'class'],
  })
}
