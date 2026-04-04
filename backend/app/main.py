from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.config import get_settings, get_supported_models, set_openai_model
from app.schemas import (
    ContractChatRequest,
    ContractChatResponse,
    EnhanceReviewRequest,
    FollowupRequest,
    FollowupResponse,
    HealthResponse,
    ModelConfigRequest,
    ModelConfigResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.services.analyzer import ContractReviewService
from app.services.llm_client import OpenAICompatibleClient

app_settings = get_settings()
app = FastAPI(title=app_settings.project_name, version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _build_review_service() -> ContractReviewService:
    return ContractReviewService(OpenAICompatibleClient(get_settings()))


def _build_model_config_response() -> ModelConfigResponse:
    settings = get_settings()
    return ModelConfigResponse(
        active_model=settings.openai_model or get_supported_models()[-1],
        available_models=get_supported_models(),
        llm_enabled=settings.llm_enabled,
    )


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        llm_enabled=settings.llm_enabled,
        frontend_ready=settings.frontend_dist.exists(),
        active_model=settings.openai_model or get_supported_models()[-1],
        available_models=get_supported_models(),
    )


@app.get("/api/model-config", response_model=ModelConfigResponse)
def get_model_config() -> ModelConfigResponse:
    return _build_model_config_response()


@app.post("/api/model-config", response_model=ModelConfigResponse)
def update_model_config(payload: ModelConfigRequest) -> ModelConfigResponse:
    try:
        set_openai_model(payload.model_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _build_model_config_response()


@app.post("/api/review", response_model=ReviewResponse)
def review_contract(payload: ReviewRequest) -> ReviewResponse:
    review_service = _build_review_service()
    return review_service.analyze_contract(
        payload.text,
        payload.role,
        payload.enhance_with_llm,
        defer_llm=payload.defer_llm,
    )


@app.post("/api/review/enhance", response_model=ReviewResponse)
def enhance_review_contract(payload: EnhanceReviewRequest) -> ReviewResponse:
    """对同一份合同文本做一次完整审查（含 LLM 增强），用于两阶段流程的第二段。"""
    review_service = _build_review_service()
    return review_service.analyze_contract(payload.text, payload.role, True, defer_llm=False)


@app.post("/api/followup", response_model=FollowupResponse)
def followup_risk(payload: FollowupRequest) -> FollowupResponse:
    review_service = _build_review_service()
    return review_service.answer_followup(
        contract_text=payload.contract_text,
        risk=payload.risk.model_dump(),
        question=payload.question,
        role=payload.role,
        enhance_with_llm=payload.enhance_with_llm,
    )


@app.post("/api/chat", response_model=ContractChatResponse)
def chat_with_contract(payload: ContractChatRequest) -> ContractChatResponse:
    review_service = _build_review_service()
    return review_service.chat_with_contract(
        contract_text=payload.contract_text,
        question=payload.question,
        role=payload.role,
        analysis=payload.analysis.model_dump(),
        messages=[message.model_dump() for message in payload.messages],
        enhance_with_llm=payload.enhance_with_llm,
    )


@app.get("/", include_in_schema=False, response_model=None)
def root() -> JSONResponse | FileResponse:
    settings = get_settings()
    index_file = settings.frontend_dist / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        {
            "name": settings.project_name,
            "message": "后端已启动。若需前端页面，请先在 frontend 目录执行 npm install && npm run build。",
        }
    )


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
def spa_fallback(full_path: str) -> JSONResponse | FileResponse:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    settings = get_settings()
    dist_dir = settings.frontend_dist
    candidate = (dist_dir / full_path).resolve()
    index_file = dist_dir / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend build not found")
    if dist_dir.exists() and Path(candidate).is_file() and str(candidate).startswith(str(dist_dir.resolve())):
        return FileResponse(candidate)
    return FileResponse(index_file)
