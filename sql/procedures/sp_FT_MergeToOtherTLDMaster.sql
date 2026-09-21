/* =============================================================================
   sp_FT_MergeToOtherTLDMaster   (section 27)
   Copies every Other-TLD row (IsOtherTLD = 1) from the staging table into
   the permanent dbo.FT_OtherTLDMaster dataset. These rows bypass the main
   filtration pipeline entirely and are never deleted (section 14).
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_MergeToOtherTLDMaster
    @StagingTable      NVARCHAR(128),
    @JobID             INT,
    @FileName          NVARCHAR(500)  = NULL,
    @NameColumn        NVARCHAR(128)  = NULL,
    @TitleColumn       NVARCHAR(128)  = NULL,
    @CompanyColumn     NVARCHAR(128)  = NULL,
    @IndustryColumn    NVARCHAR(128)  = NULL,
    @CountryColumn     NVARCHAR(128)  = NULL,
    @LinkedInColumn    NVARCHAR(128)  = NULL,
    @AdditionalDataSql NVARCHAR(MAX)  = NULL,
    @RowsInserted      INT OUTPUT
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
            THROW 51005, 'Unsafe optional column name supplied to sp_FT_MergeToOtherTLDMaster.', 1;

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
            INSERT INTO dbo.FT_OtherTLDMaster
                (Email, TLD, Name, Title, Company, Industry, Country, LinkedIn, SourceFile, SourceJobID, AdditionalData)
            SELECT
                s.NormalizedEmail, s.EmailTLD, ' + @nameExpr + N', ' + @titleExpr + N', ' + @companyExpr + N', ' +
                @industryExpr + N', ' + @countryExpr + N', ' + @linkedinExpr + N',
                @FileName, @JobID, ' + @additionalExpr + N'
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.IsOtherTLD = 1;';

        EXEC sp_executesql @sql, N'@FileName NVARCHAR(500), @JobID INT', @FileName, @JobID;
        SET @RowsInserted = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
