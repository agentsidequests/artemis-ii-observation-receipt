#!/usr/bin/env python3
"""Extract page-delimited UTF-8 text from a PDF evidence file."""

from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("output_text", type=Path)
    args = parser.parse_args()

    reader = PdfReader(args.source_pdf)
    sections = [
        f"===== PDF PAGE {index} =====\n\n{page.extract_text() or ''}"
        for index, page in enumerate(reader.pages, start=1)
    ]
    args.output_text.parent.mkdir(parents=True, exist_ok=True)
    args.output_text.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"extracted_pages={len(reader.pages)} output={args.output_text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
