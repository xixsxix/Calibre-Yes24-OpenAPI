#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build an installable Calibre plugin ZIP from yes24.py."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "yes24.py"
OUTPUT = ROOT / "Yes24.zip"


def main():
    if not SOURCE.exists():
        raise SystemExit(f"Source file not found: {SOURCE}")

    source_text = SOURCE.read_text(encoding="utf-8")

    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("__init__.py", source_text)

    print(f"Built: {OUTPUT}")


if __name__ == "__main__":
    main()
