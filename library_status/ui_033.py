#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calibre 9.14 listener-id-safe wrapper for YES24 Library Status 0.3.3."""

from calibre_plugins.yes24_library_status.client import clean_item_id
from calibre_plugins.yes24_library_status.ui import auto_debug
from calibre_plugins.yes24_library_status.ui_032 import Yes24LibraryStatusAction032


class Yes24LibraryStatusAction033(Yes24LibraryStatusAction032):
    """Compare DB listener events against Calibre's server_library_id."""

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
