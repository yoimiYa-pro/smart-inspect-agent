import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  readReviewSession,
  removeReviewSession,
  writeReviewSessionNow,
} from './reviewSessionStorage.js'

const KEY = 'smart-inspect-agent:review-session-v1'
const mem = new Map()

beforeEach(() => {
  mem.clear()
  vi.stubGlobal('sessionStorage', {
    getItem: (k) => (mem.has(k) ? mem.get(k) : null),
    setItem: (k, v) => mem.set(k, String(v)),
    removeItem: (k) => mem.delete(k),
  })
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('reviewSessionStorage', () => {
  it('round-trips minimal v1 payload', () => {
    const payload = {
      result: { one_line_conclusion: 'ok', risk_items: [] },
      reviewedContractBody: 'body',
      contractText: 'body',
      selectedRiskId: 'r1',
      chatMessages: [{ role: 'assistant', content: 'hi' }],
      selectedRole: '乙方',
      useLlm: true,
    }
    expect(writeReviewSessionNow(payload)).toBe(true)
    const read = readReviewSession()
    expect(read?.result?.one_line_conclusion).toBe('ok')
    expect(read?.reviewedContractBody).toBe('body')
    expect(read?.chatMessages).toHaveLength(1)
  })

  it('removeReviewSession clears key', () => {
    writeReviewSessionNow({ result: { x: 1 } })
    removeReviewSession()
    expect(readReviewSession()).toBeNull()
  })
})
