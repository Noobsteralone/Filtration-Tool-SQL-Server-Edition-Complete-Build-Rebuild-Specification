from app.filtration.column_detection import detect_email_columns, detect_role_columns


def test_detects_common_email_header_variants():
    for header in ["Email", "EmailAddress", "Email Address", "E-mail", "E-mail Address",
                   "Contact Email", "Work Email", "Business Email", "  email  ", "EMAIL"]:
        assert detect_email_columns([header, "Name", "Company"]) == [header]


def test_no_email_column_returns_empty():
    assert detect_email_columns(["Name", "Company", "Title"]) == []


def test_multiple_email_columns_are_all_returned_for_user_selection():
    headers = ["Work Email", "Business Email", "Name"]
    result = detect_email_columns(headers)
    assert set(result) == {"Work Email", "Business Email"}


def test_detect_role_columns():
    headers = ["Email", "Name", "Title", "Company", "Industry", "Country", "LinkedIn", "Source"]
    roles = detect_role_columns(headers)
    assert roles["EMAIL"] == ["Email"]
    assert roles["TITLE"] == ["Title"]
    assert roles["INDUSTRY"] == ["Industry"]
    assert roles["COMPANY"] == ["Company"]
    assert roles["LINKEDIN"] == ["LinkedIn"]
