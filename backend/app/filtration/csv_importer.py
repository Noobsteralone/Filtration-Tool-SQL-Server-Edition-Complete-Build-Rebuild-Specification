"""
Staging table creation + streamed data import (sections 7-8, 34).

Design:
  - The staging table's column list is derived from the uploaded file's
    header row, sanitized through app.utils.identifiers.sanitize_column_name
    (never trusts raw header text in dynamic SQL).
  - Fixed pipeline working columns are appended (NormalizedEmail, ReasonCode,
    etc.) -- see docstring on `PIPELINE_COLUMNS` below. Rows are never
    deleted during processing; every rule TAGS ReasonCode instead, which is
    what lets the pipeline honour the "first applicable reason wins"
    ordering rule (section 54) with simple `WHERE ReasonCode IS NULL`
    guards in every stored procedure.
  - For CSV, native T-SQL `BULK INSERT` is attempted first (fastest path,
    matches the reference workflow this tool replaces) and falls back to
    chunked `executemany` if the SQL Server service account cannot see the
    uploaded file (e.g. app and SQL Server on different machines/accounts).
  - Never loads the whole file into memory: CSV is read with the stdlib
    `csv` module row-by-row; Excel via app.filtration.excel_reader.
"""
from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

import pyodbc

from app.utils.identifiers import assert_safe_identifier, quote_ident, sanitize_column_name

logger = logging.getLogger("ft.csv_importer")

# Appended, in this order, to every staging table. Kept lowercase/prefixed
# distinctly from `c_<n>_...` source columns so there can never be a clash.
PIPELINE_COLUMNS: list[tuple[str, str]] = [
    ("RowID", "BIGINT IDENTITY(1,1) PRIMARY KEY"),
    ("NormalizedEmail", "NVARCHAR(500) NULL"),
    ("EmailLocalPart", "NVARCHAR(500) NULL"),
    ("EmailDomain", "NVARCHAR(255) NULL"),
    ("EmailTLD", "NVARCHAR(50) NULL"),
    ("IsOtherTLD", "BIT NOT NULL DEFAULT 0"),
    ("ReasonCode", "NVARCHAR(50) NULL"),
    ("ProcessedAt", "DATETIME2 NULL"),
]


@dataclass
class ColumnMapping:
    original_name: str
    sql_column_name: str
    ordinal: int


def build_column_mappings(headers: list[str]) -> list[ColumnMapping]:
    return [
        ColumnMapping(original_name=h, sql_column_name=sanitize_column_name(h, i), ordinal=i)
        for i, h in enumerate(headers)
    ]


def create_staging_table(cursor: pyodbc.Cursor, staging_table: str, mappings: list[ColumnMapping]) -> None:
    """
    Creates the staging table with ONLY the source columns (matching the
    uploaded file's column count exactly). This is required so that native
    `BULK INSERT` (which maps the file's columns positionally to the
    target table's columns) works without a format file. The fixed
    pipeline working columns are added afterwards via
    `add_pipeline_columns`, once the raw data is already loaded -- this
    also means no indexes/extra columns exist on the table during the bulk
    load itself (section 35).
    """
    assert_safe_identifier(staging_table)
    source_cols_sql = ",\n            ".join(
        f"{quote_ident(m.sql_column_name)} NVARCHAR(4000) NULL" for m in mappings
    )
    ddl = f"CREATE TABLE {quote_ident(staging_table)} (\n            {source_cols_sql}\n        );"
    cursor.execute(ddl)
    cursor.commit()


def add_pipeline_columns(cursor: pyodbc.Cursor, staging_table: str) -> None:
    """Adds the fixed pipeline working columns (including the RowID
    identity used as a deterministic ordering key for deduplication) after
    the raw data has been loaded. SQL Server supports adding an IDENTITY
    column to an already-populated table via ALTER TABLE ADD."""
    assert_safe_identifier(staging_table)
    for name, ddl in PIPELINE_COLUMNS:
        cursor.execute(f"ALTER TABLE {quote_ident(staging_table)} ADD {quote_ident(name)} {ddl};")
    cursor.commit()


def drop_staging_table(cursor: pyodbc.Cursor, staging_table: str) -> None:
    assert_safe_identifier(staging_table)
    cursor.execute(f"IF OBJECT_ID('{staging_table}', 'U') IS NOT NULL DROP TABLE {quote_ident(staging_table)};")
    cursor.commit()


def insert_rows_chunked(
    cursor: pyodbc.Cursor,
    staging_table: str,
    mappings: list[ColumnMapping],
    rows: Iterable[list[str | None]],
    chunk_size: int,
    on_progress: Callable[[int], None] | None = None,
) -> int:
    """
    Streams `rows` (each aligned positionally to `mappings`) into the
    staging table using pyodbc `executemany` (fast_executemany is enabled
    on the engine/connection) in batches of `chunk_size`. Never builds a
    full in-memory list of the dataset.
    """
    assert_safe_identifier(staging_table)
    col_list = ", ".join(quote_ident(m.sql_column_name) for m in mappings)
    placeholders = ", ".join(["?"] * len(mappings))
    insert_sql = f"INSERT INTO {quote_ident(staging_table)} ({col_list}) VALUES ({placeholders})"

    cursor.fast_executemany = True
    batch: list[list[str | None]] = []
    total = 0
    for row in rows:
        if len(row) < len(mappings):
            row = row + [None] * (len(mappings) - len(row))
        elif len(row) > len(mappings):
            row = row[: len(mappings)]
        batch.append(row)
        if len(batch) >= chunk_size:
            cursor.executemany(insert_sql, batch)
            total += len(batch)
            if on_progress:
                on_progress(total)
            batch = []
    if batch:
        cursor.executemany(insert_sql, batch)
        total += len(batch)
        if on_progress:
            on_progress(total)
    cursor.commit()
    return total


def read_csv_header(path: str | Path, encoding: str = "utf-8-sig") -> list[str]:
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
    return [h.strip() for h in header]


def iter_csv_rows(path: str | Path, encoding: str = "utf-8-sig") -> Iterator[list[str | None]]:
    """Streams data rows (skipping the header) without ever holding the
    full file in memory."""
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # header
        for row in reader:
            yield [cell if cell != "" else None for cell in row]


def try_native_bulk_insert(
    cursor: pyodbc.Cursor,
    staging_table: str,
    csv_path: str,
    mappings: list[ColumnMapping],
) -> bool:
    """
    Attempts SQL Server-native BULK INSERT (fastest path for very large
    CSVs when the SQL Server service account can see `csv_path`, i.e. the
    app and SQL Server run on the same machine -- the default deployment
    described in this specification: LAP-S2M059 running locally).
    Returns True on success, False if it should fall back to chunked
    executemany (e.g. permission/path-visibility errors).
    """
    assert_safe_identifier(staging_table)
    escaped_path = csv_path.replace("'", "''")
    try:
        cursor.execute(
            f"""
            BULK INSERT {staging_table}
            FROM '{escaped_path}'
            WITH (
                FIRSTROW = 2,
                FIELDTERMINATOR = ',',
                ROWTERMINATOR = '\\n',
                KEEPNULLS,
                TABLOCK,
                CODEPAGE = '65001',
                FORMAT = 'CSV'
            );
            """
        )
        cursor.commit()
        return True
    except pyodbc.Error as exc:
        logger.warning("Native BULK INSERT failed (%s); falling back to chunked import.", exc)
        cursor.rollback()
        return False
