"""确定性「工具」输出：在后端编排层执行，结果注入 LLM 的 prompt payload，体现 Agent 赛道中的 Action 维度。"""
from __future__ import annotations

import re
from typing import Any


_CURRENCY_RE = re.compile(
    r"(人民币|RMB|CNY|￥|¥)?\s*([\d０-９]+(?:[,，][\d０-９]{3})*(?:\.[\d]+)?)\s*(万元|亿元|元)?",
    re.IGNORECASE,
)
_DAYS_RE = re.compile(r"(\d+)\s*(个工作日|自然日|日|天|个月|年)")


def extract_key_numbers(contract_text: str, max_items: int = 12) -> list[dict[str, Any]]:
    """从合同中启发式抽取金额与期限类片段（不参与司法判断，仅辅助模型陈述时对齐原文）。"""
    text = (contract_text or "").strip()
    if not text:
        return []
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for m in _CURRENCY_RE.finditer(text):
        snippet = m.group(0).strip()[:80]
        if snippet and snippet not in seen:
            seen.add(snippet)
            found.append({"type": "amount_or_currency", "snippet": snippet})

    for m in _DAYS_RE.finditer(text):
        snippet = m.group(0).strip()[:80]
        if snippet and snippet not in seen:
            seen.add(snippet)
            found.append({"type": "term", "snippet": snippet})

    return found[:max_items]


def list_clause_indices(clauses: list[dict[str, Any]], max_n: int = 30) -> list[int]:
    """返回已切分条款的序号列表（确定性、可审计）。"""
    out: list[int] = []
    for item in clauses[:max_n]:
        idx = item.get("index")
        if isinstance(idx, int):
            out.append(idx)
    return out
