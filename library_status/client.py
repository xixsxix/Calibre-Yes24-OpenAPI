#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""YES24 Category API client and status summarizer.

This module deliberately keeps the network layer separate from Calibre GUI/DB
code so ranking behavior can be tested without starting Calibre.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://apis.yes24.com/v1"
KST = timezone(timedelta(hours=9))
PAGE_SIZE = 100
MAX_PAGES = 100

ROOT_BOOK_CATEGORY_NAMES = ("국내도서", "외국도서", "eBook")

STATUS_ENDPOINTS = (
    ("realtime", "실시간베스트", "/category/bestsellerRealtime", None),
    ("overall", "종합베스트", "/category/bestseller", None),
    ("deal", "특가베스트", "/category/bestsellerDeal", None),
    ("steady", "스테디셀러", "/category/bestsellerSteady", None),
    ("daily", "일간베스트", "/category/bestsellerDaily", "daily"),
    ("monthly", "월간베스트", "/category/bestsellerMonthly", "monthly"),
)

STATUS_ORDER = tuple(row[0] for row in STATUS_ENDPOINTS)
STATUS_LABELS = {key: label for key, label, _path, _period in STATUS_ENDPOINTS}
STATUS_SHORT_LABELS = {
    "realtime": "실시간",
    "overall": "종합",
    "deal": "특가",
    "steady": "스테디",
    "daily": "일간",
    "monthly": "월간",
}


class Yes24ApiError(RuntimeError):
    """A YES24 request failed in a way that makes a refresh incomplete."""


@dataclass(frozen=True)
class Category:
    category_id: str
    name: str
    full_path: str


@dataclass(frozen=True)
class Observation:
    kind: str
    category_id: str
    category_name: str
    rank: int
    item_id: str
    isbn13: str
    period: str


@dataclass(frozen=True)
class BookTarget:
    book_id: int
    item_id: str = ""
    isbn13: str = ""


