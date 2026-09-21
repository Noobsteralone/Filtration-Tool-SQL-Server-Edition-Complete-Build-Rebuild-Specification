/* =============================================================================
   FT - Filtration Tool
   000_create_database.sql

   Creates the FT_Filtration database if it does not already exist.
   Idempotent: safe to run repeatedly.

   Run this script connected to the `master` database on LAP-S2M059.
   ============================================================================= */

IF DB_ID(N'FT_Filtration') IS NULL
BEGIN
    PRINT 'Creating database FT_Filtration...';
    EXEC(N'CREATE DATABASE [FT_Filtration]');
END
ELSE
BEGIN
    PRINT 'Database FT_Filtration already exists. Skipping creation.';
END
GO

ALTER DATABASE [FT_Filtration] SET READ_COMMITTED_SNAPSHOT ON;
GO
