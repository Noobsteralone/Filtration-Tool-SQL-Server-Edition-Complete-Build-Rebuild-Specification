from app.filtration.tld import classify_tld

ALLOWED = [".com", ".org", ".edu", ".us"]


def test_allowed_tlds_are_in_scope():
    for domain in ["company.com", "school.edu", "nonprofit.org", "agency.us"]:
        result = classify_tld(domain, ALLOWED)
        assert result.is_other_tld is False


def test_other_tlds_are_flagged_but_classified_not_rejected():
    for domain in ["example.net", "example.io"]:
        result = classify_tld(domain, ALLOWED)
        assert result.is_other_tld is True


def test_multi_label_tld_example():
    result = classify_tld("example.co.uk", ALLOWED)
    assert result.is_other_tld is True
    assert result.tld == ".uk"


def test_gmail_with_com_allowed_stays_in_scope():
    result = classify_tld("gmail.com", ALLOWED)
    assert result.is_other_tld is False


def test_longest_allowed_suffix_wins():
    result = classify_tld("example.co.uk", [".uk", ".co.uk"])
    assert result.is_other_tld is False
    assert result.tld == ".co.uk"
