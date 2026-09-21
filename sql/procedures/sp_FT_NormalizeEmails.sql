/* =============================================================================
   sp_FT_NormalizeEmails   (Pipeline Step 4)
   Trims, removes embedded whitespace, and lowercases the e-mail into the
   fixed NormalizedEmail / EmailLocalPart / EmailDomain working columns.
   Only touches rows not already tagged with a reason code.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_NormalizeEmails
    @StagingTable   NVARCHAR(128),
    @EmailColumn    NVARCHAR(128),
    @RowsAffected   INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF dbo.fn_FT_IsSafeIdentifier(@EmailColumn) = 0
            THROW 51002, 'Unsafe email column name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        DECLARE @sql NVARCHAR(MAX) = N'
            UPDATE s
            SET s.NormalizedEmail = LOWER(REPLACE(LTRIM(RTRIM(s.' + QUOTENAME(@EmailColumn) + N')), '' '', '''')),
                s.EmailLocalPart  = LEFT(
                                        LOWER(REPLACE(LTRIM(RTRIM(s.' + QUOTENAME(@EmailColumn) + N')), '' '', '''')),
                                        CHARINDEX(''@'', LOWER(REPLACE(LTRIM(RTRIM(s.' + QUOTENAME(@EmailColumn) + N')), '' '', ''''))) - 1
                                    ),
                s.EmailDomain     = SUBSTRING(
                                        LOWER(REPLACE(LTRIM(RTRIM(s.' + QUOTENAME(@EmailColumn) + N')), '' '', '''')),
                                        CHARINDEX(''@'', LOWER(REPLACE(LTRIM(RTRIM(s.' + QUOTENAME(@EmailColumn) + N')), '' '', ''''))) + 1,
                                        4000
                                    )
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL;';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;

        -- Defensive re-check: if whitespace-stripping collapsed a value so it
        -- no longer contains '@'/'.', tag it invalid rather than leaving it
        -- to crash downstream string functions.
        DECLARE @sql2 NVARCHAR(MAX) = N'
            UPDATE s
            SET s.ReasonCode = ''INVALID_EMAIL''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND (s.NormalizedEmail IS NULL
                   OR CHARINDEX(''@'', s.NormalizedEmail) <= 1
                   OR CHARINDEX(''.'', s.EmailDomain) = 0
                   OR s.EmailDomain IS NULL
                   OR s.EmailDomain = '''');';
        EXEC sp_executesql @sql2;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
