#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit contract for the storefront steady-seller cache."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from steady_cache import extract_item_ids, steady_page_url, write_cache_atomic


html = '''
<a href="/product/goods/123">A</a>
<a href="https://www.yes24.com/product/goods/456">B</a>
<a href="/product/goods/123">duplicate</a>
'''
assert extract_item_ids(html) == ("123", "456")
assert steady_page_url(1).endswith("categoryNumber=001")
assert "pageNumber=2" in steady_page_url(2)

with TemporaryDirectory() as tmp:
    path = Path(tmp) / "steady_seller.json"
    payload = {"itemIds": ["123", "456"], "uniqueItemCount": 2}
    write_cache_atomic(path, payload)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == payload

print("YES24 storefront steady cache contract: OK")
