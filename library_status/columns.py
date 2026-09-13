#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Calibre custom-column schema for YES24 Library Status."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnSpec:
    label: str
    name: str
    datatype: str
    is_multiple: bool = False
    display: dict = None

    @property
    def key(self):
        return "#" + self.label


COLUMN_SPECS = (
    ColumnSpec("yes24_status", "YES24 상태", "text"),
    ColumnSpec("yes24_rank_detail", "YES24 순위", "text"),
    ColumnSpec("yes24_best_rank", "YES24 최고순위", "int"),
    ColumnSpec("yes24_best_record", "YES24 최고기록", "text"),
    ColumnSpec("yes24_years", "YES24 기록연도", "text"),
    ColumnSpec(
        "yes24_checked",
        "YES24 확인일",
        "datetime",
        display={"date_format": "yyyy-MM-dd"},
    ),
)


class ColumnSchemaError(RuntimeError):
    pass


def inspect_columns(db):
    fm = db.field_metadata
    missing = []
    incompatible = []

    for spec in COLUMN_SPECS:
        meta = fm.get(spec.key)
        if meta is None:
            missing.append(spec)
            continue

        datatype = meta.get("datatype")
        is_multiple = bool(meta.get("is_multiple"))
        if datatype != spec.datatype or is_multiple != spec.is_multiple:
            incompatible.append((spec, datatype, is_multiple))

    return missing, incompatible


def create_missing_columns(db, missing):
    created = []
    for spec in missing:
        db.create_custom_column(
            spec.label,
            spec.name,
            spec.datatype,
            spec.is_multiple,
            editable=True,
            display=dict(spec.display or {}),
        )
        created.append(spec)
    return created


def validate_columns(db):
    missing, incompatible = inspect_columns(db)
    if incompatible:
        details = []
        for spec, datatype, is_multiple in incompatible:
            details.append(
                f"{spec.key}: expected {spec.datatype}/multiple={spec.is_multiple}, "
                f"found {datatype}/multiple={is_multiple}"
            )
        raise ColumnSchemaError("\n".join(details))
    return missing


def value_maps(summaries):
    maps = {spec.key: {} for spec in COLUMN_SPECS}

    for book_id, summary in summaries.items():
        maps["#yes24_status"][book_id] = summary["status"]
        maps["#yes24_rank_detail"][book_id] = summary["rank_detail"]
        maps["#yes24_best_rank"][book_id] = summary["best_rank"]
        maps["#yes24_best_record"][book_id] = summary["best_record"]
        maps["#yes24_years"][book_id] = summary["years"]
        maps["#yes24_checked"][book_id] = summary["checked_at"]

    return maps
