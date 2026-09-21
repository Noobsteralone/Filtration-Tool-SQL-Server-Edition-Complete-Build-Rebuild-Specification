# Sample Test Data

Use these files for a first end-to-end run of the Filtration Tool once
SQL Server is initialized (`python scripts/init_db.py`) and the backend is
running.

## Files

- **`sample_leads.csv`** -- 20 rows in the same shape as the reference
  Lead411 exports this tool replaces (`Email, Name, Source, Title, Company,
  Industry, Country, LinkedIn`). Deliberately engineered to hit every
  filtration category exactly once or twice, so a single run's Report
  Summary can be checked against known-good numbers.
- **`sample_leads_multi_sheet.xlsx`** -- a 3-sheet workbook (Sheet1/Sheet2/
  Sheet3) used to verify multi-sheet Excel ingestion combines every sheet
  rather than only reading the first one.
- **`sample_reference_lists.sql`** -- OPTIONAL demo reference-list entries.
  The application ships with empty Restricted Domain/Spam Domain/Keyword/
  Title/Industry lists by default (section 16 of the spec: never invent a
  blacklist). Run this script once against `FT_Filtration` if you want
  `sample_leads.csv` to reproduce the exact category breakdown below;
  otherwise those five categories will simply show 0 rows.

## Expected category breakdown for `sample_leads.csv`

(after running `sample_reference_lists.sql`, with default Allowed TLDs
`.com,.org,.edu,.us` and the default Personal Domains list)

| Category                 | Count |
|---------------------------|------:|
| INPUT                     |    20 |
| INVALID_EMAIL             |     2 |
| DUPLICATE_EMAIL           |     1 |
| PERSONAL_EMAIL            |     2 |
| OTHER_TLD                 |     2 |
| RESTRICTED_DOMAIN         |     1 |
| RESTRICTED_KEYWORD        |     1 |
| RESTRICTED_TITLE          |     1 |
| RESTRICTED_INDUSTRY       |     1 |
| ONE_CHARACTER_USERNAME    |     1 |
| INVALID_NUMERIC_USERNAME  |     1 |
| USERNAME_EQUALS_DOMAIN    |     1 |
| SPAM_DOMAIN               |     1 |
| **FINAL KEPT**            | **5** |

This exact breakdown is asserted by
`tests/test_sample_data_pipeline_simulation.py`, which runs the same
rule logic in pure Python against this file (useful for regression-testing
the rules themselves without a live SQL Server instance).

## Testing "Duplicate vs Master"

`DUPLICATE_VS_MASTER` cannot be demonstrated from a single file. To see it:

1. Run a filtration job on `sample_leads.csv` with **Merge to Master**
   enabled.
2. Upload any small file containing one of the emails that was Kept in
   step 1 (e.g. `john.smith@acme.com`) and run it again.
3. That row will now be classified `DUPLICATE_VS_MASTER` instead of `KEPT`.

## Testing multi-sheet Excel

Upload `sample_leads_multi_sheet.xlsx` on the Filtration page. The column
selection screen should list `Email`, `Name`, `Title` (combined across all
three sheets), and the resulting job's `TotalRows` should be 6 -- proving
every sheet was read, not just `Sheet1`.
