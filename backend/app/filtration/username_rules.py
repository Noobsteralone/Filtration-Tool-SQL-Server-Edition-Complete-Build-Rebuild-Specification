"""
Username-based rules (sections 20-22). Mirrors
sql/procedures/sp_FT_FilterNumericUsernames.sql and
sql/procedures/sp_FT_FilterUsernameEqualsDomain.sql.

CONSOLIDATION NOTE (section 21): the source specification states the
digit-only / invalid-numeric-username rule twice. It is implemented exactly
once here (`is_invalid_numeric_username`) and is independently toggleable
from the one-character-username rule, per the SQL procedure's two BIT
parameters.
"""
from __future__ import annotations

_DIGITS = str.maketrans("", "", "0123456789")


def strip_digits(value: str) -> str:
    return value.translate(_DIGITS)


def is_one_character_username(local_part: str) -> bool:
    return len(local_part) == 1


def is_invalid_numeric_username(local_part: str) -> bool:
    """True when the local part is non-empty and made up entirely of
    digits (stripping all digits leaves nothing) -- covers every example
    given in the spec: '0', '1', '000', '111'."""
    return len(local_part) > 0 and strip_digits(local_part) == ""


def domain_name_before_tld(domain: str, tld: str) -> str:
    if tld and domain.endswith(tld) and len(domain) > len(tld):
        return domain[: -len(tld)]
    return domain


def is_username_equals_domain(local_part: str, domain: str, tld: str) -> bool:
    if not tld:
        return False
    return domain_name_before_tld(domain, tld) == local_part
