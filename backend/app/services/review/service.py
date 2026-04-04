from __future__ import annotations

import logging
import re
import time
from typing import Any

from app.schemas import (
    CategorySummary,
    Clause,
    ContractChatResponse,
    FollowupResponse,
    ReviewResponse,
    RiskItem,
    RoleAnalysis,
    TopRiskItem,
)
from app.services import contract_tools
from app.services.llm_client import OpenAICompatibleClient
from app.services.mock_fallback import (
    answer_contract_chat_with_mock,
    answer_with_mock,
    build_followup_hint,
    build_mock_summary_text,
)
from app.services.review.constants import (
    CATEGORY_META,
    CATEGORY_ROLE_ADVICE,
    DEFAULT_CASE_REFERENCE,
    DEFAULT_LEGAL_BASIS,
    SEVERITY_DEDUCTION,
    SEVERITY_RANK,
    SEVERITY_SCORE,
    SEVERITY_TEXT,
    TYPE_RULES,
)

logger = logging.getLogger(__name__)


def _suggested_followups_followup(risk: dict[str, Any], role: str) -> list[str]:
    title = str(risk.get("title") or "").strip()[:40]
    role_s = str(role or "乙方").strip() or "乙方"
    base: list[str] = []
    if title:
        base.append(f"若双方不改「{title}」相关表述，最坏情况下我方可能承担哪些后果？请简要列举。")
    base.append(f"站在{role_s}立场，写一条可接受的折中条款示例（一句人话）。")
    base.append("这条在邮件里和对方业务怎么沟通，不容易谈崩？给一套简短话术。")
    if len(base) < 4:
        base.append("请区分：哪些是法律依据、哪些是实务建议。")
    return base[:4]


def _suggested_followups_chat(analysis: dict[str, Any], role: str) -> list[str]:
    role_s = str(role or "乙方").strip() or "乙方"
    out: list[str] = []
    tr = analysis.get("top_risks") or []
    if tr and isinstance(tr[0], dict):
        t = str(tr[0].get("title") or "").strip()[:36]
        if t:
            out.append(f"用三句话解释「{t}」对{role_s}的实际影响（避免法条堆砌）。")
    oc = analysis.get("one_line_conclusion")
    if isinstance(oc, str) and oc.strip():
        out.append("把本轮一句话结论改成：谈判时可用的三个要点。")
    items = analysis.get("risk_items") or []
    if isinstance(items, list) and len(items) > 1:
        out.append("在已列风险里，若预算只允许改两处，优先改哪两处？")
    out.append(f"若我是{role_s}法务，发给业务同事的「签前检查清单」五条版怎么写？")
    return out[:4]


