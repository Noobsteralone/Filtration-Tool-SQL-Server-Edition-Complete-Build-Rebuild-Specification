/* =============================================================================
   FT - Filtration Tool
   020_core_tables.sql

   Users/Roles, Jobs, Master datasets, Settings, Activity Log.
   Idempotent: every object is created only if missing. Never drops data.
   ============================================================================= */

USE [FT_Filtration];
GO

/* ---------------------------------------------------------------------------
   Roles / Users
   --------------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.FT_Roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_Roles
    (
        RoleID      INT IDENTITY(1,1) PRIMARY KEY,
        RoleName    NVARCHAR(50)  NOT NULL,
        Description NVARCHAR(255) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_Roles_RoleName ON dbo.FT_Roles(RoleName);
END
GO

IF OBJECT_ID(N'dbo.FT_Users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_Users
    (
        UserID        INT IDENTITY(1,1) PRIMARY KEY,
        Username      NVARCHAR(100)  NOT NULL,
        Email         NVARCHAR(255)  NOT NULL,
        PasswordHash  NVARCHAR(255)  NOT NULL,
        RoleID        INT            NOT NULL,
        IsActive      BIT            NOT NULL CONSTRAINT DF_FT_Users_IsActive DEFAULT (1),
        CreatedAt     DATETIME2      NOT NULL CONSTRAINT DF_FT_Users_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt     DATETIME2      NULL,
        LastLoginAt   DATETIME2      NULL,
        CONSTRAINT FK_FT_Users_Role FOREIGN KEY (RoleID) REFERENCES dbo.FT_Roles(RoleID)
    );
    CREATE UNIQUE INDEX UQ_FT_Users_Username ON dbo.FT_Users(Username);
    CREATE UNIQUE INDEX UQ_FT_Users_Email ON dbo.FT_Users(Email);
END
GO

/* ---------------------------------------------------------------------------
   Jobs
   --------------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.FT_Jobs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_Jobs
    (
        JobID              INT IDENTITY(1,1) PRIMARY KEY,
        JobGuid            UNIQUEIDENTIFIER NOT NULL CONSTRAINT DF_FT_Jobs_JobGuid DEFAULT (NEWID()),
        JobType            NVARCHAR(50)   NOT NULL,   -- FILTRATION | DUPLICATE_CHECK | MASTER_MERGE
        FileName           NVARCHAR(500)  NULL,
        OriginalFilePath   NVARCHAR(1000) NULL,
        StagingTableName   NVARCHAR(128)  NULL,       -- FT_Staging_<JobID>, validated identifier
        EmailColumn        NVARCHAR(255)  NULL,       -- original header name selected as e-mail source
        TitleColumn        NVARCHAR(255)  NULL,
        IndustryColumn     NVARCHAR(255)  NULL,
        OptionsJson        NVARCHAR(MAX)  NULL,       -- selected filter toggles / master scope, JSON
        UploadedBy         INT            NULL,
        StartTime          DATETIME2      NULL,
        EndTime            DATETIME2      NULL,
        Status             NVARCHAR(20)   NOT NULL CONSTRAINT DF_FT_Jobs_Status DEFAULT ('QUEUED'),
        TotalRows          INT            NOT NULL CONSTRAINT DF_FT_Jobs_TotalRows DEFAULT (0),
        ProcessedRows      INT            NOT NULL CONSTRAINT DF_FT_Jobs_ProcessedRows DEFAULT (0),
        KeptRows           INT            NOT NULL CONSTRAINT DF_FT_Jobs_KeptRows DEFAULT (0),
        OtherTLDRows       INT            NOT NULL CONSTRAINT DF_FT_Jobs_OtherTLDRows DEFAULT (0),
        RejectedRows       INT            NOT NULL CONSTRAINT DF_FT_Jobs_RejectedRows DEFAULT (0),
        ProgressPercent    DECIMAL(5,2)   NOT NULL CONSTRAINT DF_FT_Jobs_ProgressPercent DEFAULT (0),
        CurrentStep        NVARCHAR(100)  NULL,
        ErrorMessage       NVARCHAR(MAX)  NULL,
        CreatedAt          DATETIME2      NOT NULL CONSTRAINT DF_FT_Jobs_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_FT_Jobs_User FOREIGN KEY (UploadedBy) REFERENCES dbo.FT_Users(UserID)
    );
    CREATE UNIQUE INDEX UQ_FT_Jobs_JobGuid ON dbo.FT_Jobs(JobGuid);
END
GO

/* Column map for a job's staging table: maps original (arbitrary, possibly
   unsafe) header names to sanitized SQL identifiers, and records the
   detected semantic role of each column. This is what lets dynamic SQL
   stay safe (section 7/46) and lets Master inserts preserve columns that
   are not part of the standard schema (section 25). */
