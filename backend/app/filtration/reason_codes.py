"""
Single source of truth for the standardized rejection reason codes
(section 24). Stable, machine-readable codes plus human display names --
every router/service imports from here rather than hard-coding strings.
"""
from __future__ import annotations

from collections import OrderedDict

# Order matters: it documents (and, for the pipeline orchestrator, drives)
# the mandatory pipeline order from section 69.
REASON_CODES: "OrderedDict[str, str]" = OrderedDict(
    [
        ("INVALID_EMAIL", "Invalid Email"),
        ("OTHER_TLD", "Other TLD"),
        ("DUPLICATE_EMAIL", "Duplicate Email"),
        ("DUPLICATE_VS_MASTER", "Duplicate vs Master"),
        ("PERSONAL_EMAIL", "Personal Email"),
        ("RESTRICTED_DOMAIN", "Restricted Domain"),
        ("RESTRICTED_KEYWORD", "Restricted Keyword"),
        ("RESTRICTED_TITLE", "Restricted Title"),
        ("RESTRICTED_INDUSTRY", "Restricted Industry"),
        ("ONE_CHARACTER_USERNAME", "One Character Username"),
        ("INVALID_NUMERIC_USERNAME", "Invalid Numeric Username"),
        ("USERNAME_EQUALS_DOMAIN", "Username Equals Domain"),
        ("SPAM_DOMAIN", "Spam Domain"),
    ]
)

KEPT_CODE = "KEPT"
KEPT_DISPLAY_NAME = "Final Kept"

# Reason codes that are NOT counted as "rejected" (section 14: Other-TLD
# rows bypass the pipeline and are not rejections).
NON_REJECTION_CODES = {"OTHER_TLD", KEPT_CODE}


def display_name(reason_code: str) -> str:
    if reason_code == KEPT_CODE:
        return KEPT_DISPLAY_NAME
    return REASON_CODES.get(reason_code, reason_code)


def output_filename(reason_code: str) -> str:
    """Matches the exact output file names required by section 31."""
    mapping = {
        "KEPT": "Kept.csv",
        "OTHER_TLD": "Other_TLD.csv",
        "INVALID_EMAIL": "Invalid_Email.csv",
        "DUPLICATE_EMAIL": "Duplicate_Email.csv",
        "PERSONAL_EMAIL": "Personal_Email.csv",
        "RESTRICTED_DOMAIN": "Restricted_Domain.csv",
        "RESTRICTED_KEYWORD": "Restricted_Keyword.csv",
        "RESTRICTED_TITLE": "Restricted_Title.csv",
        "RESTRICTED_INDUSTRY": "Restricted_Industry.csv",
        "ONE_CHARACTER_USERNAME": "One_Character_Username.csv",
        "INVALID_NUMERIC_USERNAME": "Invalid_Numeric_Username.csv",
        "USERNAME_EQUALS_DOMAIN": "Username_Equals_Domain.csv",
        "SPAM_DOMAIN": "Spam_Domain.csv",
        "DUPLICATE_VS_MASTER": "Duplicate_vs_Master.csv",
    }
    return mapping.get(reason_code, f"{reason_code}.csv")
