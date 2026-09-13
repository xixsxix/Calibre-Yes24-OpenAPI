#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Normalized monthly YES24 bestseller history cache.

The cache deliberately stores only the minimal fields needed for matching and
history summaries. Raw YES24 response bodies are never persisted.
"""

from contextlib import closing
from datetime import date, datetime, timedelta
from pathlib import Path
import sqlite3

try:
    from calibre_plugins.yes24_library_status.client import (
        KST,
        Observation,
        Yes24ApiError,
        clean_isbn13,
        clean_item_id,
        index_observations,
        match_observations,
        summarize_observations,
    )
except ImportError:  # local pure-Python tests
    from client import (
        KST,
        Observation,
        Yes24ApiError,
        clean_isbn13,
        clean_item_id,
        index_observations,
        match_observations,
        summarize_observations,
    )


HISTORY_START_YEAR = 2024
MONTHLY_PATH = "/category/bestsellerMonthly"
MIN_REQUEST_GAP = 0.12


class HistoryCacheError(RuntimeError):
    pass


def latest_completed_month(reference_date=None):
    reference_date = reference_date or datetime.now(KST).date()
    if isinstance(reference_date, datetime):
        reference_date = reference_date.date()
    first_this_month = reference_date.replace(day=1)
    return (first_this_month - timedelta(days=1)).replace(day=1)


def iter_completed_months(start_year=HISTORY_START_YEAR, reference_date=None):
    end = latest_completed_month(reference_date)
    current = date(start_year, 1, 1)
    while current <= end:
        yield current
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)


def _root_name_for_item(item, roots):
    goods_type = str(item.get("goodsType") or "").strip().lower()
    goods_sort = str(item.get("goodsSortNm") or "").strip().lower()

    for category in roots:
        wanted = category.name.lower()
        if goods_type == wanted:
            return category.name
        if (
            goods_sort == wanted
            or goods_sort.startswith(wanted + "-")
            or goods_sort.startswith(wanted + "/")
            or goods_sort.startswith(wanted + " >")
        ):
            return category.name
    return ""


def _detail_item_for_target(client, target):
    attempts = []
    if target.item_id:
        attempts.append(("ItemId", target.item_id))
    if target.isbn13:
        attempts.append(("ISBN13", target.isbn13))

    for search_type, query in attempts:
        try:
            payload = client._request_json(
                "/goods/itemDetail",
                {
                    "searchType": search_type,
                    "query": query,
                    "detail": "N",
                },
            )
        except Yes24ApiError:
            client.sleep(MIN_REQUEST_GAP)
            continue
        client.sleep(MIN_REQUEST_GAP)
        rows = client._payload_items(payload)
        if rows:
            return rows[0]
    return None


def required_root_categories(client, targets, abort=None):
    roots = client.root_book_categories()
    by_name = {row.name: row for row in roots}
    wanted_names = set()
    unresolved = False

    seen = set()
    for target in targets:
        if abort is not None and abort.is_set():
            return []
        key = (target.item_id, target.isbn13)
        if key in seen:
            continue
        seen.add(key)

        item = _detail_item_for_target(client, target)
        if item is None:
            unresolved = True
            continue
        name = _root_name_for_item(item, roots)
        if not name:
            unresolved = True
            continue
        wanted_names.add(name)

    if unresolved or not wanted_names:
        return list(roots)
    return [by_name[name] for name in by_name if name in wanted_names]


class HistoryCache:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        connection = sqlite3.connect(str(self.path), timeout=30)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _ensure_schema(self):
        try:
            with closing(self._connect()) as db:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS monthly_fetch (
                        period TEXT NOT NULL,
                        category_id TEXT NOT NULL,
                        category_name TEXT NOT NULL,
                        fetched_at TEXT NOT NULL,
                        row_count INTEGER NOT NULL,
                        PRIMARY KEY (period, category_id)
                    );

                    CREATE TABLE IF NOT EXISTS monthly_observation (
                        period TEXT NOT NULL,
                        category_id TEXT NOT NULL,
                        rank INTEGER NOT NULL,
                        item_id TEXT NOT NULL DEFAULT '',
                        isbn13 TEXT NOT NULL DEFAULT '',
                        PRIMARY KEY (
                            period, category_id, rank, item_id, isbn13
                        )
                    );

                    CREATE INDEX IF NOT EXISTS idx_yes24_history_item
                    ON monthly_observation(item_id);

                    CREATE INDEX IF NOT EXISTS idx_yes24_history_isbn
                    ON monthly_observation(isbn13);
                    """
                )
                db.commit()
        except sqlite3.Error as err:
            raise HistoryCacheError(f"YES24 history cache init failed: {err}") from err

    def has_month(self, category_id, period):
        with closing(self._connect()) as db:
            row = db.execute(
                "SELECT 1 FROM monthly_fetch WHERE period=? AND category_id=?",
                (period, str(category_id)),
            ).fetchone()
        return row is not None

    def store_month(self, category, period, rows, fetched_at=None):
        fetched_at = fetched_at or datetime.now(KST).isoformat()
        normalized = []
        for row in rows or []:
            if not isinstance(row, dict):
                continue
            try:
                rank = int(row.get("sortOrder"))
            except (TypeError, ValueError):
                continue
            if rank <= 0:
                continue
            item_id = clean_item_id(row.get("itemId"))
            isbn13 = clean_isbn13(row.get("isbn13"))
            if not item_id and not isbn13:
                continue
            normalized.append(
                (period, str(category.category_id), rank, item_id, isbn13)
            )

        try:
            with closing(self._connect()) as db:
                db.execute(
                    "DELETE FROM monthly_observation WHERE period=? AND category_id=?",
                    (period, str(category.category_id)),
                )
                db.executemany(
                    """
                    INSERT OR REPLACE INTO monthly_observation
                    (period, category_id, rank, item_id, isbn13)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    normalized,
                )
                db.execute(
                    """
                    INSERT OR REPLACE INTO monthly_fetch
                    (period, category_id, category_name, fetched_at, row_count)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        period,
                        str(category.category_id),
                        category.name,
                        fetched_at,
                        len(normalized),
                    ),
                )
                db.commit()
        except sqlite3.Error as err:
            raise HistoryCacheError(f"YES24 history cache write failed: {err}") from err

    def load_for_targets(self, targets):
        item_ids = sorted({target.item_id for target in targets if target.item_id})
        isbns = sorted({target.isbn13 for target in targets if target.isbn13})
        clauses = []
        params = []

        if item_ids:
            clauses.append(
                "o.item_id IN (" + ",".join("?" for _ in item_ids) + ")"
            )
            params.extend(item_ids)
        if isbns:
            clauses.append(
                "o.isbn13 IN (" + ",".join("?" for _ in isbns) + ")"
            )
            params.extend(isbns)
        if not clauses:
            return []

        query = (
            "SELECT o.period, o.category_id, f.category_name, o.rank, "
            "o.item_id, o.isbn13 "
            "FROM monthly_observation o "
            "JOIN monthly_fetch f "
            "ON f.period=o.period AND f.category_id=o.category_id "
            "WHERE " + " OR ".join("(" + part + ")" for part in clauses)
        )

        try:
            with closing(self._connect()) as db:
                rows = db.execute(query, params).fetchall()
        except sqlite3.Error as err:
            raise HistoryCacheError(f"YES24 history cache read failed: {err}") from err

        return [
            Observation(
                kind="monthly",
                category_id=str(category_id),
                category_name=str(category_name or ""),
                rank=int(rank),
                item_id=str(item_id or ""),
                isbn13=str(isbn13 or ""),
                period=str(period),
            )
            for period, category_id, category_name, rank, item_id, isbn13 in rows
        ]


