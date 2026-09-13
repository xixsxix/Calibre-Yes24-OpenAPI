# -*- coding: utf-8 -*-
"""Runtime extension for YES24 Metadata Source 0.5.4.

YES24 Library Status 0.3.6 refreshes a persistent storefront steady-seller cache in
Calibre's config directory. Metadata Source reads that local cache only; it does
not scrape YES24 during identify(). If the cache is missing or invalid, normal
metadata lookup still succeeds and the star tag is simply omitted.
"""

import json as _json_054
from pathlib import Path as _Path_054

from calibre.constants import config_dir as _config_dir_054

_STEADY_TAG_054 = "⭐스테디셀러"
_STEADY_CACHE_STATE_054 = {"signature": None, "item_ids": frozenset()}


def _steady_cache_path_054():
    return _Path_054(_config_dir_054) / "yes24_library_status" / "steady_seller.json"


def _load_steady_item_ids_054():
    path = _steady_cache_path_054()
    try:
        stat = path.stat()
        signature = (stat.st_mtime_ns, stat.st_size)
    except OSError:
        _STEADY_CACHE_STATE_054["signature"] = None
        _STEADY_CACHE_STATE_054["item_ids"] = frozenset()
        return _STEADY_CACHE_STATE_054["item_ids"]
    if _STEADY_CACHE_STATE_054["signature"] == signature:
        return _STEADY_CACHE_STATE_054["item_ids"]
    try:
        payload = _json_054.loads(path.read_text(encoding="utf-8"))
        values = payload.get("itemIds") if isinstance(payload, dict) else None
        if not isinstance(values, list):
            raise ValueError("itemIds missing")
        item_ids = frozenset(str(value) for value in values if str(value).isdigit())
    except Exception:
        item_ids = frozenset()
    _STEADY_CACHE_STATE_054["signature"] = signature
    _STEADY_CACHE_STATE_054["item_ids"] = item_ids
    return item_ids


_metadata_from_item_053 = Yes24._metadata_from_item.__func__


@classmethod
def _metadata_from_item_054(cls, item):
    mi = _metadata_from_item_053(cls, item)
    if mi is None:
        return None
    item_id = cls._clean_text((item or {}).get("itemId"))
    if item_id and item_id in _load_steady_item_ids_054():
        tags = list(getattr(mi, "tags", None) or [])
        if _STEADY_TAG_054 not in tags:
            tags.append(_STEADY_TAG_054)
        mi.tags = tags
    return mi


Yes24._metadata_from_item = _metadata_from_item_054
Yes24.version = (0, 5, 4)