def clean_digits(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def clean_isbn13(value):
    digits = clean_digits(value)
    return digits if len(digits) == 13 else ""


def clean_item_id(value):
    digits = clean_digits(value)
    return digits if digits else ""


def yesterday_kst():
    return (datetime.now(KST).date() - timedelta(days=1))


def status_period(kind, reference_date=None):
    reference_date = reference_date or yesterday_kst()
    if kind == "daily":
        return reference_date.isoformat()
    if kind == "monthly":
        return reference_date.strftime("%Y-%m")
    return ""


class Yes24Client:
    def __init__(
        self,
        api_key,
        timeout=20,
        user_agent="Calibre-YES24-Library-Status/0.3.5",
        opener=None,
        sleep=time.sleep,
    ):
        self.api_key = str(api_key or "").strip()
        if not self.api_key:
            raise ValueError("YES24 API key is required")
        self.timeout = float(timeout)
        self.user_agent = user_agent
        self.opener = opener or urlopen
        self.sleep = sleep

    def _request_json(self, path, params=None, allow_empty_404=False):
        params = dict(params or {})
        url = BASE_URL + path
        if params:
            url += "?" + urlencode(params)

        req = Request(
            url,
            headers={
                "X-Api-Key": self.api_key,
                "Accept": "application/json",
                "User-Agent": self.user_agent,
            },
            method="GET",
        )

        try:
            with self.opener(req, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as err:
            body = b""
            try:
                body = err.read()
            except Exception:
                pass

            payload = None
            if body:
                try:
                    payload = json.loads(body.decode("utf-8", "replace"))
                except Exception:
                    payload = None

            error_code = payload.get("errorCode") if isinstance(payload, dict) else None
            if allow_empty_404 and err.code == 404 and error_code in ("BEST_001", "CATEGORY_001"):
                return {
                    "success": True,
                    "message": "empty",
                    "errorCode": error_code,
                    "data": {
                        "items": [],
                        "currentPage": int(params.get("page", 1)),
                        "pageSize": int(params.get("pageSize", PAGE_SIZE)),
                        "totalCount": 0,
                    },
                }
            raise Yes24ApiError(
                f"YES24 API HTTP {err.code}: {error_code or str(err)}"
            ) from err
        except URLError as err:
            raise Yes24ApiError(f"YES24 API network error: {err}") from err

        try:
            payload = json.loads(raw.decode("utf-8", "replace"))
        except Exception as err:
            raise Yes24ApiError("YES24 API returned invalid JSON") from err

        if not isinstance(payload, dict) or not payload.get("success"):
            if isinstance(payload, dict):
                code = payload.get("errorCode") or ""
                message = payload.get("message") or ""
                raise Yes24ApiError(
                    f"YES24 API error: {code} {message}".strip()
                )
            raise Yes24ApiError("YES24 API returned an unexpected response")

        return payload

    @staticmethod
    def _payload_items(payload):
        data = payload.get("data") if isinstance(payload, dict) else None
        items = data.get("items") if isinstance(data, dict) else None
        return items if isinstance(items, list) else []

    @staticmethod
    def _payload_count(payload):
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return 0
        try:
            return max(0, int(data.get("totalCount") or 0))
        except (TypeError, ValueError):
            return 0

    def categories(self):
        payload = self._request_json("/category/list")
        data = payload.get("data") if isinstance(payload, dict) else None
        rows = data.get("data") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise Yes24ApiError("YES24 category list has no data array")

        result = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            category_id = str(row.get("categoryId") or "").strip()
            name = str(row.get("categoryName") or "").strip()
            full_path = str(row.get("categoryFullPath") or "").strip()
            if category_id and name:
                result.append(Category(category_id, name, full_path))
        return result

    def root_book_categories(self):
        rows = self.categories()
        by_name = {}
        for row in rows:
            if row.full_path == row.name:
                by_name[row.name.lower()] = row

        result = []
        for wanted in ROOT_BOOK_CATEGORY_NAMES:
            found = by_name.get(wanted.lower())
            if found is not None:
                result.append(found)

        if not result:
            result.append(Category("001", "국내도서", "국내도서"))

        return result

    def _paged_items(self, path, category_id, extra_params=None, abort=None):
        extra_params = dict(extra_params or {})
        items = []
        page = 1

        while page <= MAX_PAGES:
            if abort is not None and abort.is_set():
                return items

            params = {
                "categoryId": category_id,
                "page": page,
                "pageSize": PAGE_SIZE,
            }
            params.update(extra_params)
            payload = self._request_json(
                path,
                params,
                allow_empty_404=True,
            )
            rows = self._payload_items(payload)
            total_count = self._payload_count(payload)

            if not rows:
                break

            items.extend(rows)
            if total_count and len(items) >= total_count:
                break
            if len(rows) < PAGE_SIZE:
                break

            page += 1
            self.sleep(0.05)

        if page > MAX_PAGES:
            raise Yes24ApiError(
                f"YES24 pagination exceeded safety limit for {path}"
            )

        return items

    def snapshot(self, abort=None, reference_date=None):
        """Fetch current ranking/status observations for book root categories."""
        reference_date = reference_date or yesterday_kst()
        date_text = reference_date.isoformat()
        categories = self.root_book_categories()
        observations = []

        for category in categories:
            for kind, _label, path, period_kind in STATUS_ENDPOINTS:
                if abort is not None and abort.is_set():
                    return observations

                extra = {}
                if period_kind in ("daily", "monthly"):
                    extra["date"] = date_text

                rows = self._paged_items(
                    path,
                    category.category_id,
                    extra,
                    abort=abort,
                )
                period = status_period(kind, reference_date)

                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    try:
                        rank = int(row.get("sortOrder"))
                    except (TypeError, ValueError):
                        continue
                    if rank <= 0:
                        continue

                    item_id = clean_item_id(row.get("itemId"))
                    isbn13 = clean_isbn13(row.get("isbn13"))
                    if not item_id and not isbn13:
                        continue

                    observations.append(
                        Observation(
                            kind=kind,
                            category_id=category.category_id,
                            category_name=category.name,
                            rank=rank,
                            item_id=item_id,
                            isbn13=isbn13,
                            period=period,
                        )
                    )

        return observations


def index_observations(observations):
    by_item = {}
    by_isbn = {}

    for obs in observations:
        if obs.item_id:
            by_item.setdefault(obs.item_id, []).append(obs)
        if obs.isbn13:
            by_isbn.setdefault(obs.isbn13, []).append(obs)

    return by_item, by_isbn


def match_observations(target, indexes):
    by_item, by_isbn = indexes

    if target.item_id and target.item_id in by_item:
        return list(by_item[target.item_id])
    if target.isbn13 and target.isbn13 in by_isbn:
        return list(by_isbn[target.isbn13])
    return []


def _best_per_kind(observations):
    best = {}
    for obs in observations:
        current = best.get(obs.kind)
        if current is None or obs.rank < current.rank:
            best[obs.kind] = obs
    return best


def summarize_observations(observations, checked_at=None):
    checked_at = checked_at or datetime.now().astimezone()
    best_by_kind = _best_per_kind(observations)

    status_parts = []
    rank_parts = []
    ordered = []
    for kind in STATUS_ORDER:
        obs = best_by_kind.get(kind)
        if obs is None:
            continue
        ordered.append(obs)
        status_parts.append(STATUS_LABELS[kind])

        short = STATUS_SHORT_LABELS[kind]
        if obs.period:
            rank_parts.append(f"{short} {obs.period}:{obs.rank}")
        else:
            rank_parts.append(f"{short}:{obs.rank}")

    if ordered:
        best_obs = min(
            ordered,
            key=lambda obs: (
                obs.rank,
                STATUS_ORDER.index(obs.kind),
            ),
        )
        best_rank = best_obs.rank
        best_record = STATUS_LABELS[best_obs.kind]
        if best_obs.period:
            best_record += f" {best_obs.period}"
        best_record += f" #{best_obs.rank}"

        years = sorted(
            {
                int(obs.period[:4])
                for obs in ordered
                if obs.period and len(obs.period) >= 4 and obs.period[:4].isdigit()
            }
        )
    else:
        best_rank = None
        best_record = ""
        years = []

    return {
        "status": "|".join(status_parts),
        "rank_detail": "|".join(rank_parts),
        "best_rank": best_rank,
        "best_record": best_record,
        "years": "|".join(str(year) for year in years),
        "checked_at": checked_at,
    }


def summarize_targets(targets, observations, checked_at=None):
    indexes = index_observations(observations)
    result = {}
    for target in targets:
        matched = match_observations(target, indexes)
        result[target.book_id] = summarize_observations(
            matched,
            checked_at=checked_at,
        )
    return result
