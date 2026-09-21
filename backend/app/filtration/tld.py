"""
Domain / TLD extraction and Allowed-TLD vs Other-TLD classification
(sections 13-14). Mirrors sql/procedures/sp_FT_SeparateTLD.sql.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TldClassification:
    is_other_tld: bool
    tld: str


def extract_tld_suffix(domain: str) -> str:
    """Naive last-label TLD, e.g. 'mail.example.co.uk' -> '.uk'. Only used
    to LABEL Other-TLD rows for reporting; classification itself is a suffix
    match against the configured allowed list, not this naive extraction."""
    last_label = domain.rsplit(".", 1)[-1]
    return f".{last_label}"


def classify_tld(domain: str, allowed_tlds: list[str]) -> TldClassification:
    """
    Returns whether `domain` falls under one of the active `allowed_tlds`
    (suffix match, longest match wins so e.g. '.co.uk' beats '.uk' if both
    are configured). If nothing matches, the row is Other-TLD and its TLD
    is derived from the domain's last label for display purposes only.
    """
    domain_lower = domain.lower()
    matches = [t for t in allowed_tlds if domain_lower.endswith(t.lower())]
    if matches:
        best = max(matches, key=len)
        return TldClassification(is_other_tld=False, tld=best)
    return TldClassification(is_other_tld=True, tld=extract_tld_suffix(domain_lower))
