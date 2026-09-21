/* =============================================================================
   sp_FT_DeduplicateEmails   (Pipeline Step 5, applied post-TLD-separation to
   the Allowed-TLD branch only)
   Keeps exactly one row per NormalizedEmail (first by RowID, a deterministic
   surrogate identity column) and tags the rest DUPLICATE_EMAIL.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_DeduplicateEmails
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
            WITH DupCte AS (
                SELECT RowID,
                       ROW_NUMBER() OVER (PARTITION BY NormalizedEmail ORDER BY RowID) AS RowNum
                FROM ' + QUOTENAME(@StagingTable) + N'
                WHERE ReasonCode IS NULL AND IsOtherTLD = 0
            )
            UPDATE s
            SET s.ReasonCode = ''DUPLICATE_EMAIL''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            JOIN DupCte d ON d.RowID = s.RowID
            WHERE d.RowNum > 1;';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
