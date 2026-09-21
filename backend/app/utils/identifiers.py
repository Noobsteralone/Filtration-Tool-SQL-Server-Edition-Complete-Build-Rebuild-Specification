"""
Safe SQL identifier handling.

This is the single reusable module responsible for turning arbitrary,
untrusted input (an uploaded file's column headers, a job id) into
identifiers that are safe to interpolate into dynamic SQL. Every stored
procedure re-validates identifiers on the SQL side too (see
sql/procedures/000_helper_functions.sql, fn_FT_IsSafeIdentifier) as
defense in depth, but no raw header text is ever sent to SQL Server as an
identifier -- only the sanitized name produced here.
"""
from __future__ import annotations

import re
import unicodedata

_SAFE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_MAX_IDENTIFIER_LEN = 116  # leaves room for prefixes/suffixes under SQL Server's 128 char cap


class UnsafeIdentifierError(ValueError):
    pass


def is_safe_identifier(name: str) -> bool:
    return bool(name) and len(name) <= 128 and bool(_SAFE_RE.match(name))


def assert_safe_identifier(name: str) -> str:
    if not is_safe_identifier(name):
        raise UnsafeIdentifierError(f"Unsafe SQL identifier: {name!r}")
    return name


def quote_ident(name: str) -> str:
    """Bracket-quote an already-validated identifier for use in dynamic SQL."""
    assert_safe_identifier(name)
    return f"[{name}]"


def staging_table_name(job_id: int) -> str:
    if not isinstance(job_id, int) or job_id <= 0:
        raise UnsafeIdentifierError(f"Invalid job id for staging table name: {job_id!r}")
    return f"FT_Staging_{job_id}"


def sanitize_column_name(original: str, ordinal: int) -> str:
    """
    Converts an arbitrary uploaded column header into a safe, deterministic
    SQL column name. Never trusts the header text itself: falls back to a
    positional name (`col_<n>`) whenever the header does not reduce to a
    clean identifier, guaranteeing uniqueness via the ordinal position.
    """
    normalized = unicodedata.normalize("NFKD", original or "").encode("ascii", "ignore").decode("ascii")
    candidate = re.sub(r"[^A-Za-z0-9_]", "_", normalized).strip("_")
    if not candidate or not re.match(r"^[A-Za-z_]", candidate):
        candidate = f"col_{ordinal}"
    candidate = candidate[:_MAX_IDENTIFIER_LEN]
    return f"c_{ordinal}_{candidate}"[:128]
