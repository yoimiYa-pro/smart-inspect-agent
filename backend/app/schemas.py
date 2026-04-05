from typing import Any, List, Optional

from pydantic import BaseModel, Field


def dump_pydantic_model(model: Any) -> dict:
    """序列化为字典，兼容 Pydantic v2（model_dump）与 v1（dict）。"""
    dump_v2 = getattr(model, "model_dump", None)
    if callable(dump_v2):
        return dump_v2()
    dump_v1 = getattr(model, "dict", None)
    if callable(dump_v1):
        return dump_v1()
    raise TypeError(f"无法序列化 {type(model).__name__}：缺少 model_dump / dict")


class Clause(BaseModel):
    index: int
    text: str


class CategorySummary(BaseModel):
    category: str
    display_name: str
    level: str
    score: int
    hit_count: int


class TopRiskItem(BaseModel):
    id: str
    title: str
    clause_index: Optional[int] = None
    severity: str
    priority_rank: int
    priority_reason: str
    suggestion: str


class RoleAnalysis(BaseModel):
    role: str
    is_unfavorable: bool
    biggest_risks: List[str] = Field(default_factory=list)
    advice: List[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    id: str
    category: str
    title: str
    clause_index: Optional[int] = None
    clause_text: Optional[str] = None
    severity: str
    score: int
    risk_level_text: str
    priority_rank: int
    priority_bucket: str
    priority_reason: str
    issue: str
    basis: str
    reason: str
    plain_explanation: str
    suggestion: str
    role_impact: str
    legal_basis: str
    case_reference: str
    is_unfavorable_to_role: bool
    role_advice: str
    llm_explanation: str
    followup_hint: str


class ReviewRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=30000)
    role: str = Field(default="乙方", min_length=2, max_length=8)
    enhance_with_llm: bool = Field(
        default=True,
        description="为 True 且未启用 defer_llm 时，在本请求内完成 LLM 增强。",
    )
    defer_llm: bool = Field(
        default=False,
        description="为 True 时只做规则与本地摘要，返回 llm_mode=deferred，可再调用 /api/review/enhance。",
    )


class EnhanceReviewRequest(BaseModel):
    text: str = Field(..., min_length=20, max_length=30000)
    role: str = Field(default="乙方", min_length=2, max_length=8)


class ReviewResponse(BaseModel):
    role: str
    contract_type: str
    contract_type_reason: str
    clauses: List[Clause]
    category_overview: List[CategorySummary]
    risk_items: List[RiskItem]
    top_risks: List[TopRiskItem]
    role_analysis: RoleAnalysis
    summary: str
    review_highlights: List[str]
    one_line_conclusion: str
    priority_notice: str
    overall_risk_level: str
    signing_advice: str
    lawyer_suggestion: str
    risk_score: int
    risk_level_text: str
    llm_mode: str
    mock_reason: Optional[str] = None


class FollowupRequest(BaseModel):
    contract_text: str = Field(..., min_length=20, max_length=30000)
    risk: RiskItem
    question: str = Field(..., min_length=2, max_length=1000)
    role: str = Field(default="乙方", min_length=2, max_length=8)
    enhance_with_llm: bool = True


class FollowupResponse(BaseModel):
    answer: str
    llm_mode: str
    mock_reason: Optional[str] = None
    suggested_followups: List[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: str = Field(..., min_length=4, max_length=12)
    content: str = Field(..., min_length=1, max_length=2000)


class ContractChatRequest(BaseModel):
    contract_text: str = Field(..., min_length=20, max_length=30000)
    analysis: ReviewResponse
    question: str = Field(..., min_length=2, max_length=1000)
    role: str = Field(default="乙方", min_length=2, max_length=8)
    messages: List[ChatMessage] = Field(default_factory=list)
    enhance_with_llm: bool = True


class ContractChatResponse(BaseModel):
    answer: str
    citations: List[str] = Field(default_factory=list)
    llm_mode: str
    mock_reason: Optional[str] = None
    suggested_followups: List[str] = Field(default_factory=list)


class ModelConfigRequest(BaseModel):
    model_name: str = Field(..., min_length=2, max_length=64)


class ModelConfigResponse(BaseModel):
    active_model: str
    available_models: List[str] = Field(default_factory=list)
    llm_enabled: bool


class HealthResponse(BaseModel):
    status: str
    llm_enabled: bool
    frontend_ready: bool
    active_model: str
    available_models: List[str] = Field(default_factory=list)
