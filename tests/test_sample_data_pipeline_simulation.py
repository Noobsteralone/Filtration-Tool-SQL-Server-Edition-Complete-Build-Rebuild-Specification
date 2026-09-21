"""
End-to-end simulation of the mandatory pipeline order (section 69) against
sample_data/sample_leads.csv, using the SAME pure-Python building blocks
the SQL stored procedures mirror (normalization, tld, keywords,
username_rules). This cannot exercise T-SQL directly without a live SQL
Server instance, but it does prove that the documented expected category
breakdown for the sample dataset (see sample_data/README.md) is actually
consistent with the implemented rule logic, using real sample data read
through the real CSV streaming helpers.
"""
from pathlib import Path

from app.filtration.column_detection import detect_email_columns
from app.filtration.csv_importer import iter_csv_rows, read_csv_header
from app.filtration.keywords import keyword_matches
from app.filtration.normalization import is_syntactically_valid, normalize_email, split_local_and_domain
from app.filtration.tld import classify_tld
from app.filtration.username_rules import (
    domain_name_before_tld,
    is_invalid_numeric_username,
    is_one_character_username,
)

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "sample_leads.csv"

ALLOWED_TLDS = [".com", ".org", ".edu", ".us"]
PERSONAL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "rediffmail.com",
                    "aol.com", "msn.com", "icloud.com", "live.com", "ymail.com", "protonmail.com"}
RESTRICTED_DOMAINS = {"mailinator.com"}
SPAM_DOMAINS = {"spamtrap.com"}
RESTRICTED_KEYWORDS = ["admin*"]
RESTRICTED_TITLES = ["*intern*"]
RESTRICTED_INDUSTRIES = ["staffing"]


def classify_row(raw_email: str, title: str, industry: str, seen_emails: set[str]) -> str:
    if not is_syntactically_valid(raw_email):
        return "INVALID_EMAIL"

    normalized = normalize_email(raw_email)
    local, domain = split_local_and_domain(normalized)

    tld_result = classify_tld(domain, ALLOWED_TLDS)
    if tld_result.is_other_tld:
        return "OTHER_TLD"

    if normalized in seen_emails:
        return "DUPLICATE_EMAIL"
    seen_emails.add(normalized)

    # No pre-existing Master data in this simulation -> DUPLICATE_VS_MASTER never fires.

    if domain in PERSONAL_DOMAINS:
        return "PERSONAL_EMAIL"
    if domain in RESTRICTED_DOMAINS:
        return "RESTRICTED_DOMAIN"
    if any(keyword_matches(local, p) for p in RESTRICTED_KEYWORDS):
        return "RESTRICTED_KEYWORD"
    if title and any(keyword_matches(title, p) for p in RESTRICTED_TITLES):
        return "RESTRICTED_TITLE"
    if industry and any(keyword_matches(industry, p) for p in RESTRICTED_INDUSTRIES):
        return "RESTRICTED_INDUSTRY"
    if is_one_character_username(local):
        return "ONE_CHARACTER_USERNAME"
    if is_invalid_numeric_username(local):
        return "INVALID_NUMERIC_USERNAME"
    if domain_name_before_tld(domain, tld_result.tld) == local:
        return "USERNAME_EQUALS_DOMAIN"
    if domain in SPAM_DOMAINS:
        return "SPAM_DOMAIN"
    return "KEPT"


def test_sample_dataset_produces_expected_category_breakdown():
    headers = read_csv_header(SAMPLE_CSV)
    assert detect_email_columns(headers) == ["Email"]
    email_idx = headers.index("Email")
    title_idx = headers.index("Title")
    industry_idx = headers.index("Industry")

    counts: dict[str, int] = {}
    seen_emails: set[str] = set()
    total = 0
    for row in iter_csv_rows(SAMPLE_CSV):
        total += 1
        category = classify_row(row[email_idx], row[title_idx], row[industry_idx], seen_emails)
        counts[category] = counts.get(category, 0) + 1

    assert total == 20
    assert counts == {
        "KEPT": 5,
        "INVALID_EMAIL": 2,
        "DUPLICATE_EMAIL": 1,
        "PERSONAL_EMAIL": 2,
        "OTHER_TLD": 2,
        "RESTRICTED_DOMAIN": 1,
        "SPAM_DOMAIN": 1,
        "RESTRICTED_KEYWORD": 1,
        "RESTRICTED_TITLE": 1,
        "RESTRICTED_INDUSTRY": 1,
        "ONE_CHARACTER_USERNAME": 1,
        "INVALID_NUMERIC_USERNAME": 1,
        "USERNAME_EQUALS_DOMAIN": 1,
    }
