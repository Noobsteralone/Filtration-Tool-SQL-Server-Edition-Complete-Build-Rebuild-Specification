#!/usr/bin/env python3
"""
Generates sample_data/sample_leads_multi_sheet.xlsx: a small 3-sheet
workbook used to verify multi-sheet Excel ingestion (section 62). Re-run
any time to regenerate the file deterministically.
"""
import sys
from pathlib import Path

import openpyxl

OUT_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "sample_leads_multi_sheet.xlsx"

SHEETS = {
    "Sheet1": [
        ("Email", "Name", "Title"),
        ("kim.lee@northwind.com", "Kim Lee", "Manager"),
        ("pat.morgan@northwind.com", "Pat Morgan", "Director"),
    ],
    "Sheet2": [
        ("Email", "Name", "Title"),
        ("sam.reid@northwind.com", "Sam Reid", "Analyst"),
        ("kim.lee@northwind.com", "Kim Lee", "Manager"),  # cross-sheet duplicate
    ],
    "Sheet3": [
        ("Email", "Name", "Title"),
        ("taylor.fox@northwind.io", "Taylor Fox", "Founder"),  # Other-TLD example
        ("robin@gmail.com", "Robin Park", "Consultant"),  # personal-domain example
    ],
}


def main() -> int:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for sheet_name, rows in SHEETS.items():
        ws = wb.create_sheet(sheet_name)
        for row in rows:
            ws.append(row)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
