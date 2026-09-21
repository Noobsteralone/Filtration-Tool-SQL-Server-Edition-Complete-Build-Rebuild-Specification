/* =============================================================================
   sp_FT_CheckDuplicateVsMaster
   Supporting procedure for the "MASTER CHECK" step in the pipeline diagram
   (section 69), run after in-file deduplication and before the Personal /
   Restricted / Spam filters. Tags rows whose normalized e-mail already
   exists in dbo.FT_MasterEmails as DUPLICATE_VS_MASTER. This is distinct
   from sp_FT_MergeToMaster, which performs the final write of the Kept set
   into Master once the whole pipeline has finished.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_CheckDuplicateVsMaster
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
            SET s.ReasonCode = ''DUPLICATE_VS_MASTER''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.IsOtherTLD = 0
              AND EXISTS (SELECT 1 FROM dbo.FT_MasterEmails m WHERE m.Email = s.NormalizedEmail);';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
