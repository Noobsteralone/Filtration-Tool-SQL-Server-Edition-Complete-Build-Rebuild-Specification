/* =============================================================================
   FT - Filtration Tool
   010_reference_tables.sql

   Configurable business-rule reference tables. NOTHING in this file hard-codes
   business rules -- it only creates the empty structures. Default values are
   inserted separately (idempotently) by sql/seed/seed_reference_data.sql so
   that administrators can freely edit/remove them afterwards.

   Idempotent: every object is created only if missing.
   ============================================================================= */

USE [FT_Filtration];
GO

/* ---------------------------------------------------------------------------
   Generic pattern: every reference table shares the same shape so that a
   single reusable admin UI / service layer (ReferenceService) can manage all
   of them identically.
   --------------------------------------------------------------------------- */

IF OBJECT_ID(N'dbo.FT_AllowedTLDs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_AllowedTLDs
    (
        ID          INT IDENTITY(1,1) PRIMARY KEY,
        Value       NVARCHAR(50)  NOT NULL,   -- e.g. '.com'
        IsActive    BIT           NOT NULL CONSTRAINT DF_FT_AllowedTLDs_IsActive DEFAULT (1),
        CreatedAt   DATETIME2     NOT NULL CONSTRAINT DF_FT_AllowedTLDs_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt   DATETIME2     NULL,
        CreatedBy   NVARCHAR(100) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_AllowedTLDs_Value ON dbo.FT_AllowedTLDs(Value);
END
GO

IF OBJECT_ID(N'dbo.FT_PersonalEmailDomains', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_PersonalEmailDomains
    (
        ID          INT IDENTITY(1,1) PRIMARY KEY,
        Value       NVARCHAR(255) NOT NULL,   -- e.g. 'gmail.com'
        IsActive    BIT           NOT NULL CONSTRAINT DF_FT_PersonalEmailDomains_IsActive DEFAULT (1),
        CreatedAt   DATETIME2     NOT NULL CONSTRAINT DF_FT_PersonalEmailDomains_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt   DATETIME2     NULL,
        CreatedBy   NVARCHAR(100) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_PersonalEmailDomains_Value ON dbo.FT_PersonalEmailDomains(Value);
END
GO

IF OBJECT_ID(N'dbo.FT_RestrictedDomains', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_RestrictedDomains
    (
        ID          INT IDENTITY(1,1) PRIMARY KEY,
        Value       NVARCHAR(255) NOT NULL,   -- e.g. 'mailinator.com'
        IsActive    BIT           NOT NULL CONSTRAINT DF_FT_RestrictedDomains_IsActive DEFAULT (1),
        CreatedAt   DATETIME2     NOT NULL CONSTRAINT DF_FT_RestrictedDomains_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt   DATETIME2     NULL,
        CreatedBy   NVARCHAR(100) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_RestrictedDomains_Value ON dbo.FT_RestrictedDomains(Value);
END
GO

IF OBJECT_ID(N'dbo.FT_SpamDomains', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_SpamDomains
    (
        ID          INT IDENTITY(1,1) PRIMARY KEY,
        Value       NVARCHAR(255) NOT NULL,
        IsActive    BIT           NOT NULL CONSTRAINT DF_FT_SpamDomains_IsActive DEFAULT (1),
        CreatedAt   DATETIME2     NOT NULL CONSTRAINT DF_FT_SpamDomains_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt   DATETIME2     NULL,
        CreatedBy   NVARCHAR(100) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_SpamDomains_Value ON dbo.FT_SpamDomains(Value);
END
GO

/* Restricted keywords: matched (with wildcard support, see
   backend/app/filtration/keywords.py) against the e-mail local part
   (username). Category kept for future extension but the Email-username
   rule is the only category exercised by the pipeline today. */
IF OBJECT_ID(N'dbo.FT_RestrictedKeywords', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_RestrictedKeywords
    (
        ID          INT IDENTITY(1,1) PRIMARY KEY,
        Value       NVARCHAR(255) NOT NULL,   -- supports * wildcards, e.g. 'admin*'
        Category    NVARCHAR(50)  NOT NULL CONSTRAINT DF_FT_RestrictedKeywords_Category DEFAULT ('EMAIL_USERNAME'),
        IsActive    BIT           NOT NULL CONSTRAINT DF_FT_RestrictedKeywords_IsActive DEFAULT (1),
        CreatedAt   DATETIME2     NOT NULL CONSTRAINT DF_FT_RestrictedKeywords_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt   DATETIME2     NULL,
        CreatedBy   NVARCHAR(100) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_RestrictedKeywords_Value_Category ON dbo.FT_RestrictedKeywords(Value, Category);
END
GO

/* Restricted job titles: wildcard keyword list matched against the Title
   column when present in the uploaded file. */
IF OBJECT_ID(N'dbo.FT_RestrictedTitles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_RestrictedTitles
    (
        ID          INT IDENTITY(1,1) PRIMARY KEY,
        Value       NVARCHAR(255) NOT NULL,   -- supports * wildcards, e.g. '*intern*'
        IsActive    BIT           NOT NULL CONSTRAINT DF_FT_RestrictedTitles_IsActive DEFAULT (1),
        CreatedAt   DATETIME2     NOT NULL CONSTRAINT DF_FT_RestrictedTitles_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt   DATETIME2     NULL,
        CreatedBy   NVARCHAR(100) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_RestrictedTitles_Value ON dbo.FT_RestrictedTitles(Value);
END
GO

/* Restricted industries: wildcard keyword list matched against the Industry
   column when present in the uploaded file. */
IF OBJECT_ID(N'dbo.FT_RestrictedIndustries', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.FT_RestrictedIndustries
    (
        ID          INT IDENTITY(1,1) PRIMARY KEY,
        Value       NVARCHAR(255) NOT NULL,
        IsActive    BIT           NOT NULL CONSTRAINT DF_FT_RestrictedIndustries_IsActive DEFAULT (1),
        CreatedAt   DATETIME2     NOT NULL CONSTRAINT DF_FT_RestrictedIndustries_CreatedAt DEFAULT (SYSUTCDATETIME()),
        UpdatedAt   DATETIME2     NULL,
        CreatedBy   NVARCHAR(100) NULL
    );
    CREATE UNIQUE INDEX UQ_FT_RestrictedIndustries_Value ON dbo.FT_RestrictedIndustries(Value);
END
GO
