#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Startup storefront steady-seller cache for YES24 Library Status 0.3.7."""

from threading import Event, Thread
import time

from qt.core import QObject, QTimer, pyqtSignal
from calibre.constants import config_dir
from calibre_plugins.yes24_library_status.steady_cache import (
    SteadyCacheError,
    refresh_steady_cache,
    steady_cache_path,
)
from calibre_plugins.yes24_library_status.ui import Yes24LibraryStatusAction, auto_debug

STEADY_CACHE_STARTUP_DELAY_MS = 12 * 1000
STEADY_CACHE_RETRY_DELAY_MS = 60 * 1000


class SteadyCacheSignals(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()


class SteadyCacheWorker(Thread):
    def __init__(self, cache_path, abort, signals):
        super().__init__(name="YES24SteadySellerCache", daemon=True)
        self.cache_path = cache_path
        self.abort = abort
        self.signals = signals

    def run(self):
        started = time.monotonic()
        auto_debug("steady-seller cache worker started")
        try:
            payload = refresh_steady_cache(self.cache_path, abort=self.abort)
            if payload is None or self.abort.is_set():
                auto_debug("steady-seller cache worker cancelled")
                self.signals.cancelled.emit()
                return
            auto_debug(
                "steady-seller cache worker finished "
                f"items={payload.get('uniqueItemCount', 0)} "
                f"pages={payload.get('pagesFetched', 0)} "
                f"elapsed={time.monotonic() - started:.3f}s"
            )
            self.signals.finished.emit(payload)
        except SteadyCacheError as err:
            auto_debug(f"steady-seller cache worker failed: {err}")
            self.signals.failed.emit(str(err))
        except Exception as err:
            auto_debug(f"steady-seller cache worker crashed: {type(err).__name__}: {err}")
            self.signals.failed.emit(f"{type(err).__name__}: {err}")


class Yes24LibraryStatusAction036(Yes24LibraryStatusAction):
    """Refresh the shared storefront steady-seller cache after Calibre starts."""

    def genesis(self):
        super().genesis()
        icon = get_icons("images/icon.png", "YES24 Library Status")
        self.qaction.setIcon(icon)
        auto_debug(f"toolbar icon loaded null={icon.isNull()!r}")
        self._steady_cache_worker = None
        self._steady_cache_abort = None
        self._steady_cache_signals = None
        self._steady_cache_retry_used = False
        self._steady_cache_start_timer = QTimer(self)
        self._steady_cache_start_timer.setSingleShot(True)
        self._steady_cache_start_timer.setInterval(STEADY_CACHE_STARTUP_DELAY_MS)
        self._steady_cache_start_timer.timeout.connect(self._start_steady_cache_refresh)
        self._steady_cache_retry_timer = QTimer(self)
        self._steady_cache_retry_timer.setSingleShot(True)
        self._steady_cache_retry_timer.setInterval(STEADY_CACHE_RETRY_DELAY_MS)
        self._steady_cache_retry_timer.timeout.connect(self._start_steady_cache_refresh)

    def initialization_complete(self):
        super().initialization_complete()
        auto_debug(
            "0.3.7 storefront steady-seller cache scheduled "
            f"delay={STEADY_CACHE_STARTUP_DELAY_MS}ms"
        )
        self._steady_cache_start_timer.start()

    def _start_steady_cache_refresh(self):
        worker = self._steady_cache_worker
        if worker is not None and worker.is_alive():
            auto_debug("steady-seller cache refresh skipped: worker already running")
            return
        self._steady_cache_abort = Event()
        self._steady_cache_signals = SteadyCacheSignals()
        self._steady_cache_signals.finished.connect(self._steady_cache_finished)
        self._steady_cache_signals.failed.connect(self._steady_cache_failed)
        self._steady_cache_signals.cancelled.connect(self._steady_cache_cancelled)
        self._steady_cache_worker = SteadyCacheWorker(
            steady_cache_path(config_dir), self._steady_cache_abort, self._steady_cache_signals
        )
        auto_debug("steady-seller cache refresh dispatch")
        self._steady_cache_worker.start()

    def _clear_steady_cache_worker(self):
        self._steady_cache_worker = None
        self._steady_cache_abort = None
        self._steady_cache_signals = None

    def _steady_cache_finished(self, payload):
        count = int((payload or {}).get("uniqueItemCount") or 0)
        pages = int((payload or {}).get("pagesFetched") or 0)
        auto_debug(f"steady-seller cache ready items={count} pages={pages}")
        self._status_message(f"YES24 스테디셀러 태그 캐시 준비 완료 ({count}권)", 4000)
        self._clear_steady_cache_worker()

    def _steady_cache_failed(self, message):
        auto_debug(f"steady-seller cache refresh failed; previous cache preserved: {message}")
        self._clear_steady_cache_worker()
        if not self._steady_cache_retry_used:
            self._steady_cache_retry_used = True
            auto_debug("steady-seller cache retry scheduled")
            self._steady_cache_retry_timer.start()

    def _steady_cache_cancelled(self):
        auto_debug("steady-seller cache refresh cancelled")
        self._clear_steady_cache_worker()

    def shutting_down(self):
        auto_debug("0.3.7 shutting down; stopping steady-seller cache worker")
        for timer in (
            getattr(self, "_steady_cache_start_timer", None),
            getattr(self, "_steady_cache_retry_timer", None),
        ):
            if timer is not None:
                timer.stop()
        abort = getattr(self, "_steady_cache_abort", None)
        if abort is not None:
            abort.set()
        return super().shutting_down()
