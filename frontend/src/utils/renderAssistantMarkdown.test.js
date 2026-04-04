import { describe, expect, it, vi } from 'vitest'

vi.mock('dompurify', () => ({
  default: {
    sanitize: (html) =>
      String(html)
        .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/on\w+\s*=\s*["'][^"']*["']/gi, ''),
  },
}))

const { renderAssistantMarkdown } = await import('./renderAssistantMarkdown.js')

describe('renderAssistantMarkdown', () => {
  it('renders bold from markdown', () => {
    const html = renderAssistantMarkdown('**hi**')
    expect(html).toContain('<strong>')
    expect(html).toContain('hi')
  })

  it('returns empty for null', () => {
    expect(renderAssistantMarkdown(null)).toBe('')
  })
})
