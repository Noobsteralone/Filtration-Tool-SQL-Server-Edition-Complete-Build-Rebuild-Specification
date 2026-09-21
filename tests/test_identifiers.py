import pytest

from app.utils.identifiers import (
    UnsafeIdentifierError,
    is_safe_identifier,
    quote_alias,
    quote_ident,
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


def test_quote_ident_rejects_headers_with_spaces():
    # This is exactly what report_service/master_service must NOT do with
    # an uploaded file's original header text -- quote_ident is only for
    # SQL identifiers we generated ourselves (sanitize_column_name output).
    with pytest.raises(UnsafeIdentifierError):
        quote_ident("Company ID")


def test_quote_alias_handles_real_world_headers():
    # Regression test: a real uploaded file with a "Company ID" header
    # crashed report generation because quote_ident (strict identifier
    # rules) was used instead of quote_alias (permissive display text).
    assert quote_alias("Company ID") == "[Company ID]"
    assert quote_alias("E-mail Address!") == "[E-mail Address!]"
    assert quote_alias("") == "[]"
    assert quote_alias(None) == "[]"


def test_quote_alias_escapes_closing_bracket_to_prevent_injection():
    # ']' is the one character that can break out of a bracket-quoted
    # alias in T-SQL; doubling it (mirroring QUOTENAME's own behaviour)
    # keeps the whole thing a single, inert literal string.
    result = quote_alias("Notes] FOR JSON PATH; DROP TABLE FT_Users--")
    assert result == "[Notes]] FOR JSON PATH; DROP TABLE FT_Users--]"
    # No unescaped ']' except the final closing bracket.
    assert result[1:-1].replace("]]", "").count("]") == 0


def test_quote_alias_truncates_pathologically_long_headers():
    huge = "x" * 10_000
    result = quote_alias(huge)
    assert len(result) <= 402  # 400 chars + brackets
