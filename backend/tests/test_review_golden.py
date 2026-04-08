from __future__ import annotations

import pytest

from app.services.llm_client import OpenAICompatibleClient
from app.services.review.service import ContractReviewService

# 与 frontend/src/data/contractExamples.js 中 contractExamples[0].text 保持完全一致
GOLDEN_CONTRACT = """第一条 房屋基本情况
出租人（甲方）将坐落于某市某区某路某号的成套住宅出租给承租人（乙方）居住使用。租赁期限自2024年6月1日起至2026年5月31日止。

第二条 租金及支付方式
月租金为人民币伍仟元整。乙方应于每月5日前支付当月租金，具体付款时间以甲方书面通知或内部审批结果为准；甲方有权根据管理需要暂缓出具发票或延期确认收款。

第三条 押金
乙方应于签约时向甲方支付押金人民币壹万元。租赁期满或合同解除后，押金是否退还及退还数额由甲方单方认定，乙方无异议。

第四条 房屋使用与维修
乙方应合理使用房屋及附属设施。房屋及设施设备需要维修的，由乙方先行垫付费用并负责联系维修，甲方不承担及时维修义务。因使用不当造成损坏的，由乙方承担全部赔偿责任。

第五条 转租与分租
未经甲方书面同意，乙方不得将房屋转租、分租或以其他方式交由第三人使用。

第六条 合同解除
甲方可根据自用或出售需要随时解除合同，乙方应在接到通知后15日内搬离，甲方不承担违约金或补偿责任。

第七条 违约责任
因本合同履行产生的任何争议、行政处罚或第三方向甲方主张的赔偿，均由乙方承担全部责任，甲方不承担任何责任。

第八条 争议解决
因本合同引起的或与本合同有关的争议，双方同意提交甲方所在地人民法院诉讼解决。"""


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
    "管辖地偏向单方所在地",
    "缺少保密与数据安全条款",
]


def test_analyze_contract_rules_only_stable(review_service_disabled_llm: ContractReviewService) -> None:
    r = review_service_disabled_llm.analyze_contract(GOLDEN_CONTRACT, "乙方", enhance_with_llm=False)
    assert r.llm_mode == "rules_only"
    assert r.contract_type == "租赁合同"
    assert r.role == "乙方"
    assert sorted(item.title for item in r.risk_items) == EXPECTED_RULE_ONLY_TITLES_SORTED
    assert all(len(item.law_references) == 0 for item in r.risk_items)
    assert all(len(item.case_references) == 0 for item in r.risk_items)


def test_analyze_contract_deferred_skips_llm(review_service_disabled_llm: ContractReviewService) -> None:
    r = review_service_disabled_llm.analyze_contract(
        GOLDEN_CONTRACT,
        "乙方",
        enhance_with_llm=True,
        defer_llm=True,
    )
    assert r.llm_mode == "deferred"
    assert r.mock_reason is None
