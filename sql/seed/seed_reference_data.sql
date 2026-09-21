/* =============================================================================
   FT - Filtration Tool
   seed_reference_data.sql

   Seeds SAFE, minimal starter values into the reference tables and default
   application settings/roles. Every value here remains fully editable from
   the Reference Lists screens afterwards -- nothing is hard-coded into the
   application logic (section 51).

   Idempotent: uses MERGE / NOT EXISTS guards so re-running never creates
   duplicates and never overwrites values an administrator has since edited
   (the WHEN NOT MATCHED branch only inserts, it never updates on rerun).
   ============================================================================= */

USE [FT_Filtration];
GO

/* ---- Roles -------------------------------------------------------------- */
MERGE dbo.FT_Roles AS tgt
USING (VALUES ('USER', 'Upload, run filtration, view/download own jobs'),
              ('ADMIN', 'Also manage reference lists, master data, settings, view all jobs'),
              ('SUPER_ADMIN', 'Also manage users and application settings')) AS src(RoleName, Description)
ON tgt.RoleName = src.RoleName
WHEN NOT MATCHED THEN
    INSERT (RoleName, Description) VALUES (src.RoleName, src.Description);
GO

/* ---- Allowed TLDs (default, per spec section 13) ------------------------ */
MERGE dbo.FT_AllowedTLDs AS tgt
USING (VALUES ('.com'), ('.org'), ('.edu'), ('.us')) AS src(Value)
ON tgt.Value = src.Value
WHEN NOT MATCHED THEN INSERT (Value) VALUES (src.Value);
GO

/* ---- Personal email domains (default starter list, section 15) --------- */
MERGE dbo.FT_PersonalEmailDomains AS tgt
USING (VALUES ('gmail.com'), ('yahoo.com'), ('outlook.com'), ('hotmail.com'),
              ('rediffmail.com'), ('aol.com'), ('msn.com'), ('icloud.com'),
              ('live.com'), ('ymail.com'), ('protonmail.com')) AS src(Value)
ON tgt.Value = src.Value
WHEN NOT MATCHED THEN INSERT (Value) VALUES (src.Value);
GO

/* ---- Restricted / spam / keyword / title / industry lists are left EMPTY
   by default -- the specification explicitly says not to invent a large
   blacklist (section 16). Administrators populate these from the
   Reference Lists screen (bulk paste/upload supported). */

/* ---- Default application settings --------------------------------------- */
MERGE dbo.FT_Settings AS tgt
USING (VALUES
    ('default_filter_toggles', N'{"allowed_tld":true,"invalid_email":true,"duplicate_email":true,"duplicate_vs_master":true,"personal_email":true,"restricted_domain":true,"restricted_keyword":true,"restricted_title":true,"restricted_industry":true,"one_character_username":true,"numeric_username":true,"username_equals_domain":true,"spam_domain":true}'),
    ('upload_retention_days', N'1'),
    ('report_retention_days', N'30'),
    ('temp_retention_hours', N'24'),
    ('backup_retention_days', N'7'),
    ('max_concurrent_jobs', N'1')
) AS src(SettingKey, SettingValue)
ON tgt.SettingKey = src.SettingKey
WHEN NOT MATCHED THEN INSERT (SettingKey, SettingValue) VALUES (src.SettingKey, src.SettingValue);
GO
