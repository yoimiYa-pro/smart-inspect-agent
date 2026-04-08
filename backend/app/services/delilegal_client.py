from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)

# 得理等检索接口常在标题中带 <em> 等高亮标签，需剥离后再返回给前端
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html_tags(value: str, *, collapse_ws: bool = True) -> str:
    if not value:
        return value
    cleaned = _TAG_RE.sub("", value)
    if collapse_ws:
        return re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _first_str(*candidates: Any) -> str:
    for c in candidates:
        if c is None:
            continue
        s = str(c).strip()
        if s:
            return s
    return ""


def _parse_list_items(body: Any) -> list[dict[str, Any]]:
    """Normalize various list shapes under API body into raw row dicts."""
    if body is None:
        return []
    if isinstance(body, list):
        return [x for x in body if isinstance(x, dict)]
    if not isinstance(body, dict):
        return []
    for key in ("records", "list", "rows", "data", "items", "content"):
        raw = body.get(key)
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
    return []


def _row_to_summary(row: dict[str, Any]) -> dict[str, Any] | None:
    law_id = _first_str(
        row.get("lawId"),
        row.get("law_id"),
        row.get("id"),
        row.get("lawsId"),
    )
    title = _strip_html_tags(_first_str(row.get("title"), row.get("lawTitle"), row.get("name")))
    if not law_id or not title:
        return None
    out: dict[str, Any] = {
        "law_id": law_id,
        "title": title,
    }
    ln = _strip_html_tags(_first_str(row.get("levelName"), row.get("level_name")))
    if ln:
        out["level_name"] = ln
    tn = _strip_html_tags(_first_str(row.get("timelinessName"), row.get("timeliness_name")))
    if tn:
        out["timeliness_name"] = tn
    return out


def _row_to_case_summary(row: dict[str, Any]) -> dict[str, Any] | None:
    case_id = _first_str(
        row.get("caseId"),
        row.get("case_id"),
        row.get("id"),
        row.get("judgmentId"),
        row.get("judgementId"),
        row.get("docId"),
    )
    title = _strip_html_tags(
        _first_str(
            row.get("title"),
            row.get("caseTitle"),
            row.get("caseName"),
            row.get("name"),
            row.get("judgmentTitle"),
        )
    )
    if not case_id or not title:
        return None
    out: dict[str, Any] = {"case_id": case_id, "title": title}
    cn = _strip_html_tags(_first_str(row.get("courtName"), row.get("court"), row.get("court_name")))
    if cn:
        out["court_name"] = cn
    num = _strip_html_tags(
        _first_str(
            row.get("caseNumber"),
            row.get("caseNo"),
            row.get("case_number"),
            row.get("ah"),
        )
    )
    if num:
        out["case_number"] = num
    jd = _strip_html_tags(
        _first_str(
            row.get("judgmentDate"),
            row.get("judgementDate"),
            row.get("judgeDate"),
            row.get("publishDate"),
            row.get("judgment_date"),
        )
    )
    if jd:
        out["judgment_date"] = jd
    return out


class DeliLegalClient:
    """得理开放平台：法规检索、法规详情、案例列表检索。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._base = settings.delilegal_api_base.rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "appid": self.settings.delilegal_appid,
            "secret": self.settings.delilegal_secret,
        }

    def search_laws(
        self,
        keywords: str | list[str],
        *,
        page_no: int = 1,
        page_size: int = 5,
        sort_field: str = "correlation",
        sort_order: str = "desc",
        field_name: str = "semantic",
    ) -> list[dict[str, Any]]:
        if isinstance(keywords, str):
            kw_list = [keywords] if keywords.strip() else []
        else:
            kw_list = [str(k).strip() for k in keywords if str(k).strip()]
        if not kw_list:
            return []
        payload: dict[str, Any] = {
            "pageNo": page_no,
            "pageSize": page_size,
            "sortField": sort_field,
            "sortOrder": sort_order,
            "condition": {"keywords": kw_list, "fieldName": field_name},
        }
        url = f"{self._base}/api/qa/v3/search/queryListLaw"
        timeout = httpx.Timeout(self.settings.delilegal_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("delilegal search_laws failed: %s", exc, exc_info=True)
            return []

        if not isinstance(data, dict):
            return []
        if data.get("success") is False and data.get("code") not in (0, None):
            logger.warning("delilegal search_laws business error: %s", data)
            return []

        body = data.get("body")
        summaries: list[dict[str, Any]] = []
        for row in _parse_list_items(body):
            parsed = _row_to_summary(row)
            if parsed:
                summaries.append(parsed)
        return summaries

    def search_cases(
        self,
        keyword_arr: str | list[str],
        *,
        page_no: int = 1,
        page_size: int = 5,
        sort_field: str = "correlation",
        sort_order: str = "desc",
    ) -> list[dict[str, Any]]:
        if isinstance(keyword_arr, str):
            arr = [keyword_arr.strip()] if keyword_arr.strip() else []
        else:
            arr = [str(k).strip() for k in keyword_arr if str(k).strip()]
        if not arr:
            return []
        payload: dict[str, Any] = {
            "pageNo": page_no,
            "pageSize": page_size,
            "sortField": sort_field,
            "sortOrder": sort_order,
            "condition": {"keywordArr": arr},
        }
        url = f"{self._base}/api/qa/v3/search/queryListCase"
        timeout = httpx.Timeout(self.settings.delilegal_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("delilegal search_cases failed: %s", exc, exc_info=True)
            return []

        if not isinstance(data, dict):
            return []
        if data.get("success") is False and data.get("code") not in (0, None):
            logger.warning("delilegal search_cases business error: %s", data)
            return []

        body = data.get("body")
        summaries: list[dict[str, Any]] = []
        for row in _parse_list_items(body):
            parsed = _row_to_case_summary(row)
            if parsed:
                summaries.append(parsed)
        return summaries

    def get_law_info(self, law_id: str, *, merge: bool = True) -> dict[str, Any] | None:
        lid = (law_id or "").strip()
        if not lid:
            return None
        params = {"lawId": lid, "merge": "true" if merge else "false"}
        url = f"{self._base}/api/qa/v3/search/lawInfo"
        timeout = httpx.Timeout(self.settings.delilegal_timeout_seconds)
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params, headers=self._headers())
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("delilegal get_law_info failed: %s", exc, exc_info=True)
            return None

        if not isinstance(data, dict):
            return None
        if data.get("success") is False and data.get("code") not in (0, None):
            logger.warning("delilegal get_law_info business error: %s", data)
            return None

        body = data.get("body")
        if not isinstance(body, dict):
            return None

        raw_content = str(body.get("lawDetailContent") or "").strip()
        out: dict[str, Any] = {
            "law_id": lid,
            "title": _strip_html_tags(_first_str(body.get("title"))),
            "law_detail_content": _strip_html_tags(raw_content, collapse_ws=False),
            "level_name": _strip_html_tags(_first_str(body.get("levelName"))),
            "timeliness_name": _strip_html_tags(_first_str(body.get("timelinessName"))),
            "publisher_name": _strip_html_tags(_first_str(body.get("publisherName"))),
            "publish_date": _strip_html_tags(_first_str(body.get("publishDate"))),
            "active_date": _strip_html_tags(_first_str(body.get("activeDate"))),
            "issued_no": _strip_html_tags(_first_str(body.get("issuedNo"))),
            "laws_id": _first_str(body.get("lawsId")),
        }
        return out
