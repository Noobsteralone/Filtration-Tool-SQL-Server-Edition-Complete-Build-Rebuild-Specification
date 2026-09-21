"""
Single reusable wildcard keyword-matching module (section 17: "Implement the
keyword matching logic in exactly ONE reusable function/module. Do not
duplicate matching logic in multiple parts of the application.").

Every place that needs to test a value against an admin-authored keyword
list -- restricted email-username keywords, restricted titles, restricted
industries, and the equivalent SQL-side dbo.fn_FT_WildcardToLike helper --
uses this same '*'-wildcard syntax:

    admin        -> exact match (case-insensitive)
    admin*       -> starts with 'admin'
    *admin       -> ends with 'admin'
    *admin*      -> contains 'admin'
"""
from __future__ import annotations

import re
from functools import lru_cache


@lru_cache(maxsize=4096)
def _compile_pattern(pattern: str) -> re.Pattern[str]:
    parts = pattern.split("*")
    regex = ".*".join(re.escape(part) for part in parts)
    return re.compile(f"^{regex}$", re.IGNORECASE)


def keyword_matches(value: str | None, pattern: str) -> bool:
    """True if `value` matches the wildcard `pattern`."""
    if value is None:
        return False
    return _compile_pattern(pattern).match(value) is not None


def matches_any(value: str | None, patterns: list[str]) -> bool:
    if value is None:
        return False
    return any(keyword_matches(value, p) for p in patterns)
