#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calibre GUI action for YES24 Library Status 0.3.5.

The public source is consolidated from the internally validated 0.3.2-0.3.5
runtime layers so users only need one readable implementation file.
"""

from datetime import datetime
from pathlib import Path
from threading import Event, Lock, Thread
import time

from qt.core import QObject, QProgressDialog, QTimer, Qt, pyqtSignal

from calibre.constants import config_dir
from calibre.db.listeners import EventType
from calibre.gui2 import error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import JSONConfig

from calibre_plugins.yes24_library_status.client import (
    BookTarget,
    Yes24ApiError,
    Yes24Client,
    clean_isbn13,
    clean_item_id,
)
from calibre_plugins.yes24_library_status.columns import (
    ColumnSchemaError,
    create_missing_columns,
    validate_columns,
    value_maps,
)
from calibre_plugins.yes24_library_status.history import (
    HistoryCache,
    HistoryCacheError,
    summarize_targets_with_history,
    sync_monthly_history,
)


STARTUP_PREFETCH_DELAY_MS = 5000
SNAPSHOT_FRESH_TTL_SECONDS = 10 * 60
SNAPSHOT_MAX_STALE_SECONDS = 30 * 60
SNAPSHOT_RETRY_DELAY_MS = 60 * 1000


def load_metadata_source_api_key():
    prefs = JSONConfig("metadata_sources/Yes24.json")
    return str(prefs.get("api_key") or "").strip()


def history_cache_path():
    return Path(config_dir) / "yes24_library_status" / "history.sqlite3"


def auto_debug_log_path():
    return Path(config_dir) / "yes24_library_status" / "auto_debug.log"


def auto_debug(message):
    """Write diagnostics without API keys or raw YES24 response bodies."""
    line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} [AUTO] {message}"
    try:
        print(line, flush=True)
    except Exception:
        pass
    try:
        path = auto_debug_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
    except Exception:
        pass


class DatabaseSignals(QObject):
    identifiers_changed = pyqtSignal(str, object)


database_signals = DatabaseSignals()


def database_changed(event_type, library_id, event_data):
    if event_type is not EventType.metadata_changed:
        return
    auto_debug(
        f"metadata_changed library_id={library_id!r} event_data={event_data!r}"
    )
    try:
        field_name, book_ids = event_data
    except Exception as err:
        auto_debug(f"metadata_changed unpack failed: {type(err).__name__}: {err}")
        return
    if field_name != "identifiers":
        auto_debug(f"metadata_changed ignored field={field_name!r}")
        return
    ids = tuple(book_ids or ())
    auto_debug(f"identifiers changed ids={ids!r}")
    database_signals.identifiers_changed.emit(str(library_id or ""), ids)


class WorkerSignals(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()


class StatusWorker(Thread):
    """Manual/live worker: always fetch the current ranking snapshot."""

    def __init__(self, api_key, targets, cache_path, abort, signals):
        super().__init__(name="YES24LibraryStatusWorker", daemon=True)
        self.api_key = api_key
        self.targets = tuple(targets)
        self.cache_path = Path(cache_path)
        self.abort = abort
        self.signals = signals

    def run(self):
        auto_debug(
            "worker started targets="
            + repr([(target.book_id, target.item_id, target.isbn13) for target in self.targets])
        )
        try:
            client = Yes24Client(self.api_key)
            current_observations = client.snapshot(abort=self.abort)
            if self.abort.is_set():
                auto_debug("worker cancelled after current snapshot")
                self.signals.cancelled.emit()
                return

            cache = HistoryCache(self.cache_path)
            historical_observations, history_stats = sync_monthly_history(
                client,
                self.targets,
                cache,
                abort=self.abort,
            )
            if self.abort.is_set():
                auto_debug("worker cancelled after history sync")
                self.signals.cancelled.emit()
                return

            summaries = summarize_targets_with_history(
                self.targets,
                current_observations,
                historical_observations,
                checked_at=datetime.now().astimezone(),
            )
            auto_debug(
                f"worker finished summaries={tuple(summaries)!r} history={history_stats!r}"
            )
            self.signals.finished.emit(
                {
                    "summaries": summaries,
                    "history": history_stats,
                }
            )
        except (Yes24ApiError, HistoryCacheError) as err:
            auto_debug(f"worker failed: {type(err).__name__}: {err}")
            self.signals.failed.emit(str(err))
        except Exception as err:
            import traceback

            auto_debug(f"worker crashed: {type(err).__name__}: {err}")
            self.signals.failed.emit(
                f"{type(err).__name__}: {err}\n\n{traceback.format_exc()}"
            )


class SnapshotCache:
    """Process-local current-status snapshot with acquisition time."""

    def __init__(self):
        self._lock = Lock()
        self._observations = None
        self._fetched_at = None
        self._stored_monotonic = None

    def store(self, observations, fetched_at=None):
        rows = tuple(observations or ())
        fetched_at = fetched_at or datetime.now().astimezone()
        with self._lock:
            self._observations = rows
            self._fetched_at = fetched_at
            self._stored_monotonic = time.monotonic()
        return len(rows)

    def read(self, max_age_seconds=None):
        with self._lock:
            if self._observations is None or self._stored_monotonic is None:
                return None
            age = max(0.0, time.monotonic() - self._stored_monotonic)
            if max_age_seconds is not None and age > float(max_age_seconds):
                return None
            return {
                "observations": self._observations,
                "fetched_at": self._fetched_at,
                "age_seconds": age,
            }

    def clear(self):
        with self._lock:
            self._observations = None
            self._fetched_at = None
            self._stored_monotonic = None


snapshot_cache = SnapshotCache()


class SnapshotPrefetchSignals(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()


class SnapshotPrefetchWorker(Thread):
    """Fetch public YES24 ranking lists without sending local book targets."""

    def __init__(self, api_key, abort, signals):
        super().__init__(name="YES24StatusSnapshotPrefetch", daemon=True)
        self.api_key = api_key
        self.abort = abort
        self.signals = signals

    def run(self):
        started = time.monotonic()
        auto_debug("snapshot prefetch worker started")
        try:
            client = Yes24Client(self.api_key)
            observations = client.snapshot(abort=self.abort)
            if self.abort.is_set():
                auto_debug("snapshot prefetch worker cancelled")
                self.signals.cancelled.emit()
                return
            fetched_at = datetime.now().astimezone()
            elapsed = time.monotonic() - started
            auto_debug(
                f"snapshot prefetch worker finished observations={len(observations)} "
                f"elapsed={elapsed:.3f}s"
            )
            self.signals.finished.emit(
                {
                    "observations": observations,
                    "fetched_at": fetched_at,
                    "elapsed": elapsed,
                }
            )
        except Yes24ApiError as err:
            auto_debug(f"snapshot prefetch worker failed: {type(err).__name__}: {err}")
            self.signals.failed.emit(str(err))
        except Exception as err:
            auto_debug(f"snapshot prefetch worker crashed: {type(err).__name__}: {err}")
            self.signals.failed.emit(f"{type(err).__name__}: {err}")


class CachedStatusWorker(StatusWorker):
    """Automatic worker that reuses the process-local current snapshot."""

    def run(self):
        started = time.monotonic()
        auto_debug(
            "cached worker started targets="
            + repr([(target.book_id, target.item_id, target.isbn13) for target in self.targets])
        )
        try:
            cached = snapshot_cache.read(SNAPSHOT_MAX_STALE_SECONDS)
            if cached is None:
                auto_debug("snapshot cache miss; automatic worker falling back to live snapshot")
                client = Yes24Client(self.api_key)
                current_observations = client.snapshot(abort=self.abort)
                checked_at = datetime.now().astimezone()
                if self.abort.is_set():
                    self.signals.cancelled.emit()
                    return
                snapshot_cache.store(current_observations, checked_at)
                cache_age = 0.0
                cache_source = "live-fallback"
            else:
                client = Yes24Client(self.api_key)
                current_observations = cached["observations"]
                checked_at = cached["fetched_at"]
                cache_age = cached["age_seconds"]
                cache_source = "memory"
                auto_debug(
                    f"snapshot cache hit age={cache_age:.1f}s "
                    f"observations={len(current_observations)}"
                )

            cache = HistoryCache(self.cache_path)
            historical_observations, history_stats = sync_monthly_history(
                client,
                self.targets,
                cache,
                abort=self.abort,
            )
            if self.abort.is_set():
                self.signals.cancelled.emit()
                return

            summaries = summarize_targets_with_history(
                self.targets,
                current_observations,
                historical_observations,
                checked_at=checked_at,
            )
            auto_debug(
                f"cached worker finished source={cache_source!r} age={cache_age:.1f}s "
                f"elapsed={time.monotonic() - started:.3f}s history={history_stats!r}"
            )
            self.signals.finished.emit(
                {
                    "summaries": summaries,
                    "history": history_stats,
                    "snapshot_cache": {
                        "source": cache_source,
                        "age_seconds": cache_age,
                        "fetched_at": checked_at,
                    },
                }
            )
        except (Yes24ApiError, HistoryCacheError) as err:
            auto_debug(f"cached worker failed: {type(err).__name__}: {err}")
            self.signals.failed.emit(str(err))
        except Exception as err:
            import traceback

            auto_debug(f"cached worker crashed: {type(err).__name__}: {err}")
            self.signals.failed.emit(
                f"{type(err).__name__}: {err}\n\n{traceback.format_exc()}"
            )


class Yes24LibraryStatusAction(InterfaceAction):
    name = "YES24 Library Status"
    action_spec = (
        "YES24 상태 갱신",
        None,
        "선택한 책의 YES24 현재 상태와 월별 베스트 이력을 갱신합니다.",
        None,
    )
    dont_add_to = frozenset(("context-menu-device",))

    def genesis(self):
        self.qaction.triggered.connect(self.refresh_selected)
        self._worker = None
        self._signals = None
        self._abort = None
        self._progress = None
        self._automatic = False
        self._pending_auto_ids = set()
        self._listening_db = None

        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.setInterval(500)
        self._auto_timer.timeout.connect(self._run_pending_auto_refresh)

        database_signals.identifiers_changed.connect(
            self._database_identifiers_changed,
            type=Qt.ConnectionType.QueuedConnection,
        )
        auto_debug(
            "action genesis; database listener deferred until initialization_complete"
        )

        self._snapshot_prefetch_worker = None
        self._snapshot_prefetch_abort = None
        self._snapshot_prefetch_signals = None

        self._snapshot_start_timer = QTimer(self)
        self._snapshot_start_timer.setSingleShot(True)
        self._snapshot_start_timer.setInterval(STARTUP_PREFETCH_DELAY_MS)
        self._snapshot_start_timer.timeout.connect(self._ensure_snapshot_prefetch)

        self._snapshot_refresh_timer = QTimer(self)
        self._snapshot_refresh_timer.setSingleShot(False)
        self._snapshot_refresh_timer.setInterval(SNAPSHOT_FRESH_TTL_SECONDS * 1000)
        self._snapshot_refresh_timer.timeout.connect(self._ensure_snapshot_prefetch)

        self._snapshot_retry_timer = QTimer(self)
        self._snapshot_retry_timer.setSingleShot(True)
        self._snapshot_retry_timer.setInterval(SNAPSHOT_RETRY_DELAY_MS)
        self._snapshot_retry_timer.timeout.connect(self._ensure_snapshot_prefetch)

    def initialization_complete(self):
        db = getattr(self.gui, "current_db", None)
        if db is None:
            auto_debug("initialization_complete; current_db unavailable")
        else:
            auto_debug("initialization_complete; installing database listener")
            self._install_db_listener(getattr(db, "new_api", db))

        auto_debug(
            f"0.3.5 startup snapshot prefetch scheduled delay={STARTUP_PREFETCH_DELAY_MS}ms"
        )
        self._snapshot_start_timer.start()

    def library_changed(self, db):
        self._pending_auto_ids.clear()
        auto_debug("library_changed; pending queue cleared")
        self._install_db_listener(getattr(db, "new_api", db))

    def _install_db_listener(self, db):
        if db is self._listening_db:
            auto_debug("listener install skipped: already listening to current db")
            return
        if self._listening_db is not None:
            try:
                self._listening_db.remove_listener(database_changed)
                auto_debug("listener removed from previous db")
            except Exception as err:
                auto_debug(f"listener removal failed: {type(err).__name__}: {err}")
        self._listening_db = db
        if db is not None:
            try:
                db.add_listener(database_changed, check_already_added=True)
                auto_debug(
                    "listener installed library_id="
                    + repr(str(getattr(db, "library_id", "") or ""))
                )
            except Exception as err:
                auto_debug(f"listener install failed: {type(err).__name__}: {err}")
                raise

    def _database_identifiers_changed(self, library_id, book_ids):
        auto_debug(
            f"identifier signal received library_id={library_id!r} "
            f"book_ids={tuple(book_ids or ())!r}"
        )
        db = self.gui.current_db.new_api
        current_event_library_id = str(
            getattr(db, "server_library_id", getattr(db, "library_id", "")) or ""
        )
        auto_debug(
            f"identifier signal library check event={library_id!r} "
            f"current_event={current_event_library_id!r}"
        )
        if library_id and current_event_library_id and library_id != current_event_library_id:
            auto_debug(
                "identifier signal ignored: library mismatch "
                f"current_event={current_event_library_id!r}"
            )
            return

        for book_id in book_ids or ():
            try:
                identifiers = db.field_for("identifiers", book_id, {}) or {}
            except Exception as err:
                auto_debug(
                    f"identifier read failed book_id={book_id!r}: "
                    f"{type(err).__name__}: {err}"
                )
                continue
            if not isinstance(identifiers, dict):
                auto_debug(
                    f"identifier read ignored book_id={book_id!r}: "
                    f"type={type(identifiers).__name__}"
                )
                continue

            item_id = clean_item_id(identifiers.get("yes24"))
            auto_debug(
                f"identifier read book_id={book_id!r} yes24={item_id!r} "
                f"keys={tuple(sorted(identifiers))!r}"
            )
            if item_id:
                self._pending_auto_ids.add(int(book_id))
                auto_debug(
                    f"queued book_id={int(book_id)!r} "
                    f"pending={tuple(sorted(self._pending_auto_ids))!r}"
                )

        if self._pending_auto_ids:
            auto_debug("auto timer started")
            self._auto_timer.start()
        else:
            auto_debug("no books queued after identifier event")

    @staticmethod
    def _db_identifiers(db, book_id):
        identifiers = db.field_for("identifiers", book_id, {}) or {}
        if not isinstance(identifiers, dict):
            identifiers = {}
        return (
            clean_item_id(identifiers.get("yes24")),
            clean_isbn13(identifiers.get("isbn")),
        )

    def _run_pending_auto_refresh(self):
        auto_debug(
            f"timer fired pending={tuple(sorted(self._pending_auto_ids))!r} "
            f"worker_alive={bool(self._worker is not None and self._worker.is_alive())}"
        )
        if not self._pending_auto_ids:
            return
        if self._worker is not None and self._worker.is_alive():
            auto_debug("timer deferred: worker still alive")
            self._auto_timer.start()
            return

        book_ids = sorted(self._pending_auto_ids)
        self._pending_auto_ids.clear()
        auto_debug(f"auto refresh dispatch ids={book_ids!r}")
        self._start_refresh(book_ids, automatic=True)

    def _status_message(self, message, timeout=5000):
        try:
            self.gui.status_bar.show_message(message, timeout)
        except Exception:
            pass

    def location_selected(self, loc):
        self.qaction.setEnabled(loc == "library")

    def _selected_book_ids(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        db = self.gui.current_db
        return [db.id(row.row()) for row in rows]

    def _targets_for_ids(self, book_ids):
        db = self.gui.current_db.new_api
        targets = []
        skipped = []

        for book_id in book_ids:
            identifiers = db.field_for("identifiers", book_id, {}) or {}
            if not isinstance(identifiers, dict):
                identifiers = {}

            item_id = clean_item_id(identifiers.get("yes24"))
            isbn13 = clean_isbn13(identifiers.get("isbn"))
            if not item_id and not isbn13:
                skipped.append(book_id)
                continue

            targets.append(
                BookTarget(
                    book_id=book_id,
                    item_id=item_id,
                    isbn13=isbn13,
                )
            )

        return targets, skipped

    def refresh_selected(self):
        book_ids = self._selected_book_ids()
        if not book_ids:
            return error_dialog(
                self.gui,
                "YES24 Library Status",
                "먼저 상태를 갱신할 책을 선택하세요.",
                show=True,
            )
        return self._start_refresh(book_ids, automatic=False)

    def _ensure_snapshot_prefetch(self):
        cached = snapshot_cache.read(SNAPSHOT_FRESH_TTL_SECONDS)
        if cached is not None:
            auto_debug(f"snapshot prefetch skipped: cache fresh age={cached['age_seconds']:.1f}s")
            if not self._snapshot_refresh_timer.isActive():
                self._snapshot_refresh_timer.start()
            return

        worker = self._snapshot_prefetch_worker
        if worker is not None and worker.is_alive():
            auto_debug("snapshot prefetch skipped: worker already running")
            return

        api_key = load_metadata_source_api_key()
        if not api_key:
            auto_debug("snapshot prefetch skipped: Metadata Source API Key missing")
            return

        self._snapshot_prefetch_abort = Event()
        self._snapshot_prefetch_signals = SnapshotPrefetchSignals()
        self._snapshot_prefetch_signals.finished.connect(self._snapshot_prefetch_finished)
        self._snapshot_prefetch_signals.failed.connect(self._snapshot_prefetch_failed)
        self._snapshot_prefetch_signals.cancelled.connect(self._snapshot_prefetch_cancelled)
        self._snapshot_prefetch_worker = SnapshotPrefetchWorker(
            api_key,
            self._snapshot_prefetch_abort,
            self._snapshot_prefetch_signals,
        )
        self._status_message("YES24 상태 캐시 준비 중…", 3000)
        auto_debug("snapshot prefetch dispatch")
        self._snapshot_prefetch_worker.start()

    def _snapshot_prefetch_finished(self, payload):
        count = snapshot_cache.store(
            (payload or {}).get("observations") or (),
            (payload or {}).get("fetched_at"),
        )
        elapsed = float((payload or {}).get("elapsed") or 0.0)
        auto_debug(f"snapshot cache stored observations={count} elapsed={elapsed:.3f}s")
        self._status_message("YES24 상태 캐시 준비 완료", 3000)
        self._snapshot_prefetch_worker = None
        self._snapshot_prefetch_abort = None
        self._snapshot_prefetch_signals = None
        if not self._snapshot_refresh_timer.isActive():
            self._snapshot_refresh_timer.start()

    def _snapshot_prefetch_failed(self, message):
        auto_debug(f"snapshot cache prefetch failed; retry scheduled: {message}")
        self._snapshot_prefetch_worker = None
        self._snapshot_prefetch_abort = None
        self._snapshot_prefetch_signals = None
        self._snapshot_retry_timer.start()

    def _snapshot_prefetch_cancelled(self):
        auto_debug("snapshot cache prefetch cancelled")
        self._snapshot_prefetch_worker = None
        self._snapshot_prefetch_abort = None
        self._snapshot_prefetch_signals = None

    def _start_refresh(self, book_ids, automatic=False):
        auto_debug(f"refresh requested automatic={bool(automatic)!r} ids={list(book_ids)!r}")
        if self._worker is not None and self._worker.is_alive():
            if automatic:
                self._pending_auto_ids.update(book_ids)
                auto_debug(
                    f"refresh deferred to active worker pending={tuple(sorted(self._pending_auto_ids))!r}"
                )
                self._auto_timer.start()
                return None
            return info_dialog(
                self.gui,
                "YES24 Library Status",
                "이미 YES24 상태 조회가 진행 중입니다.",
                show=True,
            )

        api_key = load_metadata_source_api_key()
        if not api_key:
            auto_debug("refresh stopped: Metadata Source API Key missing")
            if automatic:
                self._status_message(
                    "YES24 상태 자동 갱신 건너뜀: Metadata Source API Key가 없습니다.",
                    7000,
                )
                return None
            return error_dialog(
                self.gui,
                "YES24 API Key 필요",
                "YES24 Metadata Source 플러그인에 API Key를 먼저 설정하세요.",
                show=True,
            )

        db = self.gui.current_db.new_api
        try:
            missing = validate_columns(db)
        except ColumnSchemaError as err:
            auto_debug(f"refresh stopped: column schema conflict: {err}")
            if automatic:
                self._status_message(
                    "YES24 상태 자동 갱신 건너뜀: 사용자 정의 컬럼 형식 충돌",
                    7000,
                )
                return None
            return error_dialog(
                self.gui,
                "YES24 사용자 정의 컬럼 충돌",
                "기존 사용자 정의 컬럼의 형식이 YES24 Library Status와 다릅니다.",
                det_msg=str(err),
                show=True,
            )

        if missing:
            auto_debug(
                "refresh stopped: missing columns=" + repr([spec.key for spec in missing])
            )
            if automatic:
                self._status_message(
                    "YES24 상태 자동 갱신 대기: 먼저 수동 실행으로 사용자 정의 컬럼을 생성하세요.",
                    8000,
                )
                return None
            created = create_missing_columns(db, missing)
            names = ", ".join(spec.key for spec in created)
            return info_dialog(
                self.gui,
                "YES24 사용자 정의 컬럼 생성 완료",
                (
                    "필요한 사용자 정의 컬럼을 만들었습니다.\n\n"
                    f"{names}\n\n"
                    "Calibre가 새 컬럼을 완전히 다시 읽도록 프로그램을 한 번 "
                    "재시작한 뒤 YES24 상태 갱신을 다시 실행하세요."
                ),
                show=True,
            )

        targets, skipped = self._targets_for_ids(book_ids)
        auto_debug(
            f"targets prepared target_ids={[target.book_id for target in targets]!r} skipped={skipped!r}"
        )
        if not targets:
            if automatic:
                auto_debug("automatic refresh stopped: no usable identifiers")
                return None
            return error_dialog(
                self.gui,
                "YES24 식별자 없음",
                (
                    "선택한 책에 YES24 상품번호 또는 ISBN13이 없습니다. "
                    "먼저 메타데이터를 확인하세요."
                ),
                show=True,
            )

        if automatic:
            fresh = snapshot_cache.read(SNAPSHOT_FRESH_TTL_SECONDS)
            stale = snapshot_cache.read(SNAPSHOT_MAX_STALE_SECONDS)
            if fresh is None and stale is not None:
                self._ensure_snapshot_prefetch()
            worker_class = CachedStatusWorker
        else:
            worker_class = StatusWorker

        self._automatic = bool(automatic)
        self._abort = Event()
        self._signals = WorkerSignals()
        self._signals.finished.connect(self._refresh_finished)
        self._signals.failed.connect(self._refresh_failed)
        self._signals.cancelled.connect(self._refresh_cancelled)

        if automatic:
            self._status_message(
                f"YES24 상태 자동 갱신 중: {len(targets)}권",
                3000,
            )
        else:
            self._progress = QProgressDialog(
                (
                    "YES24 현재 상태와 월별 베스트 이력을 조회하고 있습니다…\n"
                    "첫 이력 수집은 2024-01부터 캐시를 만들기 때문에 시간이 걸릴 수 있습니다."
                ),
                "취소",
                0,
                0,
                self.gui,
            )
            self._progress.setWindowTitle("YES24 Library Status")
            self._progress.setWindowModality(Qt.WindowModality.WindowModal)
            self._progress.canceled.connect(self._abort.set)
            self._progress.show()

        self._worker = worker_class(
            api_key,
            targets,
            history_cache_path(),
            self._abort,
            self._signals,
        )
        self._worker._skipped_count = len(skipped)
        auto_debug(f"worker thread starting automatic={self._automatic!r}")
        self._worker.start()
        return None

    def _close_progress(self):
        if self._progress is not None:
            self._progress.close()
            self._progress.deleteLater()
            self._progress = None

    def _clear_worker(self):
        self._worker = None
        self._signals = None
        self._abort = None
        self._automatic = False

    def _refresh_finished(self, payload):
        self._close_progress()
        automatic = bool(self._automatic)
        worker_targets = tuple(getattr(self._worker, "targets", ()) or ())
        summaries = (payload or {}).get("summaries") or {}
        history = (payload or {}).get("history") or {}
        db = self.gui.current_db.new_api
        changed_during_worker = []

        if automatic and worker_targets:
            for target in worker_targets:
                started = (target.item_id, target.isbn13)
                try:
                    current = self._db_identifiers(db, target.book_id)
                except Exception as err:
                    auto_debug(
                        f"automatic identifier verify failed book_id={target.book_id!r}: "
                        f"{type(err).__name__}: {err}"
                    )
                    continue

                summary = summaries.get(target.book_id) or {}
                auto_debug(
                    f"automatic identifier verify book_id={target.book_id!r} "
                    f"started={started!r} current={current!r} "
                    f"status={summary.get('status', '')!r} "
                    f"best_rank={summary.get('best_rank')!r} "
                    f"years={summary.get('years', '')!r}"
                )
                if started != current:
                    changed_during_worker.append(int(target.book_id))

        auto_debug(
            f"refresh finished signal automatic={automatic!r} summaries={tuple(summaries)!r}"
        )

        try:
            changed = set()
            for field, mapping in value_maps(summaries).items():
                field_changed = set(db.set_field(field, mapping))
                changed |= field_changed
                auto_debug(
                    f"field write field={field!r} books={tuple(sorted(mapping))!r} "
                    f"changed={tuple(sorted(field_changed))!r}"
                )
        except Exception as err:
            import traceback

            auto_debug(f"field write failed: {type(err).__name__}: {err}")
            self._clear_worker()
            if self._pending_auto_ids:
                self._auto_timer.start()
            if automatic:
                self._status_message(
                    f"YES24 상태 자동 기록 실패: {err}",
                    8000,
                )
                return None
            return error_dialog(
                self.gui,
                "YES24 상태 기록 실패",
                "YES24 상태를 사용자 정의 컬럼에 기록하지 못했습니다.",
                det_msg=f"{err}\n\n{traceback.format_exc()}",
                show=True,
            )

        auto_debug(f"all field writes completed changed={tuple(sorted(changed))!r}")
        skipped_count = getattr(self._worker, "_skipped_count", 0)
        book_ids = list(summaries)
        if book_ids:
            current_row = self.gui.library_view.currentIndex().row()
            self.gui.library_view.model().refresh_ids(book_ids, current_row)
            self.gui.tags_view.recount()

        current_found = sum(1 for row in summaries.values() if row["status"])
        current_missing = len(summaries) - current_found

        categories = ", ".join(history.get("categories") or []) or "-"
        downloaded = int(history.get("downloaded") or 0)
        reused = int(history.get("reused") or 0)
        history_books = int(history.get("matched_books") or 0)

        self._clear_worker()
        message = (
            f"{len(summaries)}권을 확인했습니다.\n"
            f"현재 랭킹/스테디 있음: {current_found}권\n"
            f"현재 목록에서 확인되지 않음: {current_missing}권\n"
            f"과거 월별 기록 있음: {history_books}권\n\n"
            f"월별 이력 대상: {categories}\n"
            f"월별 캐시 신규 수집: {downloaded}개\n"
            f"월별 캐시 재사용: {reused}개"
        )
        if skipped_count:
            message += f"\n식별자 없어 건너뜀: {skipped_count}권"

        if automatic:
            auto_debug(
                f"automatic refresh complete summaries={len(summaries)} "
                f"current={current_found} history={history_books}"
            )
            self._status_message(
                (
                    f"YES24 상태 자동 갱신 완료: {len(summaries)}권 "
                    f"(현재 {current_found}, 이력 {history_books})"
                ),
                6000,
            )
        else:
            info_dialog(
                self.gui,
                "YES24 상태 갱신 완료",
                message,
                show=True,
            )

        if automatic and changed_during_worker:
            self._pending_auto_ids.update(changed_during_worker)
            auto_debug(
                "automatic identifiers changed during worker; requeued="
                + repr(tuple(sorted(changed_during_worker)))
            )

        if self._pending_auto_ids:
            auto_debug(
                f"pending queue remains after completion: {tuple(sorted(self._pending_auto_ids))!r}"
            )
            self._auto_timer.start()
        return None

    def _refresh_failed(self, message):
        self._close_progress()
        automatic = self._automatic
        auto_debug(f"refresh failed signal automatic={automatic!r}: {message}")
        self._clear_worker()
        if self._pending_auto_ids:
            self._auto_timer.start()
        if automatic:
            self._status_message(
                f"YES24 상태 자동 갱신 실패: {message}",
                8000,
            )
            return None
        error_dialog(
            self.gui,
            "YES24 상태 조회 실패",
            "YES24 상태/이력 조회가 완료되지 않아 어떤 컬럼도 변경하지 않았습니다.",
            det_msg=message,
            show=True,
        )
        return None

    def _refresh_cancelled(self):
        self._close_progress()
        automatic = self._automatic
        auto_debug(f"refresh cancelled signal automatic={automatic!r}")
        self._clear_worker()
        if self._pending_auto_ids:
            self._auto_timer.start()
        if automatic:
            self._status_message("YES24 상태 자동 갱신 취소", 5000)
            return None
        info_dialog(
            self.gui,
            "YES24 상태 갱신 취소",
            "사용자가 작업을 취소했습니다. 컬럼은 변경하지 않았습니다.",
            show=True,
        )
        return None

    def shutting_down(self):
        auto_debug("0.3.5 shutting down; stopping snapshot timers/workers")
        for timer in (
            getattr(self, "_snapshot_start_timer", None),
            getattr(self, "_snapshot_refresh_timer", None),
            getattr(self, "_snapshot_retry_timer", None),
        ):
            if timer is not None:
                timer.stop()
        abort = getattr(self, "_snapshot_prefetch_abort", None)
        if abort is not None:
            abort.set()
        snapshot_cache.clear()
        try:
            if self._listening_db is not None:
                self._listening_db.remove_listener(database_changed)
        except Exception:
            pass
        return None
