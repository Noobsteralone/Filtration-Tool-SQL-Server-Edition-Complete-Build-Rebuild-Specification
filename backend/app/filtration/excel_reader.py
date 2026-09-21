"""
Streaming, multi-sheet Excel reader (section 8).

Deliberately does NOT use pandas.read_excel(), which loads the whole
workbook into memory. Uses openpyxl in read-only mode, which streams rows
from the underlying XML without materializing the full worksheet.

Every worksheet in the workbook is processed and combined -- not just the
first one (section 8: "Do not process only Sheet1").
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

import openpyxl


def _normalize_header(header: object) -> str:
    return re.sub(r"\s+", " ", str(header if header is not None else "").strip().lower())


def _cell_to_str(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return str(value)


def unified_headers(path: str | Path) -> list[str]:
    """
    First pass: scans every worksheet's header row (row 1) and builds a
    single unified, de-duplicated (case/whitespace-insensitive) column
    list in first-seen order. Only reads row 1 of each sheet -- cheap even
    for very large workbooks.
    """
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    try:
        seen: dict[str, str] = {}
        for ws in wb.worksheets:
            row_iter = ws.iter_rows(min_row=1, max_row=1, values_only=True)
            header_row = next(row_iter, None)
            if not header_row:
                continue
            for cell in header_row:
                if cell is None or str(cell).strip() == "":
                    continue
                key = _normalize_header(cell)
                if key not in seen:
                    seen[key] = str(cell).strip()
        return list(seen.values())
    finally:
        wb.close()


def iter_all_sheet_rows(path: str | Path, headers: list[str]) -> Iterator[tuple[str, int, list[str | None]]]:
    """
    Second pass: streams every data row (row 2+) of every worksheet, mapped
    positionally into the unified `headers` list (values.only, so no
    formatting/style objects are ever materialized). Yields
    (sheet_name, source_row_number, values_aligned_to_headers).
    """
    header_index_by_key = {_normalize_header(h): i for i, h in enumerate(headers)}

    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    try:
        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)
            try:
                sheet_header_row = next(rows)
            except StopIteration:
                continue
            sheet_col_to_unified: dict[int, int] = {}
            for col_idx, cell in enumerate(sheet_header_row):
                if cell is None or str(cell).strip() == "":
                    continue
                key = _normalize_header(cell)
                if key in header_index_by_key:
                    sheet_col_to_unified[col_idx] = header_index_by_key[key]

            for row_number, row in enumerate(rows, start=2):
                if row is None or all(v is None for v in row):
                    continue
                aligned: list[str | None] = [None] * len(headers)
                for col_idx, value in enumerate(row):
                    unified_idx = sheet_col_to_unified.get(col_idx)
                    if unified_idx is not None:
                        aligned[unified_idx] = _cell_to_str(value)
                yield ws.title, row_number, aligned
    finally:
        wb.close()


def sheet_names(path: str | Path) -> list[str]:
    wb = openpyxl.load_workbook(str(path), read_only=True)
    try:
        return list(wb.sheetnames)
    finally:
        wb.close()
