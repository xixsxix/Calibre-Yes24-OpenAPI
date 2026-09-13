#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Pure-Python tests for YES24 monthly history cache/merge behavior."""

from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from client import BookTarget, Category, Observation
from history import (
    HistoryCache,
    iter_completed_months,
    summarize_targets_with_history,
)


class HistoryCoreTests(unittest.TestCase):
    def test_completed_month_range_starts_at_2024(self):
        months = list(iter_completed_months(reference_date=date(2026, 9, 12)))
        self.assertEqual(months[0], date(2024, 1, 1))
        self.assertEqual(months[-1], date(2026, 8, 1))
        self.assertEqual(len(months), 32)

    def test_cache_stores_only_normalized_matching_fields(self):
        with TemporaryDirectory() as tmp:
            cache = HistoryCache(Path(tmp) / "history.sqlite3")
            category = Category("001", "국내도서", "국내도서")
            cache.store_month(
                category,
                "2025-04",
                [
                    {
                        "sortOrder": 3,
                        "itemId": 100,
                        "isbn13": "9780000000001",
                        "title": "not persisted",
                    }
                ],
            )
            rows = cache.load_for_targets(
                [BookTarget(1, item_id="100", isbn13="9780000000001")]
            )
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].period, "2025-04")
            self.assertEqual(rows[0].rank, 3)
            self.assertEqual(rows[0].item_id, "100")
            self.assertEqual(rows[0].isbn13, "9780000000001")

    def test_history_changes_peak_but_not_current_status(self):
        target = BookTarget(1, item_id="100", isbn13="9780000000001")
        current = [
            Observation("steady", "001", "국내도서", 16, "100", "9780000000001", ""),
            Observation("monthly", "001", "국내도서", 21, "100", "9780000000001", "2026-09"),
        ]
        history = [
            Observation("monthly", "001", "국내도서", 3, "100", "9780000000001", "2025-04")
        ]
        result = summarize_targets_with_history(
            [target],
            current,
            history,
            checked_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        )[1]

        self.assertEqual(result["status"], "스테디셀러|월간베스트")
        self.assertEqual(result["rank_detail"], "스테디:16|월간 2026-09:21")
        self.assertEqual(result["best_rank"], 3)
        self.assertEqual(result["best_record"], "월간베스트 2025-04 #3")
        self.assertEqual(result["years"], "2025|2026")


if __name__ == "__main__":
    unittest.main()
