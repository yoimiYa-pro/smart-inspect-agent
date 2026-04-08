from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from app.config import Settings



def _extract_json_block(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("模型未返回内容")
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("模型未返回可解析的 JSON 内容")
    return json.loads(raw[start : end + 1])


def _strip_leaked_structured_tail(text: str) -> str:
    raw = (text or "").strip()
    for marker in ("\n\n{'id':", '\n\n{"id":', "\n{'id':", '\n{"id":'):
        index = raw.find(marker)
        if index != -1:
            return raw[:index].strip()
    return raw


class OpenAICompatibleClient:

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.enabled = settings.llm_enabled
        self.model = settings.openai_model
        self.client = (
            OpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_api_base,
                timeout=settings.llm_timeout_seconds,
            )
            if self.enabled
            else None
        )

    def _ensure_enabled(self) -> None:
        if not self.enabled or self.client is None:
            raise RuntimeError("未配置可用的 OpenAI 兼容 API，已自动切换为 mock 模式")

    def _json_completion(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        self._ensure_enabled()
        completion = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = completion.choices[0].message.content or ""
        return _extract_json_block(content)

    def _build_enhance_review_prompts(self, payload: dict[str, Any]) -> tuple[str, str]:
        schema = {
            "one_line_conclusion": "string",
            "summary": "string",
            "signing_advice": "建议签 | 谨慎 | 不建议",
            "lawyer_suggestion": "string",
            "review_highlights": ["string"],
            "role_analysis": {
                "is_unfavorable": True,
                "biggest_risks": ["string"],
                "advice": ["string"],
            },
            "risks": [
                {
                    "id": "R01",
                    "reason": "法律视角说明",
                    "plain_explanation": "通俗解释",
                    "suggestion": "修改建议",
                    "role_impact": "甲/乙方影响",
                    "legal_basis": "法律依据",
                    "case_reference": "相似案例说明",
                    "followup_hint": "建议继续追问的问题",
                }
            ],
        }
        system_prompt = (
            "你是资深合同审查律师，正在向客户出具一份简明但专业的审查意见，只能基于输入中已有的合同节选、规则命中、草稿风险和草稿结论做增强。"
            "输入中若含 deterministic_tool_outputs，仅为后端已执行的确定性抽取（金额/期限片段、条款序号列表），你可酌情在 reason 或 plain_explanation 中与合同语义呼应，但不得将其解读为新的法律结论或新风险来源。"
            "你的任务是润色和补强解释，不得新增事实、不得新增风险、不得改变风险 ID、不得改变风险顺序。"
            "表达风格要像执业律师：先亮结论，再说明风险落点，最后给谈判或改稿动作；语言专业、克制、直接，不说空话，不用 AI 腔。"
            "若输入证据不足，不得编造法条编号、司法解释条文号、案例案号或裁判结论。"
            "若某条 draft_risk 附有非空的 law_references（得理法规检索候选，含 law_id 与 title，可有 excerpt 摘录），"
            "legal_basis 必须与这些候选法规一一对应：须在同一段落内用书名号列明 law_references 中的每一部法规名称，再结合摘录或法律原则展开；"
            "不得只写其中一部而忽略列表中的其他法规，不得引用未出现在该条 law_references 中的法规名称或条文号。"
            "若该条 law_references 为空，则 legal_basis：仅写法域与法律原则表述；除非输入已给出具体条文编号，否则不得自拟“第X条”。缺少可靠依据时填“依据不足，需律师复核”。"
            "若某条 draft_risk 附有非空的 case_references（得理案例检索候选，含 case_id 与 title，可有法院、案号、裁判日期等），"
            "case_reference 必须与这些候选相呼应：可简要归纳检索案例与当前风险的关联，不得编造未出现在候选中的案号、法院或确定性裁判结论。"
            "若该条 case_references 为空，则 case_reference：缺少可靠支撑时填“无可靠案例支撑，不建议臆造”。"
            "suggestion：必须给出可执行项——至少包含「谈判话术」或「可替换条款方向（要点列举）」之一，避免空泛“建议协商”。"
            "输出必须是严格 JSON，不得包含 JSON 之外的任何字符。"
            "每条风险必须输出 reason、plain_explanation、suggestion、role_impact、legal_basis、case_reference、followup_hint。"
        )
        user_prompt = (
            "请基于以下输入生成增强后的合同审查结果。"
            "输出要求："
            "1）summary、one_line_conclusion、review_highlights 只能在不改变事实基础上做专业化润色；"
            "2）risks 的数量、顺序、id 必须与 draft_risks 完全一致；"
            "3）不得新增输入中不存在的风险、条款、事实或结论；"
            "4）必须坚持输入中的角色视角，明确写出对该角色最不利的点；"
            "5）措辞要像律师给客户的书面意见，重点写“哪里有风险、为什么会吃亏、建议怎么改”；避免使用“一定”“必然”等绝对化表述；"
            "6）reason 要体现法律判断逻辑，plain_explanation 要让非法律背景的人也能马上看懂，suggestion 要写成可直接谈判或改条款的动作；"
            "7）summary 应先给总体判断，再点出最值得优先修改的条款；review_highlights 应短、硬、像风险提示；"
            "8）若某项依据不足，按 system prompt 指定占位语填写；"
            "9）若 draft_risk 含 law_references，legal_basis 必须在正文里出现其中每一条法规的完整名称（书名号），并与摘录/原则一致，不得只提部分检索结果；不得编造名单外的法条号；"
            "10）若 draft_risk 含 case_references，case_reference 必须与其中案例标题及元数据呼应，不得编造名单外的案号或裁判结果；"
            "11）全文须与输入 role（甲方/乙方）立场一致，不得改换立场。"
            "输出 JSON Schema 如下：\n"
            + json.dumps(schema, ensure_ascii=False)
            + "\n输入数据如下：\n"
            + json.dumps(payload, ensure_ascii=False)
        )
        return system_prompt, user_prompt

    def enhance_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        system_prompt, user_prompt = self._build_enhance_review_prompts(payload)
        return self._json_completion(system_prompt, user_prompt)

    def followup(self, payload: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "你是资深合同律师，正在直接回复客户的追问，只能基于给定的风险摘要、合同节选和用户问题回答。"
            "须与 payload 中的用户角色立场一致，不得改换甲乙方立场。"
            "必须严格输出 JSON，不得输出 JSON 外文字。"
            "回答控制在 220 字内，采用“先结论、再原因、再建议”的自然语言表达，像律师当面解释：直给、明确、可落地，但不装腔。"
            "回答重点是告诉客户这件事是否值得担心、风险卡在哪里、下一步该怎么谈或怎么补条款。"
            "不得泄露原始结构化数据，不得直接输出 JSON、Python 字典、字段名、内部 ID 或风险对象原文。"
            "不得编造额外事实、法条编号、案例案号或确定性裁判结果；"
            "若依据不足，必须明确回答“仅凭当前条款无法确定，建议补充上下文或律师复核”。"
            "避免使用“一定”“必然”“肯定支持”等绝对化表述，也不要输出套话、客套话或教学腔。"
        )
        user_prompt = (
            "请返回 JSON：{\"answer\":\"...\"}。"
            "回答必须结合用户角色、风险摘要和合同节选，用客户能听懂的话解释清楚；可以保留必要的法律判断，但核心要回答“能不能接受、为什么、怎么办”，不要复述输入中的字段名。\n"
            + json.dumps(payload, ensure_ascii=False)
        )

        result = self._json_completion(system_prompt, user_prompt)
        result["answer"] = _strip_leaked_structured_tail(str(result.get("answer", "")))
        return result


    def chat_with_contract(self, payload: dict[str, Any]) -> dict[str, Any]:
        schema = {"answer": "string", "citations": ["string"]}
        system_prompt = (
            "你是合同风控智能助手，回答风格应接近审查律师给客户的即时意见，只能基于已给出的 analysis 回答用户，不得重新虚构新的审查结论或新增未识别风险。"
            "必须严格输出 JSON，不得输出 JSON 外文字。"
            "回答须始终站在输入中的用户 role（甲方或乙方）立场上表述利弊，不得擅自改换立场。"
            "回答优先依赖 analysis，聊天上下文仅用于理解用户意图，合同节选仅作补充参考。"
            "表达上要先说结论，再说依据，最后给动作建议；语气专业、冷静、克制，避免空泛总结和 AI 套话。"
            "不得泄露原始结构化数据，不得输出 Python/JSON 对象、字段名、内部 ID 或分析结果原文拷贝。"
            "不得编造法条编号、案例案号或确定性裁判结果；若现有分析未覆盖该问题，必须明确回答“现有分析未覆盖该点，建议补充条款或律师复核”。"
            "不得输出 analysis 中未出现的风险结论或条款编号。"
        )
        user_prompt = (
            "请输出 JSON Schema：\n"
            + json.dumps(schema, ensure_ascii=False)
            + "\n回答要求：1）保持中文且 220 字内；2）先给清晰结论，再补充风险依据或处理建议；3）每个判断都必须能在 analysis 或 contract_excerpt 中找到依据，且不得超出 analysis 已列风险范围；4）回答要像律师给客户的实务意见，重点回答“是否可接受、主要顾虑、下一步怎么办”；5）citations 只能从 citation_candidates 中挑选原文短语，不得自造；6）只用自然语言回答，不要附带任何字典、JSON 或字段列表；7）立场必须与 payload 中的 role 一致。\n"
            + json.dumps(payload, ensure_ascii=False)
        )

        result = self._json_completion(system_prompt, user_prompt)
        result["answer"] = _strip_leaked_structured_tail(str(result.get("answer", "")))
        return result


