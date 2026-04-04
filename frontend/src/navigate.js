/** Set from main.js after router is created to avoid circular imports from composables. */
let _router = null

export function setRouter(r) {
  _router = r
}

export function pushReport() {
  _router?.push('/report')
}

export function pushReportChat() {
  _router?.push({ name: 'report-chat' })
}

/** 若当前不在智能追问页则跳转（供追问入口复用，避免与 main 动态 import 循环依赖）。 */
export async function ensureReportChatRoute() {
  if (!_router) return
  if (_router.currentRoute.value.name === 'report-chat') return
  await _router.push({ name: 'report-chat' })
}

export function replaceHome() {
  _router?.replace('/')
}
