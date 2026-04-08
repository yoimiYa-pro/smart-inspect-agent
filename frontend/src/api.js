const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 120000
const DEFAULT_RETRIES = 1

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export function formatApiErrorDetail(detail) {
  if (detail == null) return '请求失败'
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item == null) return ''
        if (typeof item === 'string') return item
        if (typeof item === 'object' && 'msg' in item) return String(item.msg)
        if (typeof item === 'object' && 'message' in item) return String(item.message)
        try {
          return JSON.stringify(item)
        } catch {
          return String(item)
        }
      })
      .filter(Boolean)
      .join('；')
  }
  if (typeof detail === 'object') {
    if ('msg' in detail) return String(detail.msg)
    if ('message' in detail) return String(detail.message)
    try {
      return JSON.stringify(detail)
    } catch {
      return '请求失败'
    }
  }
  return String(detail)
}

async function request(path, options = {}, fetchOptions = {}) {
  const timeoutMs = fetchOptions.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const retries = fetchOptions.retries ?? DEFAULT_RETRIES

  let lastErr
  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const response = await fetch(`${API_BASE}${path}`, {
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
        signal: controller.signal,
        ...options,
      })

      if (!response.ok) {
        let detail = '请求失败'
        const text = await response.text()
        try {
          const error = JSON.parse(text)
          detail = formatApiErrorDetail(error.detail ?? error.message ?? error)
        } catch {
          detail = text || '请求失败'
        }
        throw new Error(detail)
      }

      return response.json()
    } catch (err) {
      lastErr = err
      const isAbort = err?.name === 'AbortError'
      const msg = String(err?.message || '')
      const maybeNetwork = isAbort || /network|fetch|Failed to fetch/i.test(msg)
      if (attempt < retries && maybeNetwork) {
        await delay(400 * (attempt + 1))
        continue
      }
      if (isAbort) {
        throw new Error('请求超时，请稍后重试或缩短合同长度。')
      }
      throw err
    } finally {
      clearTimeout(timer)
    }
  }
  throw lastErr
}

export function fetchModelConfig() {
  return request('/api/model-config')
}

export function updateModelConfig(modelName) {
  return request('/api/model-config', {
    method: 'POST',
    body: JSON.stringify({
      model_name: modelName,
    }),
  })
}

/**
 * @param {string} text
 * @param {string} [role]
 * @param {boolean} [enhanceWithLlm]
 * @param {{ deferLlm?: boolean, timeoutMs?: number, retries?: number }} [options]
 */
export function reviewContract(text, role = '乙方', enhanceWithLlm = true, options = {}) {
  const { deferLlm = false, timeoutMs, retries } = options
  return request(
    '/api/review',
    {
      method: 'POST',
      body: JSON.stringify({
        text,
        role,
        enhance_with_llm: enhanceWithLlm,
        defer_llm: deferLlm,
      }),
    },
    { timeoutMs, retries },
  )
}

export function enhanceReviewContract(text, role = '乙方', options = {}) {
  const { timeoutMs, retries } = options
  return request(
    '/api/review/enhance',
    {
      method: 'POST',
      body: JSON.stringify({ text, role }),
    },
    { timeoutMs, retries },
  )
}

export function askRiskFollowup(contractText, risk, question, role = '乙方', enhanceWithLlm = true, fetchOpts = {}) {
  return request(
    '/api/followup',
    {
      method: 'POST',
      body: JSON.stringify({
        contract_text: contractText,
        risk,
        question,
        role,
        enhance_with_llm: enhanceWithLlm,
      }),
    },
    fetchOpts,
  )
}

export function chatWithContract(
  contractText,
  analysis,
  question,
  role = '乙方',
  messages = [],
  enhanceWithLlm = true,
  fetchOpts = {},
) {
  return request(
    '/api/chat',
    {
      method: 'POST',
      body: JSON.stringify({
        contract_text: contractText,
        analysis,
        question,
        role,
        messages,
        enhance_with_llm: enhanceWithLlm,
      }),
    },
    fetchOpts,
  )
}

/**
 * @param {string} lawId
 * @param {{ merge?: boolean, timeoutMs?: number }} [fetchOpts]
 */
export function fetchDelilegalLawDetail(lawId, fetchOpts = {}) {
  const merge = fetchOpts.merge !== false
  const q = merge ? '?merge=true' : '?merge=false'
  return request(
    `/api/laws/delilegal/${encodeURIComponent(lawId)}${q}`,
    { method: 'GET' },
    fetchOpts,
  )
}
