/* =============================================================================
   sp_FT_IndexStagingTable
   Creates the working indexes on a job's staging table AFTER the bulk load
   has completed (section 35: avoid indexes before bulk insert). Idempotent.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_IndexStagingTable
    @StagingTable NVARCHAR(128)
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        IF NOT EXISTS (
            SELECT 1 FROM sys.indexes
            WHERE name = 'IX_' + @StagingTable + '_NormalizedEmail'
              AND object_id = OBJECT_ID(@StagingTable)
        )
        BEGIN
            DECLARE @sql NVARCHAR(MAX) =
                N'CREATE INDEX ' + QUOTENAME('IX_' + @StagingTable + '_NormalizedEmail') +
                N' ON ' + QUOTENAME(@StagingTable) + N' (NormalizedEmail) INCLUDE (ReasonCode, IsOtherTLD);';
            EXEC sp_executesql @sql;
        END

        IF NOT EXISTS (
            SELECT 1 FROM sys.indexes
            WHERE name = 'IX_' + @StagingTable + '_ReasonCode'
              AND object_id = OBJECT_ID(@StagingTable)
        )
        BEGIN
            DECLARE @sql2 NVARCHAR(MAX) =
                N'CREATE INDEX ' + QUOTENAME('IX_' + @StagingTable + '_ReasonCode') +
                N' ON ' + QUOTENAME(@StagingTable) + N' (ReasonCode);';
            EXEC sp_executesql @sql2;
        END
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
