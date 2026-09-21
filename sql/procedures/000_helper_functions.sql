/* =============================================================================
   FT - Filtration Tool
   000_helper_functions.sql

   Shared helper functions used by every stored procedure below. These exist
   so identifier-safety and digit-stripping logic each live in exactly ONE
   place (mirrors the "single reusable module" rule applied to the Python
   keyword-matcher, section 17/46).
   ============================================================================= */

USE [FT_Filtration];
GO

/* Whitelists a SQL identifier: letters/digits/underscore only, must start
   with a letter or underscore. Every stored procedure that builds dynamic
   SQL around a staging table or column name calls this FIRST and refuses
   to proceed if it returns 0. This is what keeps dynamic SQL safe without
   ever concatenating raw user/file-header input into a statement. */
CREATE OR ALTER FUNCTION dbo.fn_FT_IsSafeIdentifier(@Name NVARCHAR(128))
RETURNS BIT
AS
BEGIN
    DECLARE @Result BIT = 0;
    IF @Name IS NOT NULL
       AND LEN(@Name) BETWEEN 1 AND 128
       AND @Name NOT LIKE '%[^A-Za-z0-9_]%'
       AND @Name LIKE '[A-Za-z_]%'
        SET @Result = 1;
    RETURN @Result;
END
GO

/* Removes ASCII digits 0-9 from a string. Used exactly once by
   sp_FT_FilterNumericUsernames (section 21 -- the digit-username rule
   appears twice in the source specification; it is implemented once here
   and consolidated). */
CREATE OR ALTER FUNCTION dbo.fn_FT_StripDigits(@Value NVARCHAR(500))
RETURNS NVARCHAR(500)
AS
BEGIN
    IF @Value IS NULL RETURN NULL;
    RETURN REPLACE(TRANSLATE(@Value, '0123456789', '##########'), '#', '');
END
GO

/* Converts an admin-authored wildcard pattern (using '*' as the only
   wildcard token, per section 17) into a safe SQL Server LIKE pattern,
   escaping any characters that already carry meaning in LIKE ('%','_','[').
   This is the single reusable SQL-side translation used by every keyword /
   title / industry filter procedure. */
CREATE OR ALTER FUNCTION dbo.fn_FT_WildcardToLike(@Pattern NVARCHAR(255))
RETURNS NVARCHAR(300)
AS
BEGIN
    IF @Pattern IS NULL RETURN NULL;
    DECLARE @p NVARCHAR(300) = @Pattern;
    SET @p = REPLACE(@p, '[', '[[]');
    SET @p = REPLACE(@p, '%', '[%]');
    SET @p = REPLACE(@p, '_', '[_]');
    SET @p = REPLACE(@p, '*', '%');
    RETURN @p;
END
GO