IF OBJECT_ID(N'dbo.FT_JobColumns', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_JobColumns
    (
        JobColumnID     INT IDENTITY(1,1) PRIMARY KEY,
        JobID           INT NOT NULL,
        OriginalName    NVARCHAR(255) NOT NULL,
        SqlColumnName   NVARCHAR(128) NOT NULL,
        OrdinalPosition INT NOT NULL,
        DetectedRole    NVARCHAR(50) NULL,  -- EMAIL | NAME | TITLE | COMPANY | INDUSTRY | COUNTRY | LINKEDIN | SOURCE | OTHER
        CONSTRAINT FK_FT_JobColumns_Job FOREIGN KEY (JobID) REFERENCES dbo.FT_Jobs(JobID)
    );
    CREATE INDEX IX_FT_JobColumns_JobID ON dbo.FT_JobColumns(JobID);
END
GO

/* Per-job, per-reason-code row counts -- this is what powers the Report
   Summary screen (section 53) and the download-by-category endpoint. */
IF OBJECT_ID(N'dbo.FT_JobResults', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_JobResults
    (
        JobResultID     INT IDENTITY(1,1) PRIMARY KEY,
        JobID           INT NOT NULL,
        ReasonCode      NVARCHAR(50) NOT NULL,
        DisplayName     NVARCHAR(100) NOT NULL,
        RowCount        INT NOT NULL CONSTRAINT DF_FT_JobResults_RowCount DEFAULT (0),
        OutputFilePath  NVARCHAR(1000) NULL,
        CreatedAt       DATETIME2 NOT NULL CONSTRAINT DF_FT_JobResults_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_FT_JobResults_Job FOREIGN KEY (JobID) REFERENCES dbo.FT_Jobs(JobID)
    );
    CREATE UNIQUE INDEX UQ_FT_JobResults_Job_Reason ON dbo.FT_JobResults(JobID, ReasonCode);
END
GO

/* ---------------------------------------------------------------------------
   Master datasets
   --------------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.FT_MasterEmails', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_MasterEmails
    (
        MasterID       BIGINT IDENTITY(1,1) PRIMARY KEY,
        Email          NVARCHAR(320) NOT NULL,
        Name           NVARCHAR(255) NULL,
        Title          NVARCHAR(255) NULL,
        Company        NVARCHAR(255) NULL,
        Industry       NVARCHAR(255) NULL,
        Country        NVARCHAR(255) NULL,
        LinkedIn       NVARCHAR(500) NULL,
        SourceFile     NVARCHAR(500) NULL,
        SourceJobID    INT NULL,
        AdditionalData NVARCHAR(MAX) NULL,  -- JSON blob for any non-standard uploaded columns
        CreatedAt      DATETIME2 NOT NULL CONSTRAINT DF_FT_MasterEmails_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_FT_MasterEmails_Job FOREIGN KEY (SourceJobID) REFERENCES dbo.FT_Jobs(JobID)
    );
END
GO

IF OBJECT_ID(N'dbo.FT_OtherTLDMaster', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_OtherTLDMaster
    (
        OtherTLDID     BIGINT IDENTITY(1,1) PRIMARY KEY,
        Email          NVARCHAR(320) NOT NULL,
        TLD            NVARCHAR(50) NULL,
        Name           NVARCHAR(255) NULL,
        Title          NVARCHAR(255) NULL,
        Company        NVARCHAR(255) NULL,
        Industry       NVARCHAR(255) NULL,
        Country        NVARCHAR(255) NULL,
        LinkedIn       NVARCHAR(500) NULL,
        SourceFile     NVARCHAR(500) NULL,
        SourceJobID    INT NULL,
        AdditionalData NVARCHAR(MAX) NULL,
        CreatedAt      DATETIME2 NOT NULL CONSTRAINT DF_FT_OtherTLDMaster_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_FT_OtherTLDMaster_Job FOREIGN KEY (SourceJobID) REFERENCES dbo.FT_Jobs(JobID)
    );
END
GO

/* Tracks each contribution merged into Master / Other-TLD Master so the
   Master Files screen can list / search / delete / export by source file. */
IF OBJECT_ID(N'dbo.FT_MasterFiles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_MasterFiles
    (
        MasterFileID  INT IDENTITY(1,1) PRIMARY KEY,
        FileName      NVARCHAR(500) NOT NULL,
        SourceJobID   INT NULL,
        TargetTable   NVARCHAR(50) NOT NULL CONSTRAINT DF_FT_MasterFiles_TargetTable DEFAULT ('FT_MasterEmails'),
        RowsAdded     INT NOT NULL CONSTRAINT DF_FT_MasterFiles_RowsAdded DEFAULT (0),
        RowsDuplicate INT NOT NULL CONSTRAINT DF_FT_MasterFiles_RowsDuplicate DEFAULT (0),
        UploadedBy    INT NULL,
        CreatedAt     DATETIME2 NOT NULL CONSTRAINT DF_FT_MasterFiles_CreatedAt DEFAULT (SYSUTCDATETIME()),
        IsDeleted     BIT NOT NULL CONSTRAINT DF_FT_MasterFiles_IsDeleted DEFAULT (0),
        CONSTRAINT FK_FT_MasterFiles_Job FOREIGN KEY (SourceJobID) REFERENCES dbo.FT_Jobs(JobID),
        CONSTRAINT FK_FT_MasterFiles_User FOREIGN KEY (UploadedBy) REFERENCES dbo.FT_Users(UserID)
    );
END
GO

/* ---------------------------------------------------------------------------
   Settings / Activity Log
   --------------------------------------------------------------------------- */
IF OBJECT_ID(N'dbo.FT_Settings', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_Settings
    (
        SettingKey   NVARCHAR(100) NOT NULL PRIMARY KEY,
        SettingValue NVARCHAR(MAX) NULL,
        UpdatedAt    DATETIME2 NOT NULL CONSTRAINT DF_FT_Settings_UpdatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedBy    NVARCHAR(100) NULL
    );
END
GO

IF OBJECT_ID(N'dbo.FT_ActivityLogs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_ActivityLogs
    (
        LogID      BIGINT IDENTITY(1,1) PRIMARY KEY,
        UserID     INT NULL,
        Username   NVARCHAR(100) NULL,
        Action     NVARCHAR(100) NOT NULL,
        JobID      INT NULL,
        EntityType NVARCHAR(100) NULL,
        EntityId   NVARCHAR(100) NULL,
        Status     NVARCHAR(20) NOT NULL CONSTRAINT DF_FT_ActivityLogs_Status DEFAULT ('SUCCESS'),
        Message    NVARCHAR(MAX) NULL,
        CreatedAt  DATETIME2 NOT NULL CONSTRAINT DF_FT_ActivityLogs_CreatedAt DEFAULT (SYSUTCDATETIME()),
        CONSTRAINT FK_FT_ActivityLogs_User FOREIGN KEY (UserID) REFERENCES dbo.FT_Users(UserID)
    );
END
GO
