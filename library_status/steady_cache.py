#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Persistent YES24 storefront steady-seller cache."""

from datetime import datetime
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

STEADYSELLER_URL = "https://www.yes24.com/product/category/steadyseller"
CATEGORY_NUMBER = "001"
EXPECTED_MIN_ITEM_IDS = 1000
MAX_PAGES = 40
REQUEST_DELAY_SECONDS = 0.25
REQUEST_TIMEOUT_SECONDS = 20.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)
GOODS_LINK_RE = re.compile(r"(?i)(?:https?://(?:www\.)?yes24\.com)?/product/goods/(\d+)")


class SteadyCacheError(RuntimeError):
    pass


def steady_cache_path(config_dir):
    return Path(config_dir) / "yes24_library_status" / "steady_seller.json"


def steady_page_url(page, category_number=CATEGORY_NUMBER):
    params = {"categoryNumber": str(category_number)}
    if int(page) > 1:
        params["pageNumber"] = str(int(page))
    return STEADYSELLER_URL + "?" + urlencode(params)


def extract_item_ids(html):
    text = html.decode("utf-8", "replace") if isinstance(html, bytes) else str(html or "")
    return tuple(sorted(set(GOODS_LINK_RE.findall(text)), key=int))


def _fetch_html(url, timeout, opener):
    request = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }, method="GET")
    with opener(request, timeout=float(timeout)) as response:
        return response.read()


def collect_steady_item_ids(abort=None, expected_min=EXPECTED_MIN_ITEM_IDS, max_pages=MAX_PAGES,
                            timeout=REQUEST_TIMEOUT_SECONDS, delay=REQUEST_DELAY_SECONDS,
                            opener=None, sleep=time.sleep):
    opener = opener or urlopen
    unique = set()
    pages = []
    previous_page_ids = None
    for page in range(1, int(max_pages) + 1):
        if abort is not None and abort.is_set():
            return None
        try:
            raw = _fetch_html(steady_page_url(page), timeout, opener)
        except Exception as err:
            raise SteadyCacheError(f"steady-seller page {page} request failed: {err}") from err
        page_ids = extract_item_ids(raw)
        if not page_ids:
            raise SteadyCacheError(f"steady-seller page {page} contained no goods links")
        if previous_page_ids == page_ids:
            raise SteadyCacheError(f"steady-seller page {page} repeated the previous page")
        before = len(unique)
        unique.update(page_ids)
        pages.append({"page": page, "itemCount": len(page_ids), "newItemCount": len(unique)-before,
                      "totalUnique": len(unique)})
        if len(unique) >= int(expected_min):
            break
        previous_page_ids = page_ids
        if delay:
            sleep(float(delay))
    else:
        raise SteadyCacheError(
            f"steady-seller cache did not reach {expected_min} unique itemIds within {max_pages} pages (got {len(unique)})"
        )
    if abort is not None and abort.is_set():
        return None
    return {
        "schemaVersion": 1,
        "sourceUrl": STEADYSELLER_URL,
        "categoryNumber": CATEGORY_NUMBER,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "pagesFetched": len(pages),
        "uniqueItemCount": len(unique),
        "expectedMinimum": int(expected_min),
        "itemIds": sorted(unique, key=int),
        "pages": pages,
    }


def write_cache_atomic(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def refresh_steady_cache(path, abort=None, **kwargs):
    payload = collect_steady_item_ids(abort=abort, **kwargs)
    if payload is None:
        return None
    write_cache_atomic(path, payload)
    return payload
