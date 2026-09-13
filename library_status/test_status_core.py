#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Pure-Python regression checks for YES24 Library Status core logic."""

from datetime import datetime, timezone
import unittest

from client import (
    BookTarget,
    Observation,
    clean_isbn13,
    clean_item_id,
    summarize_targets,
)


class StatusCoreTests(unittest.TestCase):
    def test_identifier_cleaning(self):
        self.assertEqual(clean_isbn13("978-89-1234-567-8"), "9788912345678")
        self.assertEqual(clean_isbn13("123"), "")
        self.assertEqual(clean_item_id(" 123456 "), "123456")

    def test_item_id_wins_over_isbn(self):
        observations = [
            Observation("steady", "001", "국내도서", 9, "100", "9780000000001", ""),
            Observation("monthly", "001", "국내도서", 2, "200", "9780000000001", "2026-09"),
        ]
        target = BookTarget(1, item_id="100", isbn13="9780000000001")
        result = summarize_targets(
            [target],
            observations,
            checked_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        )[1]
        self.assertEqual(result["status"], "스테디셀러")
        self.assertEqual(result["best_rank"], 9)

    def test_summary_order_and_pipe_separator(self):
        observations = [
            Observation("monthly", "001", "국내도서", 20, "100", "9780000000001", "2026-09"),
            Observation("realtime", "001", "국내도서", 4, "100", "9780000000001", ""),
            Observation("steady", "001", "국내도서", 11, "100", "9780000000001", ""),
        ]
        result = summarize_targets(
            [BookTarget(1, item_id="100")],
            observations,
            checked_at=datetime(2026, 9, 12, tzinfo=timezone.utc),
        )[1]
        self.assertEqual(result["status"], "실시간베스트|스테디셀러|월간베스트")
        self.assertEqual(result["rank_detail"], "실시간:4|스테디:11|월간 2026-09:20")
        self.assertEqual(result["best_rank"], 4)
        self.assertEqual(result["best_record"], "실시간베스트 #4")
        self.assertEqual(result["years"], "2026")

    def test_no_status_is_explicitly_checkable_by_checked_at(self):
        checked = datetime(2026, 9, 12, tzinfo=timezone.utc)
        result = summarize_targets(
            [BookTarget(1, isbn13="9780000000001")],
            [],
            checked_at=checked,
        )[1]
        self.assertEqual(result["status"], "")
        self.assertIsNone(result["best_rank"])
        self.assertEqual(result["checked_at"], checked)


if __name__ == "__main__":
    unittest.main()
