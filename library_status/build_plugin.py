#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build YES24 Library Status as an installable Calibre plugin ZIP."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Yes24LibraryStatus.zip"

SOURCE_FILES = (
    "__init__.py",
    "ui.py",
    "client.py",
    "columns.py",
    "history.py",
)


def main():
    missing = [name for name in SOURCE_FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("Missing source files: " + ", ".join(missing))

    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        for name in SOURCE_FILES:
            archive.write(ROOT / name, name)
        archive.writestr(
            "plugin-import-name-yes24_library_status.txt",
            b"",
        )

    print(f"Built: {OUTPUT}")


if __name__ == "__main__":
    main()
