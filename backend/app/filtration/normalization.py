"""
Email normalization and syntactic-validity helpers (sections 10-11).

These pure functions mirror, exactly, the T-SQL logic in
sql/procedures/sp_FT_RemoveInvalidEmails.sql and
sql/procedures/sp_FT_NormalizeEmails.sql, so behaviour is identical whether
a given row is evaluated on the SQL Server side (the normal, large-scale
path) or here in Python (used by the column-detection preview and by unit
tests that must run without a live SQL Server instance).
"""
from __future__ import annotations


def is_syntactically_valid(raw_email: str | None) -> bool:
    """Mirrors: CHARINDEX('@', Email) = 0 OR CHARINDEX('.', Email) = 0"""
    if raw_email is None:
        return False
    value = raw_email
    return "@" in value and "." in value and value.strip() != ""


def normalize_email(raw_email: str) -> str:
    """LTRIM/RTRIM, remove all embedded whitespace, lowercase."""
    trimmed = raw_email.strip()
    no_spaces = "".join(trimmed.split())
    return no_spaces.lower()


def split_local_and_domain(normalized_email: str) -> tuple[str, str]:
    """Splits on the FIRST '@' (mirrors CHARINDEX behaviour in SQL)."""
    idx = normalized_email.find("@")
    if idx == -1:
        raise ValueError(f"Not a valid normalized email (no '@'): {normalized_email!r}")
    return normalized_email[:idx], normalized_email[idx + 1 :]


def is_valid_after_normalization(normalized_email: str) -> bool:
    if "@" not in normalized_email:
        return False
    local, domain = split_local_and_domain(normalized_email)
    return bool(local) and bool(domain) and "." in domain
