# -*- coding: utf-8 -*-
"""Runtime overlay for YES24 Metadata Source 0.5.5."""

import html as _html_055
import re as _re_055
from concurrent.futures import ThreadPoolExecutor as _ThreadPoolExecutor_055

_CATEGORY_DISPLAY_RE_055 = _re_055.compile(r"/product/category/display/(\d+)", _re_055.I)
_CATEGORY_ANCHOR_RE_055 = _re_055.compile(r"<a\b[^>]*?href\s*=\s*['\"]([^'\"]*?/product/category/display/(\d+)[^'\"]*)['\"][^>]*>(.*?)</a>", _re_055.I | _re_055.S)
_CATEGORY_STOP_LABELS_055 = frozenset({"수상내역 및 미디어 추천 분류", "이 상품의 태그", "소개", "책소개", "목차", "저자 소개", "저자소개", "품목정보", "회원리뷰", "리뷰", "이 상품의 이벤트"})
_CATEGORY_ROOT_LABELS_055 = frozenset({"도서", "국내도서", "외국도서", "ebook"})


def _valid_isbn13_055(value):
    if not _re_055.fullmatch(r"97[89]\d{10}", value or ""):
        return False
    digits = [int(ch) for ch in value]
    check = (10 - (sum(digits[:12:2]) + 3 * sum(digits[1:12:2])) % 10) % 10
    return check == digits[12]


def _valid_isbn10_055(value):
    if not _re_055.fullmatch(r"\d{9}[\dXx]", value or ""):
        return False
    total = 0
    for index, ch in enumerate(value.upper()):
        digit = 10 if ch == "X" else int(ch)
        total += (10 - index) * digit
    return total % 11 == 0


def _extract_search_isbn_055(value):
    if value is None:
        return None
    text = str(value)
    for match in _re_055.finditer(r"97[89](?:[\s-]*\d){10}", text):
        candidate = _re_055.sub(r"\D", "", match.group(0))
        if _valid_isbn13_055(candidate):
            return candidate
    for match in _re_055.finditer(r"\d(?:[\s-]*\d){8}[\s-]*[\dXx]", text):
        candidate = _re_055.sub(r"[^0-9Xx]", "", match.group(0)).upper()
        if _valid_isbn10_055(candidate):
            return candidate
    return None


@staticmethod
def _get_isbn_055(identifiers):
    if not identifiers:
        return None
    value = identifiers.get("isbn")
    values = value if isinstance(value, (list, tuple)) else (value,)
    for candidate in values:
        isbn = _extract_search_isbn_055(candidate)
        if isbn:
            return isbn
    return None


def _tag_text_055(cls, value):
    return cls._clean_text(value)


def _is_html_element_055(element):
    return isinstance(getattr(element, "tag", None), str)


def _element_text_055(cls, element):
    if not _is_html_element_055(element):
        return ""
    try:
        return _tag_text_055(cls, " ".join(element.itertext()))
    except (TypeError, ValueError):
        return ""


def _category_rows_to_tags_055(categories):
    if not categories:
        return []
    shallowest = min(len(code) for _label, code in categories)
    maximum_depth = shallowest + 3
    tags = []
    for label, code in categories:
        if len(code) <= maximum_depth and label not in tags:
            tags.append(label)
    return tags


def _raw_category_window_055(html_text, marker_end):
    window = html_text[marker_end:marker_end + 20000]
    start = window.find("카테고리 분류")
    if start < 0 or start > 5000:
        return ""
    window = window[start + len("카테고리 분류"):]
    stops = [window.find(label) for label in _CATEGORY_STOP_LABELS_055 if window.find(label) >= 0]
    return window[:min(stops)] if stops else window


def _raw_related_category_rows_055(cls, html_text):
    if not html_text or "관련분류" not in html_text:
        return []
    candidates = []
    for marker in _re_055.finditer("관련분류", html_text):
        window = _raw_category_window_055(html_text, marker.end())
        if not window:
            continue
        rows = []
        for match in _CATEGORY_ANCHOR_RE_055.finditer(window):
            code = match.group(2)
            label = _re_055.sub(r"<[^>]+>", " ", match.group(3))
            label = _tag_text_055(cls, _html_055.unescape(label))
            if not label or label.lower() in _CATEGORY_ROOT_LABELS_055:
                continue
            row = (label, code)
            if row not in rows:
                rows.append(row)
        if rows:
            candidates.append(rows)
    return min(candidates, key=len) if candidates else []


