/* =============================================================================
   sp_FT_FilterRestrictedTitles   (section 18)
   Matches @TitleColumn (the sanitized staging column detected/selected as
   the job-title source) against dbo.FT_RestrictedTitles. If the uploaded
   file has no title column, the caller simply does not invoke this
   procedure (the Python orchestrator skips the step per section 18).
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_FilterRestrictedTitles
    @StagingTable   NVARCHAR(128),
    @TitleColumn    NVARCHAR(128),
    @RowsAffected   INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        SET @RowsAffected = 0;
        IF @TitleColumn IS NULL OR LTRIM(RTRIM(@TitleColumn)) = ''
            RETURN;  -- no title column on this file: skip, do not fail the job

        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF dbo.fn_FT_IsSafeIdentifier(@TitleColumn) = 0
            THROW 51003, 'Unsafe title column name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        DECLARE @sql NVARCHAR(MAX) = N'
            UPDATE s
            SET s.ReasonCode = ''RESTRICTED_TITLE''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.IsOtherTLD = 0
              AND s.' + QUOTENAME(@TitleColumn) + N' IS NOT NULL
              AND EXISTS (
                    SELECT 1 FROM dbo.FT_RestrictedTitles t
                    WHERE t.IsActive = 1
                      AND s.' + QUOTENAME(@TitleColumn) + N' LIKE dbo.fn_FT_WildcardToLike(t.Value)
              );';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
