#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Build an installable Calibre plugin ZIP."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "yes24.py"
PATCHES = (ROOT / "yes24_054_patch.py", ROOT / "yes24_055_patch.py")
OUTPUT = ROOT / "Yes24.zip"


def main():
    missing = [path for path in (SOURCE,) + PATCHES if not path.is_file()]
    if missing:
        raise SystemExit("Source file not found: " + ", ".join(str(path) for path in missing))

    parts = [SOURCE.read_text(encoding="utf-8").rstrip()]
    parts.extend(path.read_text(encoding="utf-8").strip() for path in PATCHES)
    combined = "\n\n".join(parts) + "\n"
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("__init__.py", combined)

    print(f"Built: {OUTPUT}")
    print("Runtime version: Yes24 (0, 5, 5)")


if __name__ == "__main__":
    main()
