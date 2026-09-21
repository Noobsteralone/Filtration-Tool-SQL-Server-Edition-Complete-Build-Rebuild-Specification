from app.filtration.username_rules import (
    domain_name_before_tld,
    is_invalid_numeric_username,
    is_one_character_username,
    is_username_equals_domain,
)


def test_one_character_username():
    assert is_one_character_username("a")
    assert is_one_character_username("x")
    assert not is_one_character_username("ab")


def test_invalid_numeric_username_examples_from_spec():
    for local in ["0", "1", "000", "111"]:
        assert is_invalid_numeric_username(local), f"{local} should be flagged"


def test_valid_alpha_username_not_flagged():
    assert not is_invalid_numeric_username("john")
    assert not is_invalid_numeric_username("a")  # one-char rule handles this separately


def test_mixed_alphanumeric_username_not_flagged():
    # contains letters, so stripping digits leaves something -> not purely numeric
    assert not is_invalid_numeric_username("john123")


def test_domain_name_before_tld():
    assert domain_name_before_tld("sales.com", ".com") == "sales"
    assert domain_name_before_tld("info.org", ".org") == "info"


def test_username_equals_domain_examples():
    assert is_username_equals_domain("sales", "sales.com", ".com")
    assert is_username_equals_domain("info", "info.com", ".com")
    assert is_username_equals_domain("admin", "admin.org", ".org")


def test_username_not_equal_domain():
    assert not is_username_equals_domain("john", "company.com", ".com")
