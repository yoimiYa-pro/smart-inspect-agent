import { reactive } from 'vue'

const state = reactive({
  items: [],
})

let idSeq = 0

export function removeToast(id) {
  const i = state.items.findIndex((t) => t.id === id)
  if (i >= 0) state.items.splice(i, 1)
}

export function pushToast({ message, variant = 'info', duration = 4800 }) {
  const id = ++idSeq
  const text = typeof message === 'string' ? message : String(message ?? '')
  if (!text.trim()) return null
  state.items.push({ id, message: text, variant })
  if (duration > 0) {
    window.setTimeout(() => removeToast(id), duration)
  }
  return id
}

export function useToastState() {
  return state
}
