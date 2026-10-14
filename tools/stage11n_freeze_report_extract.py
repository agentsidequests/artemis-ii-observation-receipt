#!/usr/bin/env python3
"""Freeze the exact Artemis II report pages used by Stage 11N."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


PAGES = (33, 34, 35, 112, 114, 115, 116)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()

    source = args.source_pdf.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(source)
    if len(reader.pages) < max(PAGES):
        raise ValueError(f"Source has {len(reader.pages)} pages; expected at least {max(PAGES)}.")

    writer = PdfWriter()
    text_sections: list[str] = []
    for page_number in PAGES:
        page = reader.pages[page_number - 1]
        writer.add_page(page)
        text_sections.append(
            f"===== SOURCE PDF PAGE {page_number} =====\n\n{page.extract_text() or ''}"
        )

    pdf_output = output_dir / "artemis-ii-preliminary-report-flash-pages.pdf"
    text_output = output_dir / "artemis-ii-preliminary-report-flash-pages.txt"
    with pdf_output.open("wb") as stream:
        writer.write(stream)
    text_output.write_text("\n\n".join(text_sections) + "\n", encoding="utf-8")

    receipt = {
        "source_path": str(source),
        "source_bytes": source.stat().st_size,
        "source_sha256": sha256(source),
        "source_page_count": len(reader.pages),
        "selected_source_pdf_pages_1_indexed": list(PAGES),
        "outputs": {
            pdf_output.name: {
                "bytes": pdf_output.stat().st_size,
                "sha256": sha256(pdf_output),
            },
            text_output.name: {
                "bytes": text_output.stat().st_size,
                "sha256": sha256(text_output),
            },
        },
    }
    receipt_output = output_dir / "preliminary-report-extract-receipt.json"
    receipt_output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
