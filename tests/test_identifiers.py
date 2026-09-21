import pytest

from app.utils.identifiers import (
    UnsafeIdentifierError,
    is_safe_identifier,
    sanitize_column_name,
    staging_table_name,
)


def test_safe_identifiers():
    assert is_safe_identifier("Email")
    assert is_safe_identifier("col_1")
    assert not is_safe_identifier("Email; DROP TABLE Users--")
    assert not is_safe_identifier("1col")
    assert not is_safe_identifier("")


def test_staging_table_name():
    assert staging_table_name(42) == "FT_Staging_42"
    with pytest.raises(UnsafeIdentifierError):
        staging_table_name(-1)


def test_sanitize_column_name_handles_arbitrary_headers():
    assert sanitize_column_name("Email Address", 0).startswith("c_0_")
    assert sanitize_column_name("1st Name", 1).startswith("c_1_")
    # A header that is entirely unsafe still yields a deterministic, safe name.
    dangerous = sanitize_column_name("]; DROP TABLE X--", 2)
    assert is_safe_identifier(dangerous)


def test_sanitize_column_name_is_deterministic():
    a = sanitize_column_name("Company Name", 3)
    b = sanitize_column_name("Company Name", 3)
    assert a == b