@classmethod
def _extract_related_category_tags_055(cls, html_text):
    if not html_text:
        return []
    categories = []
    try:
        from lxml import html as _lxml_html_055
        root = _lxml_html_055.fromstring(html_text)
        elements = list(root.iter())
        marker_index = None
        for index, element in enumerate(elements):
            if not _is_html_element_055(element):
                continue
            if element.tag.lower() in {"script", "style"}:
                continue
            own_text = _tag_text_055(cls, getattr(element, "text", None))
            full_text = _element_text_055(cls, element)
            if own_text == "관련분류" or full_text == "관련분류":
                marker_index = index
                break
        if marker_index is not None:
            for element in elements[marker_index + 1:marker_index + 1200]:
                if not _is_html_element_055(element):
                    continue
                tag = element.tag.lower()
                text = _element_text_055(cls, element)
                own_text = _tag_text_055(cls, getattr(element, "text", None))
                if text in _CATEGORY_STOP_LABELS_055 or own_text in _CATEGORY_STOP_LABELS_055:
                    break
                if tag != "a":
                    continue
                match = _CATEGORY_DISPLAY_RE_055.search(str(element.get("href") or "").strip())
                if not match:
                    continue
                if not text or text.lower() in _CATEGORY_ROOT_LABELS_055:
                    continue
                row = (text, match.group(1))
                if row not in categories:
                    categories.append(row)
    except Exception:
        categories = []
    tags = _category_rows_to_tags_055(categories)
    if tags:
        return tags
    return _category_rows_to_tags_055(_raw_related_category_rows_055(cls, html_text))


def _merge_category_tags_055(mi, category_tags):
    tags = list(getattr(mi, "tags", None) or [])
    for tag in category_tags or ():
        if tag and tag not in tags:
            tags.append(tag)
    mi.tags = tags
    return mi


def _fetch_category_tags_055(self, item_id, timeout):
    item_id = str(item_id or "").strip()
    if not item_id.isdigit():
        return item_id, [], None
    url = f"https://www.yes24.com/product/goods/{item_id}"
    try:
        browser = self._prepare_browser(api=False, referer="https://www.yes24.com/")
        raw = browser.open_novisit(url, timeout=min(float(timeout or 30), 8.0)).read()
        tags = self._extract_related_category_tags_055(raw.decode("utf-8", "replace"))
        return item_id, tags, None
    except Exception as err:
        return item_id, [], err


_identify_054 = Yes24.identify


def _identify_055(self, log, result_queue, abort, title=None, authors=None, identifiers={}, timeout=30):
    class _CaptureQueue055:
        def __init__(self):
            self.items = []
        def put(self, value):
            self.items.append(value)

    capture = _CaptureQueue055()
    _identify_054(self, log, capture, abort, title=title, authors=authors, identifiers=identifiers, timeout=timeout)
    if not capture.items:
        return

    candidate_ids = []
    item_by_id = {}
    for mi in capture.items:
        try:
            item_id = str(mi.get_identifiers().get("yes24") or "").strip()
        except Exception:
            item_id = ""
        if item_id and item_id not in item_by_id:
            candidate_ids.append(item_id)
            item_by_id[item_id] = []
        if item_id:
            item_by_id[item_id].append(mi)

    fetched = {}
    if candidate_ids and not abort.is_set():
        with _ThreadPoolExecutor_055(max_workers=min(4, len(candidate_ids))) as pool:
            futures = [pool.submit(_fetch_category_tags_055, self, item_id, timeout) for item_id in candidate_ids]
            for future in futures:
                if abort.is_set():
                    break
                item_id, tags, err = future.result()
                if err is not None:
                    log.warning(f"YES24 related-category lookup failed for item={item_id}: {err}")
                elif not tags:
                    log(f"YES24 related categories: item={item_id}, no category tags extracted")
                fetched[item_id] = tags

    for item_id, metadata_rows in item_by_id.items():
        tags = fetched.get(item_id) or []
        if tags:
            log(f"YES24 related categories: item={item_id}, tags={', '.join(tags)}")
        for mi in metadata_rows:
            _merge_category_tags_055(mi, tags)
    for mi in capture.items:
        result_queue.put(mi)


Yes24._get_isbn = _get_isbn_055
Yes24._extract_related_category_tags_055 = _extract_related_category_tags_055
Yes24.identify = _identify_055
Yes24.version = (0, 5, 5)
