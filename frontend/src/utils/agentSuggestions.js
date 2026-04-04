/**
 * 规则驱动的下一步追问（无额外 LLM 调用）；与后端 suggested_followups 并存时以后端优先。
 * @param {{
 *   result: object | null
 *   selectedRisk: object | null
 *   lastUserContent?: string
 * }} opts
 * @returns {string[]}
 */
export function buildAgentFollowupChats({ result, selectedRisk, lastUserContent = '' }) {
  const out = []
  const role = result?.role ? String(result.role) : '乙方'
  const q = (lastUserContent || '').slice(0, 80)

  if (selectedRisk?.title) {
    out.push(`用一句话概括「${String(selectedRisk.title).slice(0, 36)}」对我方（${role}）的最坏影响。`)
    out.push(`如果我是${role}，和甲方谈这一条时，开场白怎么说不激化矛盾？`)
  }

  if (result?.top_risks?.length && out.length < 4) {
    const t = result.top_risks[0]?.title
    if (t && !out.some((s) => s.includes(String(t).slice(0, 12)))) {
      out.push(`除了「${String(t).slice(0, 28)}」，本轮报告里还有哪一条最值得一起关注？`)
    }
  }

  if (result?.signing_advice && out.length < 4) {
    out.push(`结合当前「${String(result.signing_advice).slice(0, 20)}」结论，签前我还应核对哪些条款？`)
  }

  if (q && out.length < 4) {
    out.push(`刚才的问题里，哪些是法律依据、哪些只是实务建议？请分开说明。`)
  }

  if (out.length < 2) {
    out.push(`把本轮合同风险按「必须改 / 可以谈 / 可接受」三档帮我分一下。`)
    out.push(`若只能改三条，应该先改哪三条？`)
  }

  return [...new Set(out)].slice(0, 4)
}
