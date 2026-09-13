#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Static packaging contract for Metadata Source 0.5.4 steady tag bridge."""

from pathlib import Path

root = Path(__file__).resolve().parent
patch = (root / "yes24_054_patch.py").read_text(encoding="utf-8")
build = (root / "build_plugin.py").read_text(encoding="utf-8")
compile(patch, "yes24_054_patch.py", "exec")

for needle in (
    '"⭐스테디셀러"',
    '"yes24_library_status" / "steady_seller.json"',
    "Yes24.version = (0, 5, 4)",
    "_load_steady_item_ids_054",
):
    assert needle in patch, needle

assert 'PATCH = ROOT / "yes24_054_patch.py"' in build
assert "Runtime version: Yes24 (0, 5, 4)" in build
print("YES24 Metadata Source 0.5.4 steady tag contract: OK")
