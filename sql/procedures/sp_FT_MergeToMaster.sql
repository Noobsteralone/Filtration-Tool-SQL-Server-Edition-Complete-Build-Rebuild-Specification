/* =============================================================================
   sp_FT_MergeToMaster   (section 26)
   Final step: inserts the surviving "Kept" rows (ReasonCode IS NULL AND
   IsOtherTLD = 0) into dbo.FT_MasterEmails. Re-checks Email uniqueness at
   insert time (NOT EXISTS) as a safety net even though
   sp_FT_CheckDuplicateVsMaster already ran earlier in the pipeline --
   protects against another job concurrently merging the same address.
   Standard columns are supplied by sanitized staging column names (NULL if
   the source file did not have that field); any other uploaded columns are
   preserved as a JSON blob in AdditionalData via an optional pre-built,
   already-identifier-validated SQL fragment supplied by the Python
   orchestrator (see backend/app/services/master_service.py).
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_MergeToMaster
    @StagingTable     NVARCHAR(128),
    @JobID            INT,
    @FileName         NVARCHAR(500)  = NULL,
    @NameColumn       NVARCHAR(128)  = NULL,
    @TitleColumn      NVARCHAR(128)  = NULL,
    @CompanyColumn    NVARCHAR(128)  = NULL,
    @IndustryColumn   NVARCHAR(128)  = NULL,
    @CountryColumn    NVARCHAR(128)  = NULL,
    @LinkedInColumn   NVARCHAR(128)  = NULL,
    @AdditionalDataSql NVARCHAR(MAX) = NULL,  -- e.g. N's.[col1] AS [Original Header 1], s.[col2] AS [Original Header 2]'
    @RowsInserted     INT OUTPUT,
    @RowsDuplicate    INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        DECLARE @cols TABLE (Role NVARCHAR(20), ColName NVARCHAR(128));
        INSERT INTO @cols VALUES ('Name', @NameColumn), ('Title', @TitleColumn),
            ('Company', @CompanyColumn), ('Industry', @IndustryColumn),
            ('Country', @CountryColumn), ('LinkedIn', @LinkedInColumn);
        IF EXISTS (SELECT 1 FROM @cols WHERE ColName IS NOT NULL AND dbo.fn_FT_IsSafeIdentifier(ColName) = 0)
            THROW 51005, 'Unsafe optional column name supplied to sp_FT_MergeToMaster.', 1;

        DECLARE @nameExpr     NVARCHAR(200) = CASE WHEN @NameColumn     IS NULL THEN 'NULL' ELSE 's.' + QUOTENAME(@NameColumn) END;
        DECLARE @titleExpr    NVARCHAR(200) = CASE WHEN @TitleColumn    IS NULL THEN 'NULL' ELSE 's.' + QUOTENAME(@TitleColumn) END;
        DECLARE @companyExpr  NVARCHAR(200) = CASE WHEN @CompanyColumn  IS NULL THEN 'NULL' ELSE 's.' + QUOTENAME(@CompanyColumn) END;
        DECLARE @industryExpr NVARCHAR(200) = CASE WHEN @IndustryColumn IS NULL THEN 'NULL' ELSE 's.' + QUOTENAME(@IndustryColumn) END;
        DECLARE @countryExpr  NVARCHAR(200) = CASE WHEN @CountryColumn  IS NULL THEN 'NULL' ELSE 's.' + QUOTENAME(@CountryColumn) END;
        DECLARE @linkedinExpr NVARCHAR(200) = CASE WHEN @LinkedInColumn IS NULL THEN 'NULL' ELSE 's.' + QUOTENAME(@LinkedInColumn) END;

        DECLARE @additionalExpr NVARCHAR(MAX) =
            CASE WHEN @AdditionalDataSql IS NULL OR LTRIM(RTRIM(@AdditionalDataSql)) = ''
                 THEN 'NULL'
                 ELSE '(SELECT ' + @AdditionalDataSql + ' FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)'
            END;

        DECLARE @sql NVARCHAR(MAX) = N'
            INSERT INTO dbo.FT_MasterEmails
                (Email, Name, Title, Company, Industry, Country, LinkedIn, SourceFile, SourceJobID, AdditionalData)
            SELECT
                s.NormalizedEmail, ' + @nameExpr + N', ' + @titleExpr + N', ' + @companyExpr + N', ' +
                @industryExpr + N', ' + @countryExpr + N', ' + @linkedinExpr + N',
                @FileName, @JobID, ' + @additionalExpr + N'
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.IsOtherTLD = 0
              AND NOT EXISTS (SELECT 1 FROM dbo.FT_MasterEmails m WHERE m.Email = s.NormalizedEmail);';

        EXEC sp_executesql @sql, N'@FileName NVARCHAR(500), @JobID INT', @FileName, @JobID;
        SET @RowsInserted = @@ROWCOUNT;

        -- Anything that slipped through as a race-condition duplicate.
        DECLARE @sqlDup NVARCHAR(MAX) = N'
            SELECT @cnt = COUNT(*)
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.IsOtherTLD = 0
              AND EXISTS (SELECT 1 FROM dbo.FT_MasterEmails m WHERE m.Email = s.NormalizedEmail);';
        DECLARE @dupCount INT;
        EXEC sp_executesql @sqlDup, N'@cnt INT OUTPUT', @cnt = @dupCount OUTPUT;
        SET @RowsDuplicate = ISNULL(@dupCount, 0) - @RowsInserted;
        IF @RowsDuplicate < 0 SET @RowsDuplicate = 0;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
