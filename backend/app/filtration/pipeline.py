"""
Filtration pipeline orchestrator (section 69).

Python's role here is orchestration only -- every set-based operation is
pushed down into a SQL Server stored procedure so that multi-million-row
jobs are never iterated over row-by-row in the Python process (sections 3,
34, 71). Progress is reported back to the caller via `on_step` /
`on_progress` callbacks so the job worker can persist periodic (not
per-row) updates to dbo.FT_Jobs (section 30).

Mandatory step order (do not silently reorder, section 7):
  1. RemoveInvalidEmails
  2. NormalizeEmails
  3. SeparateTLD               (Other-TLD rows exit the pipeline here)
  4. DeduplicateEmails         (Allowed-TLD branch only)
  5. CheckDuplicateVsMaster
  6. FilterPersonalEmails
  7. FilterRestrictedDomains
  8. FilterRestrictedKeywords
  9. FilterRestrictedTitles    (skipped if no title column)
 10. FilterRestrictedIndustries(skipped if no industry column)
 11. FilterNumericUsernames    (one-char + numeric-username, each toggleable)
 12. FilterUsernameEqualsDomain
 13. FilterSpamDomains
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

import pyodbc

from app.utils.identifiers import assert_safe_identifier

logger = logging.getLogger("ft.pipeline")


@dataclass
class FilterToggles:
    allowed_tld: bool = True
    invalid_email: bool = True
    duplicate_email: bool = True
    duplicate_vs_master: bool = True
    personal_email: bool = True
    restricted_domain: bool = True
    restricted_keyword: bool = True
    restricted_title: bool = True
    restricted_industry: bool = True
    one_character_username: bool = True
    numeric_username: bool = True
    username_equals_domain: bool = True
    spam_domain: bool = True

    @classmethod
    def from_dict(cls, d: dict) -> "FilterToggles":
        return cls(**{k: bool(v) for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class StepResult:
    step_name: str
    rows_affected: int


@dataclass
class PipelineResult:
    steps: list[StepResult] = field(default_factory=list)


def _call_proc_with_int_outputs(
    conn: pyodbc.Connection,
    proc_name: str,
    params: dict[str, object],
    output_names: list[str],
) -> dict[str, int]:
    """
    pyodbc cannot bind T-SQL OUTPUT parameters through plain '?'
    placeholders, so this wraps the call in a small anonymous batch that
    declares local variables, EXECs the procedure with them as OUTPUT, and
    SELECTs them back as a result set. `proc_name` and `output_names` are
    always fixed, internal, whitelisted values (never derived from user
    input), so this is safe despite being string-built.
    """
    declare_sql = "; ".join(f"DECLARE @{n} INT" for n in output_names)
    param_names = list(params.keys())
    call_args = ", ".join([f"@{k}=?" for k in param_names] + [f"@{n}=@{n} OUTPUT" for n in output_names])
    select_sql = "SELECT " + ", ".join(f"@{n} AS {n}" for n in output_names)
    batch = f"{declare_sql}; EXEC {proc_name} {call_args}; {select_sql};"

    cursor = conn.cursor()
    cursor.execute(batch, list(params.values()))
    row = cursor.fetchone()
    result = {n: (getattr(row, n) if row is not None else 0) or 0 for n in output_names}
    conn.commit()
    return result


class FiltrationPipeline:
    def __init__(
        self,
        conn: pyodbc.Connection,
        staging_table: str,
        email_column: str,
        title_column: Optional[str] = None,
        industry_column: Optional[str] = None,
        on_step: Optional[Callable[[str, int], None]] = None,
    ) -> None:
        assert_safe_identifier(staging_table)
        self.conn = conn
        self.staging_table = staging_table
        self.email_column = email_column
        self.title_column = title_column
        self.industry_column = industry_column
        self.on_step = on_step or (lambda step, rows: None)

    def _run(self, step_label: str, proc_name: str, params: dict[str, object]) -> int:
        logger.info("Job step starting: %s", step_label)
        outputs = _call_proc_with_int_outputs(self.conn, proc_name, params, ["RowsAffected"])
        rows = outputs["RowsAffected"]
        logger.info("Job step complete: %s (%s rows tagged)", step_label, rows)
        self.on_step(step_label, rows)
        return rows

    def run_full_pipeline(self, toggles: FilterToggles) -> PipelineResult:
        result = PipelineResult()

        if toggles.invalid_email:
            rows = self._run(
                "Invalid Email Filter",
                "dbo.sp_FT_RemoveInvalidEmails",
                {"StagingTable": self.staging_table, "EmailColumn": self.email_column},
            )
            result.steps.append(StepResult("INVALID_EMAIL", rows))

        rows = self._run(
            "Email Normalization",
            "dbo.sp_FT_NormalizeEmails",
            {"StagingTable": self.staging_table, "EmailColumn": self.email_column},
        )
        result.steps.append(StepResult("NORMALIZE", rows))

        cursor = self.conn.cursor()
        cursor.execute(
            "DECLARE @a INT, @o INT; "
            "EXEC dbo.sp_FT_SeparateTLD @StagingTable=?, @RowsAllowedTLD=@a OUTPUT, @RowsOtherTLD=@o OUTPUT; "
            "SELECT @a AS Allowed, @o AS Other;",
            [self.staging_table],
        )
        row = cursor.fetchone()
        self.conn.commit()
        result.steps.append(StepResult("ALLOWED_TLD", row.Allowed if row else 0))
        result.steps.append(StepResult("OTHER_TLD", row.Other if row else 0))
        self.on_step("TLD Separation", (row.Allowed if row else 0) + (row.Other if row else 0))

        if toggles.duplicate_email:
            rows = self._run(
                "Duplicate Email Filter",
                "dbo.sp_FT_DeduplicateEmails",
                {"StagingTable": self.staging_table},
            )
            result.steps.append(StepResult("DUPLICATE_EMAIL", rows))

        if toggles.duplicate_vs_master:
            rows = self._run(
                "Duplicate vs Master Check",
                "dbo.sp_FT_CheckDuplicateVsMaster",
                {"StagingTable": self.staging_table},
            )
            result.steps.append(StepResult("DUPLICATE_VS_MASTER", rows))

        if toggles.personal_email:
            rows = self._run(
                "Personal Email Filter",
                "dbo.sp_FT_FilterPersonalEmails",
                {"StagingTable": self.staging_table},
            )
            result.steps.append(StepResult("PERSONAL_EMAIL", rows))

        if toggles.restricted_domain:
            rows = self._run(
                "Restricted Domain Filter",
                "dbo.sp_FT_FilterRestrictedDomains",
                {"StagingTable": self.staging_table},
            )
            result.steps.append(StepResult("RESTRICTED_DOMAIN", rows))

        if toggles.restricted_keyword:
            rows = self._run(
                "Restricted Keyword Filter",
                "dbo.sp_FT_FilterRestrictedKeywords",
                {"StagingTable": self.staging_table},
            )
            result.steps.append(StepResult("RESTRICTED_KEYWORD", rows))

        if toggles.restricted_title and self.title_column:
            rows = self._run(
                "Restricted Title Filter",
                "dbo.sp_FT_FilterRestrictedTitles",
                {"StagingTable": self.staging_table, "TitleColumn": self.title_column},
            )
            result.steps.append(StepResult("RESTRICTED_TITLE", rows))
        elif toggles.restricted_title:
            logger.info("Skipping Restricted Title Filter: no title column on this file.")

        if toggles.restricted_industry and self.industry_column:
            rows = self._run(
                "Restricted Industry Filter",
                "dbo.sp_FT_FilterRestrictedIndustries",
                {"StagingTable": self.staging_table, "IndustryColumn": self.industry_column},
            )
            result.steps.append(StepResult("RESTRICTED_INDUSTRY", rows))
        elif toggles.restricted_industry:
            logger.info("Skipping Restricted Industry Filter: no industry column on this file.")

        if toggles.one_character_username or toggles.numeric_username:
            rows = self._run(
                "Username Rules (one-character / numeric)",
                "dbo.sp_FT_FilterNumericUsernames",
                {
                    "StagingTable": self.staging_table,
                    "EnableOneCharacterUsername": 1 if toggles.one_character_username else 0,
                    "EnableNumericUsername": 1 if toggles.numeric_username else 0,
                },
            )
            result.steps.append(StepResult("USERNAME_RULES", rows))

        if toggles.username_equals_domain:
            rows = self._run(
                "Username Equals Domain Filter",
                "dbo.sp_FT_FilterUsernameEqualsDomain",
                {"StagingTable": self.staging_table},
            )
            result.steps.append(StepResult("USERNAME_EQUALS_DOMAIN", rows))

        if toggles.spam_domain:
            rows = self._run(
                "Spam Domain Filter",
                "dbo.sp_FT_FilterSpamDomains",
                {"StagingTable": self.staging_table},
            )
            result.steps.append(StepResult("SPAM_DOMAIN", rows))

        return result

    def job_summary(self) -> dict[str, int]:
        cursor = self.conn.cursor()
        cursor.execute("EXEC dbo.sp_FT_GetJobSummary @StagingTable=?", [self.staging_table])
        return {row.ReasonCode: row.RowCount for row in cursor.fetchall()}
