import { describe, expect, it } from 'vitest'
import { buildAgentFollowupChats } from './agentSuggestions.js'

describe('buildAgentFollowupChats', () => {
  it('returns up to 4 unique strings', () => {
    const result = {
      role: '乙方',
      top_risks: [{ title: '付款风险' }],
      signing_advice: '谨慎',
      risk_items: [{ id: '1' }, { id: '2' }],
    }
    const selectedRisk = { title: '单方解除' }
    const out = buildAgentFollowupChats({
      result,
      selectedRisk,
      lastUserContent: '你好',
    })
    expect(out.length).toBeGreaterThanOrEqual(2)
    expect(out.length).toBeLessThanOrEqual(4)
    expect(new Set(out).size).toBe(out.length)
  })

  it('works with minimal result', () => {
    const out = buildAgentFollowupChats({
      result: null,
      selectedRisk: null,
      lastUserContent: '',
    })
    expect(out.length).toBeGreaterThanOrEqual(2)
  })
})
