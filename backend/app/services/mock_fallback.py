from __future__ import annotations

from typing import Any

CATEGORY_LABELS = {
    "payment": "付款与结算",
    "liability": "违约与责任",
    "termination": "解除与终止",
    "confidentiality": "保密与数据安全",
    "intellectual_property": "知识产权",
    "dispute": "争议解决",
}

CATEGORY_HINTS = {
    "payment": "优先锁定付款节点、开票条件、逾期责任和验收标准。",
    "liability": "优先锁定责任边界、赔偿范围、免责条件和责任上限。",
    "termination": "优先锁定解除条件、通知期限、结算方式和交接义务。",
    "confidentiality": "优先锁定保密范围、数据安全措施、返还删除和违约责任。",
    "intellectual_property": "优先锁定成果归属、背景技术保留、源码交付和授权边界。",
    "dispute": "优先锁定唯一争议解决路径和中立管辖地。",
}

CLAUSE_TEMPLATES = {
    "payment": "示例：甲方应在乙方提交合法有效发票且对应阶段成果验收通过后10个工作日内支付该阶段款项；逾期超过15日的，按未付款项每日万分之五支付违约金。",
    "liability": "示例：除故意或重大过失外，任何一方仅对其违约直接造成的实际损失承担赔偿责任，累计赔偿总额以已支付合同金额为上限。",
    "termination": "示例：任何一方拟提前解除合同的，应至少提前30日书面通知对方，并就已完成工作量、已发生合理成本和资料交接进行结算。",
    "confidentiality": "示例：双方应对保密信息和个人信息采取加密、访问控制、最小必要和留痕审计措施；合作结束后15日内完成返还或删除。",
    "intellectual_property": "示例：项目成果知识产权在甲方付清全部价款后按约转移；乙方预先拥有的工具、通用组件和背景技术仍归乙方所有。",
    "dispute": "示例：因本合同产生的争议，双方应先友好协商；协商不成的，提交合同签订地有管辖权的人民法院处理。",
}


def _as_risk_dict(item: Any) -> dict[str, Any]:
    return item if isinstance(item, dict) else {}


def build_followup_hint(risk: dict[str, Any]) -> str:
    return CATEGORY_HINTS.get(risk.get("category", ""), "建议继续围绕触发条件、责任边界和补救措施追问。")



def build_mock_summary_text(
    contract_type: str,
    role: str,
    overall_risk_level: str,
    signing_advice: str,
    priority_notice: str,
    top_titles: list[str],
) -> str:
    title_text = "；".join(top_titles[:3]) if top_titles else "暂未命中强风险规则，但仍建议复核付款、责任和争议条款"
    return (
        f"系统已按“条款切分 → 规则识别 → 结构化分析”流程完成对“{contract_type}”的审查。"
        f"从{role}视角看，合同整体风险为“{overall_risk_level}”，签约建议为“{signing_advice}”。"
        f"当前最值得优先处理的问题包括：{title_text}。{priority_notice}"
    )



def build_clause_template(category: str) -> str:
    return CLAUSE_TEMPLATES.get(category, "建议补充更清晰的权利义务、违约责任和争议处理条款。")



def answer_with_mock(risk: dict[str, Any], question: str, role: str) -> str:
    template = build_clause_template(risk.get("category", ""))
    clause_index = risk.get("clause_index")
    clause_label = f"第{clause_index}条" if clause_index else "相关条款"
    return (
        f"从{role}视角看，{clause_label}的核心问题是“{risk.get('title', '风险条款')}”。"
        f"法律判断上，主要因为：{risk.get('reason') or risk.get('issue') or '该条款责任边界不清'}。"
        f"通俗来说，这意味着：{risk.get('plain_explanation') or risk.get('issue') or '后续履约和回款可能失控'}。"
        f"如果你问“{question}”，当前最可执行的处理是：{risk.get('suggestion') or risk.get('role_advice') or '补充更明确的保护条款'}。"
        f"可直接参考这类改法：{template}"
    )



def answer_contract_chat_with_mock(
    question: str,
    analysis: dict[str, Any],
    messages: list[dict[str, Any]] | None,
    role: str,
) -> dict[str, Any]:
    risk_items = analysis.get("risk_items", [])
    top_risks = analysis.get("top_risks", [])
    one_line = analysis.get("one_line_conclusion", "")
    overall = analysis.get("overall_risk_level", "中")
    signing_advice = analysis.get("signing_advice", "谨慎")
    priority_notice = analysis.get("priority_notice", "")
    recent_messages = messages or []
    last_msg = recent_messages[-1] if recent_messages else None
    recent_question = (
        str(last_msg.get("content") or "").strip() if isinstance(last_msg, dict) else ""
    )
    q = question.strip()

    if "安全" in q:
        answer = (
            f"结论先说：{one_line or f'这份合同从{role}视角整体为{overall}风险，建议{signing_advice}签署。'}"
            f"目前最危险的集中在：{'；'.join(_as_risk_dict(item).get('title', '') for item in top_risks[:3]) or '付款、责任和解除条款'}。"
            f"{priority_notice}"
        )
    elif "最危险" in q or "top3" in q or "前三" in q:
        answer = (
            "当前优先级最高的3项是："
            + "；".join(
                f"{_as_risk_dict(item).get('title', '风险项')}（优先级#{_as_risk_dict(item).get('priority_rank', '-') }）"
                for item in top_risks[:3]
            )
            + "。建议先把这些条款谈妥，再决定是否继续推进签署。"
        )
    elif "注意" in q or "留意" in q:
        if not top_risks:
            answer = (
                f"从{role}视角，结合当前分析整体风险为“{overall}”。"
                f"{one_line or '建议重点核对付款、违约责任、解除与争议解决等核心条款，必要时请律师复核。'}"
                f"{priority_notice}"
            )
        else:
            r0 = _as_risk_dict(top_risks[0])
            r1 = _as_risk_dict(top_risks[1]) if len(top_risks) > 1 else {}
            r2 = _as_risk_dict(top_risks[2]) if len(top_risks) > 2 else {}
            answer = (
                f"从{role}视角，最需要注意三件事："
                f"1）{r0.get('suggestion', '先改付款条件')}；"
                f"2）{r1.get('suggestion', '再收紧责任边界') if len(top_risks) > 1 else '再补齐违约责任'}；"
                f"3）{r2.get('suggestion', '最后明确解除与争议条款') if len(top_risks) > 2 else '最后确认争议解决机制'}。"
            )
    else:
        reference_titles = (
            "；".join(_as_risk_dict(item).get("title", "") for item in top_risks[:2]) or "重点风险条款"
        )
        answer = (
            f"我会基于现有分析继续回答。当前合同整体风险为“{overall}”，重点是：{reference_titles}。"
            f"结合你刚才的问题“{q}”以及上下文“{recent_question}”，建议优先围绕付款触发条件、责任边界和解除补偿三块继续谈判。"
        )

    citations = [
        t
        for t in (_as_risk_dict(item).get("title", "") for item in top_risks[:3])
        if t
    ]
    if not citations and risk_items:
        citations = [
            t
            for t in (_as_risk_dict(item).get("title", "") for item in risk_items[:3])
            if t
        ]
    return {"answer": answer, "citations": citations}
