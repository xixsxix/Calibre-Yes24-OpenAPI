#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

root = Path(__file__).resolve().parent
init = (root / "__init__.py").read_text(encoding="utf-8")
ui = (root / "ui.py").read_text(encoding="utf-8")
ui_036 = (root / "ui_036.py").read_text(encoding="utf-8")
steady = (root / "steady_cache.py").read_text(encoding="utf-8")
build = (root / "build_plugin.py").read_text(encoding="utf-8")

for name, text in (
    ("__init__.py", init),
    ("ui.py", ui),
    ("ui_036.py", ui_036),
    ("steady_cache.py", steady),
    ("build_plugin.py", build),
):
    compile(text, name, "exec")

for needle in (
    "version = (0, 3, 6)",
    "yes24_library_status.ui_036",
    "Yes24LibraryStatusAction036",
):
    assert needle in init, needle

for needle in (
    "STARTUP_PREFETCH_DELAY_MS = 5000",
    "SNAPSHOT_FRESH_TTL_SECONDS = 10 * 60",
    "snapshot prefetch worker started",
    "snapshot cache hit age=",
):
    assert needle in ui, needle

for needle in (
    "STEADY_CACHE_STARTUP_DELAY_MS = 12 * 1000",
    "steady-seller cache worker started",
    "steady-seller cache ready items=",
    "previous cache preserved",
):
    assert needle in ui_036, needle

for needle in (
    "STEADYSELLER_URL",
    "EXPECTED_MIN_ITEM_IDS = 1000",
    "write_cache_atomic",
    "steady_seller.json",
):
    assert needle in steady, needle

for name in (
    "__init__.py",
    "ui.py",
    "ui_036.py",
    "client.py",
    "columns.py",
    "history.py",
    "steady_cache.py",
):
    assert f'"{name}"' in build, name

print("YES24 Library Status 0.3.6 public contract: OK")
