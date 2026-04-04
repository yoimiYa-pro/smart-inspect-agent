const KEY = 'smart-inspect-agent:review-session-v1'
const MAX_CHARS = 4_000_000
const DEBOUNCE_MS = 400

let persistTimer = null

export function removeReviewSession() {
  try {
    sessionStorage.removeItem(KEY)
  } catch {
    /* ignore quota / private mode */
  }
}

export function readReviewSession() {
  try {
    const raw = sessionStorage.getItem(KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    if (!data || data.v !== 1 || !data.result) return null
    return data
  } catch {
    return null
  }
}

export function writeReviewSessionNow(payload) {
  try {
    const str = JSON.stringify({ v: 1, ...payload, savedAt: Date.now() })
    if (str.length > MAX_CHARS) return false
    sessionStorage.setItem(KEY, str)
    return true
  } catch {
    return false
  }
}

export function scheduleReviewSessionPersist(buildPayload) {
  if (persistTimer) clearTimeout(persistTimer)
  persistTimer = window.setTimeout(() => {
    persistTimer = null
    const payload = buildPayload()
    if (!payload) {
      removeReviewSession()
      return
    }
    writeReviewSessionNow(payload)
  }, DEBOUNCE_MS)
}
