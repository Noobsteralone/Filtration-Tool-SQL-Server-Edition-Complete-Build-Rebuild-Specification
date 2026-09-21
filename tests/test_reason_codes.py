from app.filtration.reason_codes import NON_REJECTION_CODES, REASON_CODES, display_name, output_filename


def test_all_reason_codes_have_display_names():
    for code in REASON_CODES:
        assert display_name(code)


def test_other_tld_is_not_a_rejection():
    assert "OTHER_TLD" in NON_REJECTION_CODES


def test_output_filenames_match_spec_section_31():
    assert output_filename("KEPT") == "Kept.csv"
    assert output_filename("OTHER_TLD") == "Other_TLD.csv"
    assert output_filename("DUPLICATE_VS_MASTER") == "Duplicate_vs_Master.csv"
    assert output_filename("SPAM_DOMAIN") == "Spam_Domain.csv"
