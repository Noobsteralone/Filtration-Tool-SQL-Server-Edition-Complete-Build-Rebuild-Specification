/* =============================================================================
   sp_FT_RemoveInvalidEmails   (Pipeline Step 3)
   Tags rows whose RAW e-mail value lacks '@' or '.' as INVALID_EMAIL.
   Never deletes -- tags in place so the row remains fully auditable.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_RemoveInvalidEmails
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
            SET s.ReasonCode = ''INVALID_EMAIL''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND (
                    s.' + QUOTENAME(@EmailColumn) + N' IS NULL
                 OR LTRIM(RTRIM(s.' + QUOTENAME(@EmailColumn) + N')) = ''''
                 OR CHARINDEX(''@'', s.' + QUOTENAME(@EmailColumn) + N') = 0
                 OR CHARINDEX(''.'', s.' + QUOTENAME(@EmailColumn) + N') = 0
              );';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
