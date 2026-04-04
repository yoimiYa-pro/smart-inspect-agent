import { describe, expect, it } from 'vitest'
import { formatApiErrorDetail } from './api.js'

describe('formatApiErrorDetail', () => {
  it('joins pydantic-style validation array', () => {
    const detail = [
      { type: 'missing', loc: ['body', 'risk'], msg: 'field required' },
      { type: 'string_too_short', loc: ['body', 'question'], msg: 'too short' },
    ]
    const out = formatApiErrorDetail(detail)
    expect(out).toContain('field required')
    expect(out).toContain('too short')
    expect(out).toMatch(/；/)
  })

  it('returns string as-is', () => {
    expect(formatApiErrorDetail('bad')).toBe('bad')
  })
})
