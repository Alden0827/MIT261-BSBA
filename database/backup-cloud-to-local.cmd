@echo off
setlocal

title MongoDB Sync - Down (Cloud → Local)

echo ============================================
echo   MongoDB Sync - Cloud to Local
echo ============================================
echo.
echo This will:
echo 1. Backup database from your CLOUD cluster.
echo 2. Restore it into your LOCAL DB "mit261" (dropping existing data).
echo.

set /p confirm="Proceed? (Y/N): "

if /i not "%confirm%"=="Y" (
    echo ❌ Cancelled.
    pause
    exit /b
)

echo.
echo 📥 Backing up from cloud...
"C:\Program Files\MongoDB\Tools\100\bin\mongodump.exe" ^
  --uri "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261" ^
  --out ./backup

if errorlevel 1 (
    echo ❌ Backup failed.
    pause
    exit /b
)

echo ✅ Cloud backup completed.
echo.

echo 🔄 Restoring to local server...
"C:\Program Files\MongoDB\Tools\100\bin\mongorestore.exe" ^
  --db mit261 --drop ./backup/mit261

if errorlevel 1 (
    echo ❌ Restore failed.
    pause
    exit /b
)

echo.
echo ✅ Cloud → Local sync completed successfully!
pause
