/* =============================================================================
   sp_FT_FilterUsernameEqualsDomain   (section 22)
   Compares the e-mail's local part to its "domain name before the TLD"
   (EmailDomain with EmailTLD stripped off), e.g. sales@sales.com ->
   local part 'sales' == domain name 'sales'.
   ============================================================================= */
USE [FT_Filtration];
GO

CREATE OR ALTER PROCEDURE dbo.sp_FT_FilterUsernameEqualsDomain
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
            SET s.ReasonCode = ''USERNAME_EQUALS_DOMAIN''
            FROM ' + QUOTENAME(@StagingTable) + N' AS s
            WHERE s.ReasonCode IS NULL
              AND s.IsOtherTLD = 0
              AND s.EmailTLD IS NOT NULL
              AND LEN(s.EmailDomain) > LEN(s.EmailTLD)
              AND LEFT(s.EmailDomain, LEN(s.EmailDomain) - LEN(s.EmailTLD)) = s.EmailLocalPart;';
        EXEC sp_executesql @sql;
        SET @RowsAffected = @@ROWCOUNT;
    END TRY
    BEGIN CATCH
        THROW;
    END CATCH
END
GO