class ContractReviewService:
    def __init__(self, llm_client: OpenAICompatibleClient) -> None:
        self.llm_client = llm_client

    def analyze_contract(
        self,
        text: str,
        role: str = "乙方",
        enhance_with_llm: bool = True,
        defer_llm: bool = False,
    ) -> ReviewResponse:
        t0 = time.monotonic()

        normalized = self._normalize_text(text)
        selected_role = self._normalize_role(role)
        clauses = self._split_clauses(normalized)
        contract_type, type_reason = self._classify_contract_type(normalized)
        rule_hits = self._identify_rule_hits(normalized, clauses, contract_type)
        risk_dicts = self._build_risks_from_hits(rule_hits, selected_role)
        risk_dicts.sort(
            key=lambda item: (
                SEVERITY_RANK[item["severity"]],
                item["score"],
                1 if item["is_unfavorable_to_role"] else 0,
            ),
            reverse=True,
        )
        self._assign_priorities(risk_dicts, selected_role)
        category_overview = self._build_category_overview(risk_dicts)
        t_after_rules = time.monotonic()
        logger.info(
            "analyze_contract rules_done",
            extra={
                "elapsed_ms": round((t_after_rules - t0) * 1000, 2),
                "rule_hit_count": len(rule_hits),
                "risk_count": len(risk_dicts),
            },
        )

        summary_payload = self.generate_contract_summary(
            contract_type=contract_type,
            role=selected_role,
            risk_items=risk_dicts,
            category_overview=category_overview,
        )
        t_after_summary = time.monotonic()
        logger.info(
            "analyze_contract summary_done",
            extra={"elapsed_ms": round((t_after_summary - t_after_rules) * 1000, 2)},
        )

        llm_mode = "rules_only"
        mock_reason = None
        want_llm = enhance_with_llm and not defer_llm

        if defer_llm:
            llm_mode = "deferred"
            logger.info(
                "analyze_contract llm_skipped_deferred",
                extra={"elapsed_ms": round((time.monotonic() - t0) * 1000, 2)},
            )
        elif not enhance_with_llm:
            logger.info(
                "analyze_contract llm_skipped_rules_only",
                extra={"elapsed_ms": round((time.monotonic() - t0) * 1000, 2)},
            )
        elif want_llm and risk_dicts:
            t_llm_start = time.monotonic()
            logger.info("analyze_contract llm_start", extra={"elapsed_ms": round((t_llm_start - t0) * 1000, 2)})
            prompt_payload = self._build_review_prompt_payload(
                contract_text=normalized,
                role=selected_role,
                contract_type=contract_type,
                type_reason=type_reason,
                clauses=clauses,
                rule_hits=rule_hits,
                risk_items=risk_dicts,
                category_overview=category_overview,
                summary_payload=summary_payload,
            )
            try:
                enhanced = self.llm_client.enhance_review(prompt_payload)
                t_llm_after_call = time.monotonic()
                logger.info(
                    "analyze_contract llm_enhance_returned",
                    extra={"elapsed_ms": round((t_llm_after_call - t_llm_start) * 1000, 2)},
                )
                self._merge_llm_review(summary_payload, risk_dicts, enhanced, selected_role)
                t_after_merge = time.monotonic()
                logger.info(
                    "analyze_contract merge_done",
                    extra={"elapsed_ms": round((t_after_merge - t_llm_after_call) * 1000, 2)},
                )
                llm_mode = "live"
            except Exception as exc:
                mock_reason = str(exc)
                llm_mode = "mock"
                logger.warning(
                    "analyze_contract llm_failed: %s",
                    exc,
                    extra={"elapsed_ms": round((time.monotonic() - t_llm_start) * 1000, 2)},
                    exc_info=True,
                )
        elif enhance_with_llm and not self.llm_client.enabled:
            mock_reason = "未配置可用的 OpenAI 兼容模型，已自动切换为 mock 模式。"
            llm_mode = "mock"

        logger.info(
            "analyze_contract complete",
            extra={
                "llm_mode": llm_mode,
                "total_ms": round((time.monotonic() - t0) * 1000, 2),
            },
        )

        return ReviewResponse(
            role=selected_role,
            contract_type=contract_type,
            contract_type_reason=type_reason,
            clauses=[Clause(**item) for item in clauses],
            category_overview=[CategorySummary(**item) for item in category_overview],
            risk_items=[RiskItem(**item) for item in risk_dicts],
            top_risks=[TopRiskItem(**item) for item in summary_payload["top_risks"]],
            role_analysis=RoleAnalysis(**summary_payload["role_analysis"]),
            summary=summary_payload["summary"],
            review_highlights=summary_payload["review_highlights"],
            one_line_conclusion=summary_payload["one_line_conclusion"],
            priority_notice=summary_payload["priority_notice"],
            overall_risk_level=summary_payload["overall_risk_level"],
            signing_advice=summary_payload["signing_advice"],
            lawyer_suggestion=summary_payload["lawyer_suggestion"],
            risk_score=summary_payload["risk_score"],
            risk_level_text=summary_payload["risk_level_text"],
            llm_mode=llm_mode,
            mock_reason=mock_reason,
        )

    def generate_contract_summary(
        self,
        contract_type: str,
        role: str,
        risk_items: list[dict[str, Any]],
        category_overview: list[dict[str, Any]],
    ) -> dict[str, Any]:
        risk_score = self._calculate_risk_score(risk_items)
        overall_risk_level = self._derive_overall_level(risk_items, risk_score)
        signing_advice = {"高": "不建议", "中": "谨慎", "低": "建议签"}[overall_risk_level]
        lawyer_suggestion = {
            "高": "建议咨询律师",
            "中": "建议在签约前咨询律师",
            "低": "暂可不必咨询律师",
        }[overall_risk_level]
        risk_level_text = {
            "高": "高风险预警",
            "中": "中风险待谈判",
            "低": "低风险可控",
        }[overall_risk_level]
        top_risks = risk_items[:3]
        top_titles = [item["title"] for item in top_risks]
        role_unfavorable = any(item["is_unfavorable_to_role"] for item in top_risks) or overall_risk_level == "高"
        priority_notice = "如果只能修改3条，建议优先处理以下条款："
        if top_risks:
            priority_notice += "；".join(
                f"第{item['clause_index']}条《{item['title']}》" if item.get("clause_index") else f"《{item['title']}》"
                for item in top_risks
            )
        else:
            priority_notice += "优先复核付款、责任、解除与争议解决条款。"

        role_advice = [item["role_advice"] for item in top_risks if item.get("role_advice")]
        if not role_advice:
            role_advice = [
                "建议先确认付款触发条件是否客观、明确。",
                "建议再确认责任边界和赔偿上限是否对等。",
                "建议最后确认解除与争议解决条款是否可接受。",
            ]
        biggest_risks = [self._format_risk_headline(item) for item in top_risks]
        if not biggest_risks and category_overview:
            biggest_risks = [f"{item['display_name']}待复核" for item in category_overview[:3]]

        base_conclusion = self._build_one_line_conclusion(role, overall_risk_level, signing_advice, role_unfavorable)
        summary = build_mock_summary_text(
            contract_type=contract_type,
            role=role,
            overall_risk_level=overall_risk_level,
            signing_advice=signing_advice,
            priority_notice=priority_notice,
            top_titles=top_titles,
        )
        review_highlights = [
            f"{item['title']}：{item['plain_explanation']}"[:48]
            for item in top_risks
        ] or [f"{contract_type}当前未命中高风险规则，但仍建议复核重点条款。"]

        return {
            "summary": summary,
            "review_highlights": review_highlights,
            "one_line_conclusion": base_conclusion,
            "priority_notice": priority_notice,
            "overall_risk_level": overall_risk_level,
            "signing_advice": signing_advice,
            "lawyer_suggestion": lawyer_suggestion,
            "risk_score": risk_score,
            "risk_level_text": risk_level_text,
            "top_risks": [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "clause_index": item.get("clause_index"),
                    "severity": item["severity"],
                    "priority_rank": item["priority_rank"],
                    "priority_reason": item["priority_reason"],
                    "suggestion": item["suggestion"],
                }
                for item in top_risks
            ],
            "role_analysis": {
                "role": role,
                "is_unfavorable": role_unfavorable,
                "biggest_risks": biggest_risks,
                "advice": role_advice[:3],
            },
        }

    def answer_followup(
        self,
        contract_text: str,
        risk: dict[str, Any],
        question: str,
        role: str = "乙方",
        enhance_with_llm: bool = True,
    ) -> FollowupResponse:
        selected_role = self._normalize_role(role)
        prompt_payload = self._build_followup_prompt_payload(contract_text, risk, question, selected_role)
        if enhance_with_llm:
            try:
                result = self.llm_client.followup(prompt_payload)
                answer = str(result.get("answer", "")).strip()

                if answer:
                    return FollowupResponse(
                        answer=answer,
                        llm_mode="live",
                        mock_reason=None,
                        suggested_followups=_suggested_followups_followup(risk, selected_role),
                    )
                raise ValueError("模型未返回有效回答")
            except Exception as exc:
                return FollowupResponse(
                    answer=answer_with_mock(risk, question, selected_role),
                    llm_mode="mock",
                    mock_reason=str(exc),
                    suggested_followups=_suggested_followups_followup(risk, selected_role),
                )

        return FollowupResponse(
            answer=answer_with_mock(risk, question, selected_role),
            llm_mode="mock",
            mock_reason="已按本地 mock 模式回答。",
            suggested_followups=_suggested_followups_followup(risk, selected_role),
        )

    def chat_with_contract(
        self,
        contract_text: str,
        question: str,
        analysis: dict[str, Any],
        messages: list[dict[str, Any]] | None,
        role: str = "乙方",
        enhance_with_llm: bool = True,
    ) -> ContractChatResponse:
        selected_role = self._normalize_role(role)
        prompt_payload = self._build_chat_prompt_payload(contract_text, question, analysis, messages, selected_role)
        if enhance_with_llm:
            try:
                result = self.llm_client.chat_with_contract(prompt_payload)
                answer = str(result.get("answer", "")).strip()
                citations = self._filter_chat_citations(
                    result.get("citations", []),
                    prompt_payload["citation_candidates"],
                )
                if answer:
                    return ContractChatResponse(
                        answer=answer,
                        citations=citations,
                        llm_mode="live",
                        mock_reason=None,
                        suggested_followups=_suggested_followups_chat(analysis, selected_role),
                    )
                raise ValueError("模型未返回有效回答")
            except Exception as exc:
                fallback = answer_contract_chat_with_mock(question, analysis, messages or [], selected_role)
                return ContractChatResponse(
                    answer=fallback["answer"],
                    citations=fallback.get("citations", []),
                    llm_mode="mock",
                    mock_reason=str(exc),
                    suggested_followups=_suggested_followups_chat(analysis, selected_role),
                )

        fallback = answer_contract_chat_with_mock(question, analysis, messages or [], selected_role)
        return ContractChatResponse(
            answer=fallback["answer"],
            citations=fallback.get("citations", []),
            llm_mode="mock",
            mock_reason="已按本地 mock 模式回答。",
            suggested_followups=_suggested_followups_chat(analysis, selected_role),
        )


    def _build_followup_prompt_payload(
        self,
        contract_text: str,
        risk: dict[str, Any],
        question: str,
        role: str,
    ) -> dict[str, Any]:
        return {
            "role": role,
            "question": (question or "").strip(),
            "risk_brief": {
                "title": risk.get("title"),
                "severity": risk.get("severity"),
                "clause_index": risk.get("clause_index"),
                "issue": risk.get("issue"),
                "reason": risk.get("reason"),
                "plain_explanation": risk.get("plain_explanation"),
                "suggestion": risk.get("suggestion"),
                "role_impact": risk.get("role_impact"),
                "legal_basis": risk.get("legal_basis"),
                "clause_text": (risk.get("clause_text") or "")[:240],
            },
            "contract_excerpt": contract_text[:2200],
        }

    def _build_chat_prompt_payload(
        self,
        contract_text: str,
        question: str,
        analysis: dict[str, Any],
        messages: list[dict[str, Any]] | None,
        role: str,
    ) -> dict[str, Any]:
        compact_messages: list[dict[str, str]] = []
        for item in (messages or [])[-6:]:
            if not isinstance(item, dict):
                continue
            msg_role = str(item.get("role") or "").strip()
            content = str(item.get("content") or "").strip()
            if not msg_role or not content:
                continue
            compact_messages.append({"role": msg_role, "content": content[:180]})

        citation_candidates: list[str] = []
        one_line_conclusion = str(analysis.get("one_line_conclusion") or "").strip()
        if one_line_conclusion:
            citation_candidates.append(one_line_conclusion)
        for items in (analysis.get("top_risks", [])[:3], analysis.get("risk_items", [])[:6]):
            for item in items:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or "").strip()
                if title and title not in citation_candidates:
                    citation_candidates.append(title)

        return {
            "role": role,
            "question": (question or "").strip(),
            "messages": compact_messages,
            "analysis": {
                "one_line_conclusion": analysis.get("one_line_conclusion"),
                "overall_risk_level": analysis.get("overall_risk_level"),
                "signing_advice": analysis.get("signing_advice"),
                "priority_notice": analysis.get("priority_notice"),
                "review_highlights": analysis.get("review_highlights", [])[:4],
                "top_risks": [
                    {
                        "title": item.get("title"),
                        "clause_index": item.get("clause_index"),
                        "severity": item.get("severity"),
                        "priority_rank": item.get("priority_rank"),
                        "suggestion": item.get("suggestion"),
                    }
                    for item in analysis.get("top_risks", [])[:3]
                    if isinstance(item, dict)
                ],
                "risk_items": [
                    {
                        "title": item.get("title"),
                        "clause_index": item.get("clause_index"),
                        "severity": item.get("severity"),
                        "priority_rank": item.get("priority_rank"),
                        "issue": item.get("issue"),
                        "plain_explanation": item.get("plain_explanation"),
                        "suggestion": item.get("suggestion"),
                        "role_advice": item.get("role_advice"),
                    }
                    for item in analysis.get("risk_items", [])[:6]
                    if isinstance(item, dict)
                ],
                "role_analysis": analysis.get("role_analysis", {}),
            },
            "citation_candidates": citation_candidates,
            "contract_excerpt": contract_text[:2200],
        }

    def _filter_chat_citations(self, citations: list[Any], allowed: list[str]) -> list[str]:
        allowed_values = {item.strip() for item in allowed if isinstance(item, str) and item.strip()}
        cleaned: list[str] = []
        for item in citations:
            value = str(item).strip()
            if value and value in allowed_values and value not in cleaned:
                cleaned.append(value)
        return cleaned[:4]

    def _normalize_role(self, role: str) -> str:
        role = (role or "乙方").strip()
        return role if role in {"甲方", "乙方"} else "乙方"


    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[\t\u3000]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _split_clauses(self, text: str) -> list[dict[str, Any]]:
        parts = re.split(
            r"(?=(?:^|\n)\s*(?:第[一二三四五六七八九十百零]+条|[0-9]{1,2}[.、)]|[一二三四五六七八九十]+、))",
            text,
            flags=re.MULTILINE,
        )
        chunks = [item.strip() for item in parts if item and item.strip()]
        if len(chunks) < 4:
            paragraphs = [item.strip() for item in re.split(r"\n{2,}", text) if item.strip()]
            if len(paragraphs) > len(chunks):
                chunks = paragraphs
        if len(chunks) < 4:
            sentences = [
                item.strip(" ；;。\n")
                for item in re.split(r"[。；;\n]", text)
                if len(item.strip()) >= 12
            ]
            merged: list[str] = []
            buffer = ""
            for sentence in sentences:
                if len(buffer) + len(sentence) < 80:
                    buffer = f"{buffer}；{sentence}" if buffer else sentence
                else:
                    if buffer:
                        merged.append(buffer)
                    buffer = sentence
            if buffer:
                merged.append(buffer)
            chunks = merged or [text]
        return [{"index": index + 1, "text": chunk} for index, chunk in enumerate(chunks)]

    def _classify_contract_type(self, text: str) -> tuple[str, str]:
        best_type = "通用合同"
        best_score = 0
        matched_words: list[str] = []
        for contract_type, keywords in TYPE_RULES.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > best_score:
                best_type = contract_type
                best_score = score
                matched_words = [keyword for keyword in keywords if keyword in text][:4]
        if best_score == 0:
            return "通用合同", "未命中特定合同类型关键词，按通用合同处理。"
        return best_type, f"命中关键词：{'、'.join(matched_words)}。"

    def _identify_rule_hits(
        self,
        full_text: str,
        clauses: list[dict[str, Any]],
        contract_type: str,
    ) -> list[dict[str, Any]]:
        hits: list[dict[str, Any]] = []
        seen: set[tuple[str, str, int | None]] = set()

        def add_hit(
            category: str,
            title: str,
            severity: str,
            issue: str,
            basis: str,
            suggestion: str,
            clause: dict[str, Any] | None = None,
            unfavorable_to: tuple[str, ...] = ("甲方", "乙方"),
            role_impact_map: dict[str, str] | None = None,
            role_advice_map: dict[str, str] | None = None,
            legal_basis: str | None = None,
            case_reference: str | None = None,
        ) -> None:
            clause_index = clause["index"] if clause else None
            unique_key = (category, title, clause_index)
            if unique_key in seen:
                return
            seen.add(unique_key)
            hits.append(
                {
                    "category": category,
                    "title": title,
                    "severity": severity,
                    "issue": issue,
                    "basis": basis,
                    "suggestion": suggestion,
                    "clause_index": clause_index,
                    "clause_text": clause["text"] if clause else None,
                    "unfavorable_to": list(unfavorable_to),
                    "role_impact_map": role_impact_map or {},
                    "role_advice_map": role_advice_map or {},
                    "legal_basis": legal_basis or DEFAULT_LEGAL_BASIS[category],
                    "case_reference": case_reference or DEFAULT_CASE_REFERENCE[category],
                }
            )

        def filter_clauses(keywords: list[str]) -> list[dict[str, Any]]:
            return [clause for clause in clauses if any(keyword in clause["text"] for keyword in keywords)]

        payment_clauses = filter_clauses(["付款", "支付", "价款", "结算", "发票", "账期", "尾款"])
        if not payment_clauses:
            add_hit(
                "payment",
                "缺少明确付款结算机制",
                "medium",
                "合同未清晰约定付款节点、开票条件或结算口径，容易引发回款和履约争议。",
                "全文未命中付款、结算、发票等核心关键词。",
                "补充分阶段付款安排、验收标准、开票要求和逾期付款责任。",
            )
        else:
            payment_text = "\n".join(item["text"] for item in payment_clauses)
            for clause in payment_clauses:
                content = clause["text"]
                if re.search(r"付款时间另行(?:协商|通知)|以甲方(?:审批|确认|审核)为准|甲方有权(?:延期|暂缓)支付", content):
                    add_hit(
                        "payment",
                        "付款时间被单方控制",
                        "high",
                        "付款触发条件不客观，容易导致一方虽然完成交付却迟迟无法收款。",
                        "命中“付款时间另行协商/以甲方审批为准/甲方有权延期支付”等表述。",
                        "改为固定日期或客观验收节点，并补充逾期付款违约责任。",
                        clause,
                        unfavorable_to=("乙方",),
                        role_impact_map={
                            "乙方": "从乙方视角看，甲方掌握付款触发权，回款周期和现金流都会被动。",
                            "甲方": "从甲方视角看，单方控制付款虽短期有利，但容易导致乙方消极履约或要求抬价。",
                        },
                        role_advice_map={
                            "乙方": "要求把付款条件改成“阶段交付+书面验收+固定期限付款”。",
                            "甲方": "建议保留合理验收权，但不要把付款完全绑定到内部审批。",
                        },
                    )
                if re.search(r"(?:全部|100%).{0,12}(?:验收|交付).{0,12}(?:后|合格后).{0,8}(?:支付|付款)", content):
                    add_hit(
                        "payment",
                        "尾款过度集中在最终验收后",
                        "medium",
                        "费用过度后置，履约方要先投入大部分成本，回款风险集中。",
                        "命中“全部款项在最终验收合格后支付”等集中付款表述。",
                        "设置预付款、阶段款和验收尾款，降低单点回款风险。",
                        clause,
                        unfavorable_to=("乙方",),
                        role_impact_map={
                            "乙方": "从乙方视角看，项目越长、投入越大，尾款越集中，现金流压力越大。"
                        },
                        role_advice_map={
                            "乙方": "至少争取启动款或里程碑付款，避免全部风险压到最终验收。"
                        },
                    )
                if re.search(r"乙方.{0,8}垫资|先行承担全部成本", content):
                    add_hit(
                        "payment",
                        "存在垫资履约风险",
                        "high",
                        "一方需先行垫付大量成本，一旦项目延期、验收卡顿或终止，损失会快速累积。",
                        "条款出现“乙方垫资/先行承担全部成本”等表述。",
                        "增加启动款或里程碑付款，避免无上限垫资。",
                        clause,
                        unfavorable_to=("乙方",),
                        role_impact_map={
                            "乙方": "从乙方视角看，这会直接拉高履约成本和坏账风险。"
                        },
                        role_advice_map={
                            "乙方": "要求把人力、采购和差旅成本拆分到阶段回款中。"
                        },
                    )
                if "验收" in content and not re.search(r"标准|指标|视为验收|工作日内", content):
                    add_hit(
                        "payment",
                        "验收标准不明确",
                        "medium",
                        "合同提到验收，但没有量化指标或逾期视为通过机制，容易导致付款卡在验收环节。",
                        "条款出现“验收”但未命中标准、时限、默认通过等关键表达。",
                        "补充验收指标、整改次数、时限和逾期未反馈视为通过。",
                        clause,
                    )
            if not re.search(r"逾期|违约金|滞纳金", payment_text):
                add_hit(
                    "payment",
                    "未约定逾期付款责任",
                    "medium",
                    "即使出现拖延付款，也缺少明确违约后果，催收抓手不足。",
                    "付款相关条款未命中逾期付款违约责任描述。",
                    "补充逾期付款违约金、暂停服务或解除合同权利。",
                    unfavorable_to=("乙方",),
                )

        liability_clauses = filter_clauses(["违约", "责任", "赔偿", "损失", "免责", "连带责任"])
        if not liability_clauses:
            add_hit(
                "liability",
                "违约责任边界不清",
                "medium",
                "未约定违约责任、赔偿范围或免责条件，争议时很难高效主张权利。",
                "全文未命中违约责任、赔偿、损失等关键词。",
                "补充违约责任、赔偿范围、免责条件及责任上限。",
            )
        else:
            for clause in liability_clauses:
                content = clause["text"]
                if re.search(r"承担(?:全部|一切)损失|无限责任|连带责任", content):
                    add_hit(
                        "liability",
                        "赔偿责任可能失控",
                        "high",
                        "责任范围过宽，可能导致一方承担无限或不成比例的损失。",
                        "命中“承担全部损失/无限责任/连带责任”等高压责任表述。",
                        "限定为直接损失，并设置责任上限与免责情形。",
                        clause,
                        role_impact_map={
                            "乙方": "从乙方视角看，这类条款最容易造成项目收益无法覆盖潜在赔偿。",
                            "甲方": "从甲方视角看，责任失衡虽然有利索赔，但也容易导致对方拒签或显著抬价。",
                        },
                    )
                if re.search(r"甲方不承担任何责任|乙方不得追究|单方免责", content):
                    add_hit(
                        "liability",
                        "存在单方免责条款",
                        "high",
                        "责任明显失衡，一方几乎不承担违约后果。",
                        "条款出现“甲方不承担任何责任/乙方不得追究”等片面免责表述。",
                        "改为双方责任对等，并明确各自违约后果。",
                        clause,
                        unfavorable_to=("乙方",),
                        role_impact_map={
                            "乙方": "从乙方视角看，这意味着一旦出现损失，维权空间会被明显压缩。"
                        },
                    )
                if "违约金" in content and re.search(r"合同总额.{0,6}(30%|50%|100%)", content):
                    add_hit(
                        "liability",
                        "违约金比例明显偏高",
                        "medium",
                        "违约金约定过高，可能导致轻微违约也承担过重后果。",
                        "条款出现按合同总额高比例计收违约金的表述。",
                        "将违约金与实际损失、违约程度相匹配，并设置上限。",
                        clause,
                    )

        termination_clauses = filter_clauses(["解除", "终止", "提前", "续期", "到期"])
        if not termination_clauses:
            add_hit(
                "termination",
                "缺少解除与终止机制",
                "medium",
                "未明确何种情形可解除合同以及解除后的清算规则。",
                "全文未命中解除、终止、提前通知等关键词。",
                "补充解除条件、通知期限、已履行部分结算和交接义务。",
            )
        else:
            for clause in termination_clauses:
                content = clause["text"]
                if re.search(r"甲方有权单方解除|一方可随时解除|无需承担补偿责任", content):
                    add_hit(
                        "termination",
                        "单方解除权过强",
                        "high",
                        "一方可随时退出且无需补偿，另一方的前期投入和人员安排都缺乏保障。",
                        "命中“单方解除/随时解除/无需承担补偿责任”等单边退出条款。",
                        "要求增加提前通知期，并约定已完成工作量和已发生合理成本的结算补偿。",
                        clause,
                        unfavorable_to=("乙方",),
                        role_impact_map={
                            "乙方": "从乙方视角看，项目随时可能被叫停，前期投入难以回收。"
                        },
                    )
                if re.search(r"自动续期|自动延长", content) and not re.search(r"提前\d+日|提前 [0-9]+ 日", content):
                    add_hit(
                        "termination",
                        "自动续期但通知机制不清",
                        "medium",
                        "合同可能被动延长，预算、资源和履约计划都容易失控。",
                        "存在自动续期表述，但未命中明确的提前通知期限。",
                        "明确续期条件、通知期限和拒绝续签方式。",
                        clause,
                    )
                if re.search(r"解除后.*无需结算|终止后.*不再支付", content):
                    add_hit(
                        "termination",
                        "解除后结算规则失衡",
                        "medium",
                        "解除后若不对已完成工作量和已发生成本结算，会放大退出风险。",
                        "条款出现终止后无需结算或已完成工作不付款的表述。",
                        "补充解除后的阶段成果确认、已发生成本承担和资料交接规则。",
                        clause,
                        unfavorable_to=("乙方",),
                    )

        confidentiality_clauses = filter_clauses(["保密", "数据", "信息安全", "个人信息", "商业秘密", "隐私"])
        if not confidentiality_clauses:
            add_hit(
                "confidentiality",
                "缺少保密与数据安全条款",
                "high",
                "若合同涉及商业信息或业务数据，缺少保密与安全要求会带来泄露和合规风险。",
                "全文未命中保密、数据安全、个人信息等关键词。",
                "补充保密范围、安全措施、返还删除机制和违约责任。",
            )
        else:
            confidentiality_text = "\n".join(item["text"] for item in confidentiality_clauses)
            if re.search(r"个人信息|用户数据|敏感信息", full_text) and not re.search(
                r"加密|脱敏|删除|返还|访问控制|最小必要|留痕|审计", confidentiality_text
            ):
                add_hit(
                    "confidentiality",
                    "涉及数据处理但缺少安全措施",
                    "high",
                    "出现数据或个人信息处理情形，但未约定最基本的安全控制与删除机制。",
                    "文本提及个人信息/用户数据，却未命中加密、脱敏、删除、返还等安全要求。",
                    "增加加密、分级授权、删除返还、留痕审计等安全条款。",
                    unfavorable_to=("甲方", "乙方"),
                )
            if re.search(r"永久无偿使用.*数据|数据.*归甲方所有", confidentiality_text):
                add_hit(
                    "confidentiality",
                    "数据使用权限过宽",
                    "medium",
                    "数据权利边界不清，可能超出合作必要范围持续使用数据。",
                    "命中“永久无偿使用全部数据/数据归一方所有”等宽泛使用表述。",
                    "限定数据用途、保存期限、删除机制和再使用授权边界。",
                    unfavorable_to=("乙方",),
                    role_impact_map={
                        "乙方": "从乙方视角看，该条款可能导致合作结束后仍失去对业务数据成果的控制边界。"
                    },
                )

        ip_clauses = filter_clauses(["知识产权", "著作权", "专利", "技术成果", "源代码", "商标", "成果归属"])
        if not ip_clauses and contract_type in {"服务合同", "技术开发/合作合同"}:
            add_hit(
                "intellectual_property",
                "成果归属与授权规则缺失",
                "medium",
                "服务或技术类合同未明确知识产权归属，后续交付和商业使用容易产生争议。",
                "合同类型识别为服务/技术类，但未命中知识产权相关条款。",
                "补充成果归属、授权范围、源码交付和背景技术保留规则。",
            )
        else:
            for clause in ip_clauses:
                content = clause["text"]
                if re.search(r"(?:全部|所有).{0,10}(?:知识产权|著作权|源代码|技术成果).{0,10}归甲方所有", content) and not re.search(r"付清|验收|授权|背景技术", content):
                    add_hit(
                        "intellectual_property",
                        "知识产权转移条件过于笼统",
                        "high",
                        "成果权利直接全部转移，但未与付款完成、验收节点或既有技术边界挂钩。",
                        "命中“全部知识产权归甲方所有”，但未出现付清价款、验收完成或背景技术保留条件。",
                        "将知识产权转移与付款完成挂钩，并保留乙方既有工具和背景技术。",
                        clause,
                        unfavorable_to=("乙方",),
                        role_impact_map={
                            "乙方": "从乙方视角看，成果先被全部拿走而回款条件未锁定，商业风险很高。"
                        },
                    )
                if "源代码" in content and not re.search(r"托管|备份|交付范围|使用许可", content):
                    add_hit(
                        "intellectual_property",
                        "源码交付边界不清",
                        "medium",
                        "涉及源代码交付但未明确交付范围、版本、托管或许可边界，容易引发后续争议。",
                        "条款提及源代码，但未命中托管、交付清单或许可限制等关键表达。",
                        "补充交付物清单、交付版本、托管机制和使用许可范围。",
                        clause,
                    )

        dispute_clauses = filter_clauses(["争议", "仲裁", "诉讼", "法院", "管辖"])
        if not dispute_clauses:
            add_hit(
                "dispute",
                "争议解决机制缺失",
                "low",
                "合同未约定争议解决路径，后续诉讼或仲裁成本和地域风险不确定。",
                "全文未命中争议解决、法院、仲裁等关键词。",
                "明确协商、仲裁或诉讼路径，并约定具体管辖规则。",
            )
        else:
            for clause in dispute_clauses:
                content = clause["text"]
                if re.search(r"甲方所在地.{0,12}(法院|仲裁委员会)", content):
                    add_hit(
                        "dispute",
                        "管辖地偏向单方所在地",
                        "medium",
                        "争议解决地点明显偏向一方，另一方维权成本较高。",
                        "命中“甲方所在地法院/仲裁委员会管辖”等单边管辖表述。",
                        "改为合同签订地、被告所在地或双方认可的中立机构。",
                        clause,
                        unfavorable_to=("乙方",),
                    )
                if "仲裁" in content and "法院" in content:
                    add_hit(
                        "dispute",
                        "争议解决路径可能冲突",
                        "medium",
                        "同一条款同时出现仲裁与诉讼，可能导致管辖约定无效或执行混乱。",
                        "单条争议解决条款同时提及仲裁和法院。",
                        "保留一种明确且唯一的争议解决方式。",
                        clause,
                    )

        return hits

    def _build_risks_from_hits(self, rule_hits: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        for index, hit in enumerate(rule_hits, start=1):
            is_unfavorable = role in hit.get("unfavorable_to", [])
            score = min(SEVERITY_SCORE[hit["severity"]] + (6 if is_unfavorable else 0), 100)
            reason = self._build_reason(hit)
            plain_explanation = self._build_plain_explanation(hit)
            role_impact = self._resolve_role_impact(hit, role)
            role_advice = self._resolve_role_advice(hit, role)
            risk = {
                "id": f"R{index:02d}",
                "category": hit["category"],
                "title": hit["title"],
                "clause_index": hit.get("clause_index"),
                "clause_text": hit.get("clause_text"),
                "severity": hit["severity"],
                "score": score,
                "risk_level_text": SEVERITY_TEXT[hit["severity"]],
                "priority_rank": 0,
                "priority_bucket": "low",
                "priority_reason": "",
                "issue": hit["issue"],
                "basis": hit["basis"],
                "reason": reason,
                "plain_explanation": plain_explanation,
                "suggestion": hit["suggestion"],
                "role_impact": role_impact,
                "legal_basis": hit["legal_basis"],
                "case_reference": hit["case_reference"],
                "is_unfavorable_to_role": is_unfavorable,
                "role_advice": role_advice,
                "llm_explanation": reason,
                "followup_hint": build_followup_hint(hit),
            }
            risks.append(risk)
        return risks

    def _assign_priorities(self, risks: list[dict[str, Any]], role: str) -> None:
        for index, risk in enumerate(risks, start=1):
            risk["priority_rank"] = index
            if index <= 3:
                risk["priority_bucket"] = "top"
            elif risk["severity"] == "low":
                risk["priority_bucket"] = "low"
            else:
                risk["priority_bucket"] = "medium"
            risk["priority_reason"] = self._build_priority_reason(risk, role)

    def _build_category_overview(self, risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        overview: list[dict[str, Any]] = []
        for category, display_name in CATEGORY_META.items():
            current = [item for item in risks if item["category"] == category]
            if not current:
                overview.append(
                    {
                        "category": category,
                        "display_name": display_name,
                        "level": "low",
                        "score": 10,
                        "hit_count": 0,
                    }
                )
                continue
            max_level = max(current, key=lambda item: SEVERITY_RANK[item["severity"]])["severity"]
            max_score = max(item["score"] for item in current) + max(len(current) - 1, 0) * 5
            overview.append(
                {
                    "category": category,
                    "display_name": display_name,
                    "level": max_level,
                    "score": min(max_score, 100),
                    "hit_count": len(current),
                }
            )
        return overview

    def _calculate_risk_score(self, risks: list[dict[str, Any]]) -> int:
        score = 100
        for item in risks:
            score -= SEVERITY_DEDUCTION[item["severity"]]
        return max(score, 0)

    def _derive_overall_level(self, risks: list[dict[str, Any]], risk_score: int) -> str:
        if not risks:
            return "低"
        high_count = sum(1 for item in risks if item["severity"] == "high")
        medium_count = sum(1 for item in risks if item["severity"] == "medium")
        if risk_score <= 45 or high_count >= 2:
            return "高"
        if risk_score <= 75 or high_count >= 1 or medium_count >= 2:
            return "中"
        return "低"

    def _build_review_prompt_payload(
        self,
        contract_text: str,
        role: str,
        contract_type: str,
        type_reason: str,
        clauses: list[dict[str, Any]],
        rule_hits: list[dict[str, Any]],
        risk_items: list[dict[str, Any]],
        category_overview: list[dict[str, Any]],
        summary_payload: dict[str, Any],
    ) -> dict[str, Any]:
        tool_extractions = contract_tools.extract_key_numbers(contract_text)
        clause_index_list = contract_tools.list_clause_indices(clauses)
        return {
            "role": role,
            "contract_type": contract_type,
            "contract_type_reason": type_reason,
            "contract_excerpt": contract_text[:2400],
            "deterministic_tool_outputs": {
                "tool_extract_key_numbers": tool_extractions,
                "tool_list_clause_indices": clause_index_list,
                "note": "以上由后端确定性工具生成，仅供润色时引用原文语义；不得据此捏造法条或新风险。",
            },
            "clauses": [{"index": item["index"], "text": item["text"][:220]} for item in clauses[:10]],
            "rule_hits": [
                {
                    "title": item["title"],
                    "category": item["category"],
                    "severity": item["severity"],
                    "basis": item["basis"],
                    "clause_index": item.get("clause_index"),
                }
                for item in rule_hits[:10]
            ],
            "draft_risks": [
                {
                    "id": item["id"],
                    "title": item["title"],
                    "clause_index": item.get("clause_index"),
                    "severity": item["severity"],
                    "priority_rank": item.get("priority_rank"),
                    "issue": item["issue"],
                    "basis": item["basis"],
                    "reason": item["reason"],
                    "plain_explanation": item["plain_explanation"],
                    "suggestion": item["suggestion"],
                    "role_impact": item["role_impact"],
                    "followup_hint": item["followup_hint"],
                    "legal_basis": item["legal_basis"],
                    "case_reference": item["case_reference"],
                    "clause_text": (item.get("clause_text") or "")[:220],
                }
                for item in risk_items[:8]
            ],
            "category_overview": category_overview[:6],
            "draft_summary": {
                "one_line_conclusion": summary_payload.get("one_line_conclusion"),
                "summary": summary_payload.get("summary"),
                "signing_advice": summary_payload.get("signing_advice"),
                "lawyer_suggestion": summary_payload.get("lawyer_suggestion"),
                "review_highlights": summary_payload.get("review_highlights", [])[:4],
                "role_analysis": summary_payload.get("role_analysis", {}),
                "top_risks": summary_payload.get("top_risks", [])[:3],
            },
        }


    def _merge_llm_review(
        self,
        summary_payload: dict[str, Any],
        risk_items: list[dict[str, Any]],
        enhanced: dict[str, Any],
        role: str,
    ) -> None:
        for field in ["summary", "one_line_conclusion", "lawyer_suggestion", "risk_level_text"]:
            value = enhanced.get(field)
            if isinstance(value, str) and value.strip():
                summary_payload[field] = value.strip()

        signing_advice = enhanced.get("signing_advice")
        if signing_advice in {"建议签", "谨慎", "不建议"}:
            summary_payload["signing_advice"] = signing_advice

        highlights = enhanced.get("review_highlights")
        if isinstance(highlights, list):
            cleaned = [str(item).strip() for item in highlights if str(item).strip()]
            if cleaned:
                summary_payload["review_highlights"] = cleaned[:4]

        role_analysis = enhanced.get("role_analysis")
        if isinstance(role_analysis, dict):
            advice = [str(item).strip() for item in role_analysis.get("advice", []) if str(item).strip()]
            biggest = [str(item).strip() for item in role_analysis.get("biggest_risks", []) if str(item).strip()]
            summary_payload["role_analysis"] = {
                "role": role,
                "is_unfavorable": bool(role_analysis.get("is_unfavorable", summary_payload["role_analysis"]["is_unfavorable"])),
                "biggest_risks": biggest or summary_payload["role_analysis"]["biggest_risks"],
                "advice": advice[:3] or summary_payload["role_analysis"]["advice"],
            }

        risk_map = {item["id"]: item for item in risk_items}
        for item in enhanced.get("risks", []):
            if not isinstance(item, dict):
                continue
            current = risk_map.get(str(item.get("id", "")).strip())
            if not current:
                continue
            for field in [
                "reason",
                "plain_explanation",
                "suggestion",
                "role_impact",
                "legal_basis",
                "case_reference",
                "followup_hint",
            ]:
                value = item.get(field)
                if isinstance(value, str) and value.strip():
                    current[field] = value.strip()
            current["llm_explanation"] = current["reason"]

    def _build_reason(self, hit: dict[str, Any]) -> str:
        category_name = CATEGORY_META[hit["category"]]
        return f"从{category_name}的法律审查视角看，{hit['issue']} 其触发依据为：{hit['basis']}"

    def _build_plain_explanation(self, hit: dict[str, Any]) -> str:
        return f"简单说，这条约定会让后续履约、收款或维权更被动：{hit['issue']}"

    def _resolve_role_impact(self, hit: dict[str, Any], role: str) -> str:
        mapping = hit.get("role_impact_map", {})
        if mapping.get(role):
            return mapping[role]
        if role in hit.get("unfavorable_to", []):
            return f"从{role}视角看，该条款对己方明显不利，签约后更容易在{CATEGORY_META[hit['category']]}环节被动。"
        return f"从{role}视角看，该条款虽然不一定直接伤害己方，但会提高合作摩擦和后续争议概率。"

    def _resolve_role_advice(self, hit: dict[str, Any], role: str) -> str:
        mapping = hit.get("role_advice_map", {})
        if mapping.get(role):
            return mapping[role]
        if role in hit.get("unfavorable_to", []):
            return hit["suggestion"]
        return CATEGORY_ROLE_ADVICE[hit["category"]]

    def _build_priority_reason(self, risk: dict[str, Any], role: str) -> str:
        clause_text = f"已定位到第{risk['clause_index']}条" if risk.get("clause_index") else "属于整体结构性问题"
        role_text = f"且对{role}明显不利" if risk.get("is_unfavorable_to_role") else "并会放大签约争议"
        return f"{risk['risk_level_text']}，{clause_text}，{role_text}。"

    def _format_risk_headline(self, item: dict[str, Any]) -> str:
        if item.get("clause_index"):
            return f"第{item['clause_index']}条：{item['title']}"
        return item["title"]

    def _build_one_line_conclusion(
        self,
        role: str,
        overall_risk_level: str,
        signing_advice: str,
        is_unfavorable: bool,
    ) -> str:
        if overall_risk_level == "高" and is_unfavorable:
            return f"该合同对{role}明显不利，不建议直接签署。"
        if overall_risk_level == "中":
            return f"该合同存在多项需谈判条款，建议从{role}视角谨慎签署。"
        if signing_advice == "建议签":
            return f"该合同整体风险较可控，可在{role}完成关键条款复核后推进签署。"
        return f"该合同整体风险较可控，但仍建议从{role}视角完成关键条款复核后再签署。"

