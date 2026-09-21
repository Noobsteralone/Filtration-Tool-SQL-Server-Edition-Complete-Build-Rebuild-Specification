/* =============================================================================
   sp_FT_FilterNumericUsernames   (sections 20 & 21, consolidated)

   NOTE ON CONSOLIDATION: the source specification describes the "digit-only
   / invalid numeric username" rule twice (section 21) and separately
   describes the "one character username" rule (section 20). Both rules
   operate on the same EmailLocalPart column and are implemented once, in
   this single procedure, each independently toggleable and each emitting
   its own distinct reason code as required by section 24:
     - ONE_CHARACTER_USERNAME   : LEN(local part) = 1
     - INVALID_NUMERIC_USERNAME : local part is non-empty and made up
                                   entirely of digits (i.e. stripping all
                                   digits leaves nothing) -- this covers
                                   every example in the spec: 0, 1, 000, 111.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_FilterNumericUsernames
    @StagingTable               NVARCHAR(128),
    @EnableOneCharacterUsername BIT = 1,
    @EnableNumericUsername      BIT = 1,
    @RowsAffected               INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        DECLARE @total INT = 0;

        IF @EnableOneCharacterUsername = 1
        BEGIN
            DECLARE @sql1 NVARCHAR(MAX) = N'
                UPDATE s
                SET s.ReasonCode = ''ONE_CHARACTER_USERNAME''
                FROM ' + QUOTENAME(@StagingTable) + N' AS s
                WHERE s.ReasonCode IS NULL
                  AND s.IsOtherTLD = 0
                  AND LEN(s.EmailLocalPart) = 1;';
            EXEC sp_executesql @sql1;
            SET @total += @@ROWCOUNT;
        END

        IF @EnableNumericUsername = 1
        BEGIN
            DECLARE @sql2 NVARCHAR(MAX) = N'
                UPDATE s
                SET s.ReasonCode = ''INVALID_NUMERIC_USERNAME''
                FROM ' + QUOTENAME(@StagingTable) + N' AS s
                WHERE s.ReasonCode IS NULL
                  AND s.IsOtherTLD = 0
                  AND LEN(s.EmailLocalPart) > 0
                  AND dbo.fn_FT_StripDigits(s.EmailLocalPart) = '''';';
            EXEC sp_executesql @sql2;
            SET @total += @@ROWCOUNT;
        END

        SET @RowsAffected = @total;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
