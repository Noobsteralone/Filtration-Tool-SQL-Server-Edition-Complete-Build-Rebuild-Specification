/* =============================================================================
   sp_FT_SeparateTLD   (Pipeline Steps 6 & 7)
   Classifies each surviving row's TLD against dbo.FT_AllowedTLDs. Rows on an
   allowed TLD stay IsOtherTLD = 0 and continue through the pipeline. Every
   other row is tagged IsOtherTLD = 1 / ReasonCode = 'OTHER_TLD' and, per
   section 14, bypasses the rest of the filtration pipeline entirely (it is
   preserved, never deleted, and is not counted as a rejection).
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_SeparateTLD
    @StagingTable    NVARCHAR(128),
    @RowsAllowedTLD  INT OUTPUT,
    @RowsOtherTLD    INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        IF dbo.fn_FT_IsSafeIdentifier(@StagingTable) = 0
            THROW 51000, 'Unsafe staging table name.', 1;
        IF OBJECT_ID(@StagingTable, 'U') IS NULL
            THROW 51001, 'Staging table does not exist.', 1;

        -- Allowed TLD match: suffix comparison against every active
        -- allowed value (supports both single-level '.com' and multi-level
        -- '.co.uk' style entries if an administrator adds them).
        DECLARE @sqlAllowed NVARCHAR(MAX) = N'
            UPDATE s
            SET s.EmailTLD = a.Value, s.IsOtherTLD = 0
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            CROSS APPLY (
                SELECT TOP 1 Value
                FROM dbo.FT_AllowedTLDs
                WHERE IsActive = 1
                  AND s.EmailDomain LIKE ''%'' + Value
                ORDER BY LEN(Value) DESC
            ) AS a
            WHERE s.ReasonCode IS NULL;';
        EXEC sp_executesql @sqlAllowed;
        SET @RowsAllowedTLD = @@ROWCOUNT;

        -- Everything else with no reason code yet and no EmailTLD assigned
        -- is Other-TLD: preserve, tag, derive the TLD from the last domain
        -- label for reporting purposes only.
        DECLARE @sqlOther NVARCHAR(MAX) = N'
            UPDATE s
            SET s.IsOtherTLD = 1,
                s.ReasonCode = ''OTHER_TLD'',
                s.EmailTLD = ''.'' + PARSENAME(s.EmailDomain, 1)
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.EmailTLD IS NULL;';
        EXEC sp_executesql @sqlOther;
        SET @RowsOtherTLD = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
