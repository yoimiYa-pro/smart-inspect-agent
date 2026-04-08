from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from tests.test_review_golden import GOLDEN_CONTRACT

client = TestClient(app)


def test_post_review_defer_llm() -> None:
    r = client.post(
        "/api/review",
        json={
            "text": GOLDEN_CONTRACT,
            "role": "乙方",
            "enhance_with_llm": True,
            "defer_llm": True,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["llm_mode"] == "deferred"
    assert body["contract_type"] == "租赁合同"
