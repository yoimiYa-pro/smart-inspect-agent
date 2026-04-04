import { describe, expect, it } from 'vitest'
import { getErrorMessage } from './errorMessage'

describe('getErrorMessage', () => {
  it('reads Error.message', () => {
    expect(getErrorMessage(new Error('x'), 'f')).toBe('x')
  })

  it('uses fallback when message empty', () => {
    expect(getErrorMessage(new Error('   '), 'fallback')).toBe('fallback')
  })

  it('handles string errors', () => {
    expect(getErrorMessage('plain')).toBe('plain')
  })

  it('handles null', () => {
    expect(getErrorMessage(null, 'fb')).toBe('fb')
  })
})
