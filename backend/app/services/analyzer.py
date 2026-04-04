"""向后兼容：审查编排已迁移至 ``app.services.review``。"""
from __future__ import annotations

from app.services.review.service import ContractReviewService

__all__ = ["ContractReviewService"]
