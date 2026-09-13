#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Static contract checks for the consolidated public 0.3.5 source."""

from pathlib import Path

root = Path(__file__).resolve().parent
ui = (root / "ui.py").read_text(encoding="utf-8")
init = (root / "__init__.py").read_text(encoding="utf-8")
build = (root / "build_plugin.py").read_text(encoding="utf-8")

for name, source in (("ui.py", ui), ("__init__.py", init), ("build_plugin.py", build)):
    compile(source, name, "exec")

required = (
    "EventType.metadata_changed",
    'field_name != "identifiers"',
    'clean_item_id(identifiers.get("yes24"))',
    'getattr(db, "server_library_id", getattr(db, "library_id", ""))',
    "database listener deferred until initialization_complete",
    "automatic identifier verify book_id=",
    "automatic identifiers changed during worker; requeued=",
    "class SnapshotCache",
    "STARTUP_PREFETCH_DELAY_MS = 5000",
    "SNAPSHOT_FRESH_TTL_SECONDS = 10 * 60",
    "SNAPSHOT_MAX_STALE_SECONDS = 30 * 60",
    "class SnapshotPrefetchWorker",
    "class CachedStatusWorker",
    "snapshot prefetch worker started",
    "snapshot cache hit age=",
    "snapshot cache miss; automatic worker falling back to live snapshot",
    "checked_at=checked_at",
    "worker_class = CachedStatusWorker",
    "worker_class = StatusWorker",
    "snapshot_cache.clear()",
    "auto_debug.log",
    "automatic refresh complete",
)
for needle in required:
    assert needle in ui, needle

# Startup prefetch must fetch only the public ranking snapshot. Local book
# targets are consumed later by CachedStatusWorker and never sent by prefetch.
prefetch_body = ui.split("class SnapshotPrefetchWorker", 1)[1].split(
    "class CachedStatusWorker", 1
)[0]
assert "client.snapshot" in prefetch_body
assert "self.targets" not in prefetch_body
assert "BookTarget(" not in prefetch_body

# The explicit manual action must stay on the live worker path.
start_refresh_body = ui.split("def _start_refresh(self, book_ids, automatic=False):", 1)[1]
assert "if automatic:" in start_refresh_body
assert "worker_class = CachedStatusWorker" in start_refresh_body
assert "worker_class = StatusWorker" in start_refresh_body

# Diagnostic logging must not serialize the API key or raw response bodies.
assert "api_key=" not in ui
assert "raw response" not in ui.lower()

# Public packaging is intentionally consolidated: no internal version-overlay
# modules are required in the release ZIP.
assert "version = (0, 3, 5)" in init
assert "yes24_library_status.ui:" in init
assert "Yes24LibraryStatusAction" in init
for legacy in ("ui_032.py", "ui_033.py", "ui_034.py", "ui_035.py"):
    assert legacy not in build

print("YES24 Library Status 0.3.5 public contract: OK")
