from __future__ import annotations

import pytest

from app.services.llm_client import OpenAICompatibleClient
from app.services.review.service import ContractReviewService

GOLDEN_CONTRACT = """第一条 服务内容
乙方负责为甲方完成软件开发与上线支持。

第二条 费用与支付
合同总金额为人民币80万元。甲方在验收合格后60个工作日内一次性支付全部服务费。

第三条 知识产权
项目产生的全部源代码归甲方所有。

第四条 违约责任
因本项目引发的任何争议均由乙方承担全部责任，甲方不承担任何责任。
"""


@pytest.fixture()
def review_service_disabled_llm(monkeypatch) -> ContractReviewService:
    def fake_settings():
        from app.config import Settings

        return Settings(openai_api_key="", openai_model="")

    monkeypatch.setattr("app.config.get_settings", fake_settings)
    return ContractReviewService(OpenAICompatibleClient(fake_settings()))


EXPECTED_RULE_ONLY_TITLES_SORTED = [
    "存在单方免责条款",
    "未约定逾期付款责任",
    "源码交付边界不清",
    "知识产权转移条件过于笼统",
    "缺少保密与数据安全条款",
    "缺少解除与终止机制",
]


def test_analyze_contract_rules_only_stable(review_service_disabled_llm: ContractReviewService) -> None:
    r = review_service_disabled_llm.analyze_contract(GOLDEN_CONTRACT, "乙方", enhance_with_llm=False)
    assert r.llm_mode == "rules_only"
    assert r.contract_type == "技术开发/合作合同"
    assert r.role == "乙方"
    assert sorted(item.title for item in r.risk_items) == EXPECTED_RULE_ONLY_TITLES_SORTED


def test_analyze_contract_deferred_skips_llm(review_service_disabled_llm: ContractReviewService) -> None:
    r = review_service_disabled_llm.analyze_contract(
        GOLDEN_CONTRACT,
        "乙方",
        enhance_with_llm=True,
        defer_llm=True,
    )
    assert r.llm_mode == "deferred"
    assert r.mock_reason is None
