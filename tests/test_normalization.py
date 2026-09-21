from app.filtration.normalization import (
    is_syntactically_valid,
    normalize_email,
    split_local_and_domain,
)


def test_valid_emails_pass_syntax_check():
    assert is_syntactically_valid("john@abc.com")
    assert is_syntactically_valid(" JOHN@ABC.COM ")


def test_invalid_emails_fail_syntax_check():
    assert not is_syntactically_valid("johnexample.com")   # no '@'
    assert not is_syntactically_valid("john@example")      # no '.'
    assert not is_syntactically_valid("johnexample")       # neither
    assert not is_syntactically_valid("")
    assert not is_syntactically_valid(None)


def test_normalize_trims_and_lowercases():
    assert normalize_email("  JOHN@ABC.COM  ") == "john@abc.com"


def test_normalize_removes_embedded_whitespace():
    assert normalize_email("john . smith @ company.com") == "john.smith@company.com"


def test_duplicate_detection_case_insensitive():
    a = normalize_email("John@ABC.com")
    b = normalize_email("john@abc.com")
    assert a == b


def test_split_local_and_domain():
    local, domain = split_local_and_domain("john.smith@company.com")
    assert local == "john.smith"
    assert domain == "company.com"
