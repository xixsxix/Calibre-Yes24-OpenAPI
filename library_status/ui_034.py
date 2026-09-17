#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calibre 9.14 identifier-stability wrapper for YES24 Library Status 0.3.4."""

from calibre_plugins.yes24_library_status.client import clean_isbn13, clean_item_id
from calibre_plugins.yes24_library_status.ui import auto_debug
from calibre_plugins.yes24_library_status.ui_033 import Yes24LibraryStatusAction033


class Yes24LibraryStatusAction034(Yes24LibraryStatusAction033):
    @staticmethod
    def _db_identifiers(db, book_id):
        identifiers = db.field_for("identifiers", book_id, {}) or {}
        if not isinstance(identifiers, dict):
            identifiers = {}
        return (
            clean_item_id(identifiers.get("yes24")),
            clean_isbn13(identifiers.get("isbn")),
        )

    def _refresh_finished(self, payload):
        automatic = bool(self._automatic)
        worker_targets = tuple(getattr(self._worker, "targets", ()) or ())
        changed_during_worker = []

        if automatic and worker_targets:
            db = self.gui.current_db.new_api
            summaries = (payload or {}).get("summaries") or {}
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

        result = super()._refresh_finished(payload)
        if automatic and changed_during_worker:
            self._pending_auto_ids.update(changed_during_worker)
            auto_debug(
                "automatic identifiers changed during worker; requeued="
                + repr(tuple(sorted(changed_during_worker)))
            )
            self._auto_timer.start()
        return result