def sync_monthly_history(client, targets, cache, abort=None, reference_date=None):
    categories = required_root_categories(client, targets, abort=abort)
    periods = [
        month.strftime("%Y-%m")
        for month in iter_completed_months(reference_date=reference_date)
    ]

    downloaded = 0
    reused = 0
    base_sleep = client.sleep

    def paced_sleep(seconds=0):
        base_sleep(max(float(seconds or 0), MIN_REQUEST_GAP))

    client.sleep = paced_sleep
    try:
        for category in categories:
            for period in periods:
                if abort is not None and abort.is_set():
                    return [], {
                        "downloaded": downloaded,
                        "reused": reused,
                        "categories": [row.name for row in categories],
                        "matched_books": 0,
                    }

                if cache.has_month(category.category_id, period):
                    reused += 1
                    continue

                rows = client._paged_items(
                    MONTHLY_PATH,
                    category.category_id,
                    {"date": period + "-01"},
                    abort=abort,
                )
                if abort is not None and abort.is_set():
                    return [], {
                        "downloaded": downloaded,
                        "reused": reused,
                        "categories": [row.name for row in categories],
                        "matched_books": 0,
                    }
                cache.store_month(category, period, rows)
                downloaded += 1
                paced_sleep()
    finally:
        client.sleep = base_sleep

    observations = cache.load_for_targets(targets)
    indexes = index_observations(observations)
    matched_books = sum(
        1 for target in targets if match_observations(target, indexes)
    )
    return observations, {
        "downloaded": downloaded,
        "reused": reused,
        "categories": [row.name for row in categories],
        "matched_books": matched_books,
    }


def _years_from_observations(observations):
    years = sorted(
        {
            int(obs.period[:4])
            for obs in observations
            if obs.period
            and len(obs.period) >= 4
            and obs.period[:4].isdigit()
        }
    )
    return "|".join(str(year) for year in years)


def summarize_targets_with_history(
    targets,
    current_observations,
    historical_observations,
    checked_at=None,
):
    current_indexes = index_observations(current_observations)
    history_indexes = index_observations(historical_observations)
    result = {}

    for target in targets:
        current = match_observations(target, current_indexes)
        history = match_observations(target, history_indexes)
        combined_observations = current + history

        summary = summarize_observations(current, checked_at=checked_at)
        combined = summarize_observations(
            combined_observations,
            checked_at=checked_at,
        )
        summary["best_rank"] = combined["best_rank"]
        summary["best_record"] = combined["best_record"]
        summary["years"] = _years_from_observations(combined_observations)
        result[target.book_id] = summary

    return result
