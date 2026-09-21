from app.filtration.keywords import keyword_matches, matches_any


def test_exact_match_no_wildcard():
    assert keyword_matches("admin", "admin")
    assert not keyword_matches("administrator", "admin")


def test_prefix_wildcard():
    assert keyword_matches("admin_team", "admin*")
    assert not keyword_matches("team_admin", "admin*")


def test_suffix_wildcard():
    assert keyword_matches("team_admin", "*admin")
    assert not keyword_matches("admin_team", "*admin")


def test_contains_wildcard():
    assert keyword_matches("super_admin_team", "*admin*")
    assert keyword_matches("admin", "*admin*")


def test_case_insensitive():
    assert keyword_matches("ADMIN", "admin")
    assert keyword_matches("Admin_Team", "admin*")


def test_matches_any():
    patterns = ["intern*", "*recruiter*", "student"]
    assert matches_any("internship_coordinator", patterns)
    assert matches_any("senior_recruiter", patterns)
    assert matches_any("student", patterns)
    assert not matches_any("engineer", patterns)


def test_none_value_never_matches():
    assert not keyword_matches(None, "admin*")
