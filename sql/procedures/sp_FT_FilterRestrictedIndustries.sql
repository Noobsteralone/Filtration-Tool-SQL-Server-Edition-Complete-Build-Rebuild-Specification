/* =============================================================================
   sp_FT_FilterRestrictedIndustries   (section 19)
   Matches @IndustryColumn against dbo.FT_RestrictedIndustries. If the
   uploaded file has no industry column, the caller skips this step
   entirely (section 19: do not fail the job).
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_FilterRestrictedIndustries
    @StagingTable   NVARCHAR(128),
    @IndustryColumn NVARCHAR(128),
    @RowsAffected   INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        SET @RowsAffected = 0;
        IF @IndustryColumn IS NULL OR LTRIM(RTRIM(@IndustryColumn)) = ''
            RETURN;

        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF dbo.fn_FT_IsSafeIdentifier(@IndustryColumn) = 0
            THROW 51004, 'Unsafe industry column name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        DECLARE @sql NVARCHAR(MAX) = N'
            UPDATE s
            SET s.ReasonCode = ''RESTRICTED_INDUSTRY''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.IsOtherTLD = 0
              AND s.' + QUOTENAME(@IndustryColumn) + N' IS NOT NULL
              AND EXISTS (
                    SELECT 1 FROM dbo.FT_RestrictedIndustries i
                    WHERE i.IsActive = 1
                      AND s.' + QUOTENAME(@IndustryColumn) + N' LIKE dbo.fn_FT_WildcardToLike(i.Value)
              );';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
