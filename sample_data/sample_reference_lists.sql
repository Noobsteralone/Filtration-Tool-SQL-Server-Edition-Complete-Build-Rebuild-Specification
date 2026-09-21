/* =============================================================================
   OPTIONAL demo data for exercising every filtration category against
   sample_data/sample_leads.csv. This is NOT part of application startup
   seeding (sql/seed/seed_reference_data.sql) -- run it manually only if you
   want to reproduce the exact category breakdown documented in
   sample_data/README.md.
   ============================================================================= */
USE [FT_Filtration];
GO

INSERT INTO dbo.FT_RestrictedDomains (Value) VALUES ('mailinator.com');
INSERT INTO dbo.FT_SpamDomains (Value) VALUES ('spamtrap.com');
INSERT INTO dbo.FT_RestrictedKeywords (Value, Category) VALUES ('admin*', 'EMAIL_USERNAME');
INSERT INTO dbo.FT_RestrictedTitles (Value) VALUES ('*intern*');
INSERT INTO dbo.FT_RestrictedIndustries (Value) VALUES ('staffing');
GO
