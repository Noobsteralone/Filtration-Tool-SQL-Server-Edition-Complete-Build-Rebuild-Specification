/* =============================================================================
   sp_FT_FilterRestrictedKeywords   (section 17)
   Matches the e-mail username (local part) against dbo.FT_RestrictedKeywords
   (Category = 'EMAIL_USERNAME'), using wildcard '*' patterns translated to
   LIKE via dbo.fn_FT_WildcardToLike.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_FilterRestrictedKeywords
    @StagingTable   NVARCHAR(128),
    @RowsAffected   INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        DECLARE @sql NVARCHAR(MAX) = N'
            UPDATE s
            SET s.ReasonCode = ''RESTRICTED_KEYWORD''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.IsOtherTLD = 0
              AND EXISTS (
                    SELECT 1 FROM dbo.FT_RestrictedKeywords k
                    WHERE k.IsActive = 1
                      AND k.Category = ''EMAIL_USERNAME''
                      AND s.EmailLocalPart LIKE dbo.fn_FT_WildcardToLike(k.Value)
              );';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
