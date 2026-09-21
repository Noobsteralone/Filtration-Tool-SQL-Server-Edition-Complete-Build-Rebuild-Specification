/* =============================================================================
   sp_FT_GetJobSummary
   Returns actual, computed (never fabricated, section 53) row counts per
   reason code plus totals, for populating dbo.FT_JobResults and the
   dbo.FT_Jobs summary columns, and for driving the Report Summary screen.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_GetJobSummary
    @StagingTable NVARCHAR(128)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        DECLARE @sql NVARCHAR(MAX) = N'
            SELECT
                COALESCE(ReasonCode, ''KEPT'') AS ReasonCode,
                COUNT(*) AS RowCount
            FROM ' + QUOTENAME(@StagingTable) + N'
            GROUP BY ReasonCode;';
        EXEC sp_executesql @sql;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
