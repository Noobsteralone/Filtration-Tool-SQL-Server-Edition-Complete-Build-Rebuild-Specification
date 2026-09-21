/* =============================================================================
   FT - Filtration Tool
   030_indexes.sql

   Indexes driven by actual query patterns (section 35). Idempotent: each
   index is created only if missing. Deliberately does NOT index the
   per-job staging tables here -- those are created fresh per job, indexed
   (if at all) only after the bulk load completes (see sp_FT_PrepareStaging).
   ============================================================================= */

USE [FT_Filtration];
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_MasterEmails_Email' AND object_id = OBJECT_ID('dbo.FT_MasterEmails'))
    CREATE UNIQUE INDEX IX_FT_MasterEmails_Email ON dbo.FT_MasterEmails(Email);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_OtherTLDMaster_Email' AND object_id = OBJECT_ID('dbo.FT_OtherTLDMaster'))
    CREATE INDEX IX_FT_OtherTLDMaster_Email ON dbo.FT_OtherTLDMaster(Email);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_Jobs_Status' AND object_id = OBJECT_ID('dbo.FT_Jobs'))
    CREATE INDEX IX_FT_Jobs_Status ON dbo.FT_Jobs(Status);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_Jobs_UploadedBy' AND object_id = OBJECT_ID('dbo.FT_Jobs'))
    CREATE INDEX IX_FT_Jobs_UploadedBy ON dbo.FT_Jobs(UploadedBy);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_PersonalEmailDomains_Value' AND object_id = OBJECT_ID('dbo.FT_PersonalEmailDomains'))
    CREATE INDEX IX_FT_PersonalEmailDomains_Value ON dbo.FT_PersonalEmailDomains(Value) WHERE IsActive = 1;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_RestrictedDomains_Value' AND object_id = OBJECT_ID('dbo.FT_RestrictedDomains'))
    CREATE INDEX IX_FT_RestrictedDomains_Value ON dbo.FT_RestrictedDomains(Value) WHERE IsActive = 1;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_SpamDomains_Value' AND object_id = OBJECT_ID('dbo.FT_SpamDomains'))
    CREATE INDEX IX_FT_SpamDomains_Value ON dbo.FT_SpamDomains(Value) WHERE IsActive = 1;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_AllowedTLDs_Value' AND object_id = OBJECT_ID('dbo.FT_AllowedTLDs'))
    CREATE INDEX IX_FT_AllowedTLDs_Value ON dbo.FT_AllowedTLDs(Value) WHERE IsActive = 1;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_ActivityLogs_CreatedAt' AND object_id = OBJECT_ID('dbo.FT_ActivityLogs'))
    CREATE INDEX IX_FT_ActivityLogs_CreatedAt ON dbo.FT_ActivityLogs(CreatedAt DESC);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_ActivityLogs_JobID' AND object_id = OBJECT_ID('dbo.FT_ActivityLogs'))
    CREATE INDEX IX_FT_ActivityLogs_JobID ON dbo.FT_ActivityLogs(JobID);
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_FT_JobResults_JobID' AND object_id = OBJECT_ID('dbo.FT_JobResults'))
    CREATE INDEX IX_FT_JobResults_JobID ON dbo.FT_JobResults(JobID);
GO
