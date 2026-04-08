from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx

from app.config import Settings
from app.services.delilegal_client import DeliLegalClient


def _settings_with_deli() -> Settings:
    return Settings(
        delilegal_appid="test-appid",
        delilegal_secret="test-secret",
        delilegal_api_base="https://example.com",
    )


def test_search_laws_parses_records() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "success": True,
        "code": 0,
        "body": {
            "records": [
                {"lawId": "law-1", "title": "示例法规", "levelName": "法律", "timelinessName": "有效"},
            ]
        },
    }
    mock_resp.raise_for_status = MagicMock()
    mock_cm = MagicMock()
    mock_cm.post.return_value = mock_resp
    mock_cm.__enter__.return_value = mock_cm
    mock_cm.__exit__.return_value = None

    with patch("app.services.delilegal_client.httpx.Client", return_value=mock_cm):
        client = DeliLegalClient(_settings_with_deli())
        out = client.search_laws("合同 付款")

    assert len(out) == 1
    assert out[0]["law_id"] == "law-1"
    assert out[0]["title"] == "示例法规"
    assert out[0]["level_name"] == "法律"
    assert out[0]["timeliness_name"] == "有效"

    called_kw = mock_cm.post.call_args.kwargs
    assert called_kw["json"]["condition"]["fieldName"] == "semantic"
    headers = called_kw["headers"]
    assert headers["appid"] == "test-appid"
    assert headers["secret"] == "test-secret"


def test_search_laws_empty_on_http_error() -> None:
    mock_cm = MagicMock()
    mock_cm.post.side_effect = httpx.HTTPError("boom")
    mock_cm.__enter__.return_value = mock_cm
    mock_cm.__exit__.return_value = None

    with patch("app.services.delilegal_client.httpx.Client", return_value=mock_cm):
        client = DeliLegalClient(_settings_with_deli())
        out = client.search_laws("x")

    assert out == []


def test_get_law_info_parses_body() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "success": True,
        "code": 0,
        "body": {
            "title": "复函标题",
            "lawDetailContent": "正文第一段",
            "levelName": "司法解释",
            "timelinessName": "失效",
        },
    }
    mock_resp.raise_for_status = MagicMock()
    mock_cm = MagicMock()
    mock_cm.get.return_value = mock_resp
    mock_cm.__enter__.return_value = mock_cm
    mock_cm.__exit__.return_value = None

    with patch("app.services.delilegal_client.httpx.Client", return_value=mock_cm):
        client = DeliLegalClient(_settings_with_deli())
        out = client.get_law_info("id-9", merge=True)

    assert out is not None
    assert out["law_id"] == "id-9"
    assert out["title"] == "复函标题"
    assert out["law_detail_content"] == "正文第一段"
    assert out["level_name"] == "司法解释"
    args, kwargs = mock_cm.get.call_args
    assert kwargs["params"]["lawId"] == "id-9"
    assert kwargs["params"]["merge"] == "true"


def test_search_cases_parses_records_and_keyword_arr() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "success": True,
        "code": 0,
        "body": {
            "records": [
                {
                    "caseId": "c-1",
                    "caseTitle": "某劳动争议案",
                    "courtName": "某法院",
                    "caseNo": "（2020）民终1号",
                    "judgmentDate": "2020-01-01",
                },
            ]
        },
    }
    mock_resp.raise_for_status = MagicMock()
    mock_cm = MagicMock()
    mock_cm.post.return_value = mock_resp
    mock_cm.__enter__.return_value = mock_cm
    mock_cm.__exit__.return_value = None

    with patch("app.services.delilegal_client.httpx.Client", return_value=mock_cm):
        client = DeliLegalClient(_settings_with_deli())
        out = client.search_cases("上班途中车祸工伤案例")

    assert len(out) == 1
    assert out[0]["case_id"] == "c-1"
    assert out[0]["title"] == "某劳动争议案"
    assert out[0]["court_name"] == "某法院"
    assert out[0]["case_number"] == "（2020）民终1号"
    assert out[0]["judgment_date"] == "2020-01-01"

    called = mock_cm.post.call_args
    assert called.kwargs["json"]["condition"]["keywordArr"] == ["上班途中车祸工伤案例"]
    assert called.kwargs["json"]["sortField"] == "correlation"
    assert str(called.args[0]).endswith("/api/qa/v3/search/queryListCase")
    assert called.kwargs["headers"]["appid"] == "test-appid"


def test_search_cases_strips_em_tags_in_title() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "success": True,
        "code": 0,
        "body": {
            "records": [
                {
                    "caseId": "c-em",
                    "caseTitle": "甲与乙技术<em>合同</em>纠纷一案",
                    "courtName": "某法院",
                },
            ]
        },
    }
    mock_resp.raise_for_status = MagicMock()
    mock_cm = MagicMock()
    mock_cm.post.return_value = mock_resp
    mock_cm.__enter__.return_value = mock_cm
    mock_cm.__exit__.return_value = None

    with patch("app.services.delilegal_client.httpx.Client", return_value=mock_cm):
        client = DeliLegalClient(_settings_with_deli())
        out = client.search_cases("关键词")

    assert len(out) == 1
    assert "<em>" not in out[0]["title"]
    assert out[0]["title"] == "甲与乙技术合同纠纷一案"
