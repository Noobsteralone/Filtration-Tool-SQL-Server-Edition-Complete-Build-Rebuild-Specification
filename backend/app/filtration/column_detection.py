"""
Email (and other semantic role) column auto-detection (section 9).

Matching is case-insensitive and whitespace-normalized. If more than one
header looks like an e-mail column, the caller MUST surface a
column-selection screen rather than silently picking one (section 9).
"""
from __future__ import annotations

import re

EMAIL_COLUMN_NAMES = {
    "email",
    "emailaddress",
    "email address",
    "e-mail",
    "e-mail address",
    "contact email",
    "work email",
    "business email",
}

TITLE_COLUMN_NAMES = {"title", "job title", "jobtitle", "position"}
INDUSTRY_COLUMN_NAMES = {"industry", "industry name", "sector"}
NAME_COLUMN_NAMES = {"name", "full name", "contact name", "first name", "fullname"}
COMPANY_COLUMN_NAMES = {"company", "company name", "organization", "organisation"}
COUNTRY_COLUMN_NAMES = {"country", "country name"}
LINKEDIN_COLUMN_NAMES = {"linkedin", "linkedin url", "linkedin profile"}


def _normalize_header(header: str) -> str:
    return re.sub(r"\s+", " ", header.strip().lower())


def find_matching_headers(headers: list[str], candidate_names: set[str]) -> list[str]:
    return [h for h in headers if _normalize_header(h) in candidate_names]


def detect_email_columns(headers: list[str]) -> list[str]:
    """Returns every header that looks like an e-mail column. Zero results
    means the user must map it manually; more than one means the user must
    be shown a selection screen (never silently guess, section 9)."""
    return find_matching_headers(headers, EMAIL_COLUMN_NAMES)


def detect_role_columns(headers: list[str]) -> dict[str, list[str]]:
    return {
        "EMAIL": find_matching_headers(headers, EMAIL_COLUMN_NAMES),
        "TITLE": find_matching_headers(headers, TITLE_COLUMN_NAMES),
        "INDUSTRY": find_matching_headers(headers, INDUSTRY_COLUMN_NAMES),
        "NAME": find_matching_headers(headers, NAME_COLUMN_NAMES),
        "COMPANY": find_matching_headers(headers, COMPANY_COLUMN_NAMES),
        "COUNTRY": find_matching_headers(headers, COUNTRY_COLUMN_NAMES),
        "LINKEDIN": find_matching_headers(headers, LINKEDIN_COLUMN_NAMES),
    }
