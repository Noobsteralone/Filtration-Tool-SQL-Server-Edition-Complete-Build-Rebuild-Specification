from app.filtration.csv_importer import build_column_mappings, iter_csv_rows, read_csv_header
from app.utils.identifiers import is_safe_identifier


def test_build_column_mappings_produces_safe_identifiers():
    headers = ["Email", "Full Name", "1st Company", "Title"]
    mappings = build_column_mappings(headers)
    assert len(mappings) == 4
    for m in mappings:
        assert is_safe_identifier(m.sql_column_name)
    # deterministic, unique by ordinal
    names = [m.sql_column_name for m in mappings]
    assert len(names) == len(set(names))


def test_read_csv_header_and_stream_rows(tmp_path):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "Email,Name,Title\n"
        "john@company.com,John Smith,Manager\n"
        "jane@company.com,Jane Doe,\n",
        encoding="utf-8",
    )
    header = read_csv_header(csv_path)
    assert header == ["Email", "Name", "Title"]

    rows = list(iter_csv_rows(csv_path))
    assert rows == [
        ["john@company.com", "John Smith", "Manager"],
        ["jane@company.com", "Jane Doe", None],
    ]


def test_iter_csv_rows_never_materializes_full_file_as_list_in_caller(tmp_path):
    csv_path = tmp_path / "big.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Email,Name\n")
        for i in range(1000):
            f.write(f"user{i}@company.com,User {i}\n")

    count = 0
    for row in iter_csv_rows(csv_path):
        count += 1
        assert row[0].startswith("user")
    assert count == 1000
