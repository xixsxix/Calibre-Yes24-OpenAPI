#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calibre 9.14 startup-safe wrapper for YES24 Library Status 0.3.2."""

from qt.core import QTimer, Qt

from calibre_plugins.yes24_library_status.ui import (
    Yes24LibraryStatusAction,
    auto_debug,
    database_signals,
)


class Yes24LibraryStatusAction032(Yes24LibraryStatusAction):
    """Install the database listener only after the main GUI has a current DB."""

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

    def initialization_complete(self):
        db = getattr(self.gui, "current_db", None)
        if db is None:
            auto_debug("initialization_complete; current_db unavailable")
            return
        auto_debug("initialization_complete; installing database listener")
        self._install_db_listener(getattr(db, "new_api", db))
