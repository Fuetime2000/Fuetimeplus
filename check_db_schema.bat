@echo off
echo Checking database schema...

set DB_PATH=instance\fuetime.db

echo.
echo Checking if database exists...
if not exist "%DB_PATH%" (
    echo ❌ Database file not found at: %DB_PATH%
    exit /b 1
)

echo.
echo Database file exists at: %DB_PATH%

echo.
echo Listing all tables in the database...
sqlite3 "%DB_PATH%" ".tables"

echo.
echo Checking user table schema...
sqlite3 "%DB_PATH%" ".schema user"

echo.
echo Checking if 'verified' column exists in user table...
sqlite3 "%DB_PATH%" "SELECT name FROM pragma_table_info('user') WHERE name='verified';"

echo.
echo Done.
