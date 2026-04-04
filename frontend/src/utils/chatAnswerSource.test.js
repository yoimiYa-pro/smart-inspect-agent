import { describe, expect, it } from 'vitest'
import { getChatAnswerSource } from './chatAnswerSource'

describe('getChatAnswerSource', () => {
  it('live → 大模型', () => {
    const s = getChatAnswerSource({ llm_mode: 'live' })
    expect(s.variant).toBe('live')
    expect(s.label).toContain('大模型')
  })

  it('mock → 本地兜底', () => {
    const s = getChatAnswerSource({ llm_mode: 'mock' })
    expect(s.variant).toBe('mock')
    expect(s.label).toContain('本地')
  })

  it('rules_only / deferred → 审查摘要类', () => {
    expect(getChatAnswerSource({ llm_mode: 'rules_only' }).variant).toBe('rules')
    expect(getChatAnswerSource({ llm_mode: 'deferred' }).variant).toBe('rules')
  })
})
