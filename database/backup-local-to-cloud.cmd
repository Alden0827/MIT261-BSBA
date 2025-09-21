@echo off
setlocal enabledelayedexpansion

:: Title
title MongoDB Sync - Upload (Local → Cloud)

echo ============================================
echo   MongoDB Backup (Local) and Restore (Cloud)
echo ============================================
echo.
echo This will perform the following actions:
echo 1. Backup the local database "mit261".
echo 2. Restore the backup into your cloud cluster (dropping existing data).
echo.

:: Ask for confirmation
set /p confirm="Do you want to continue? (Y/N): "

if /i "%confirm%" neq "Y" (
    echo Operation cancelled.
    pause
    exit /b
)

echo.
echo Starting local backup...

"C:\Program Files\MongoDB\Tools\100\bin\mongodump.exe" ^
  --db mit261 ^
  --out ./backup

if errorlevel 1 (
    echo ❌ Backup failed!
    pause
    exit /b
)

echo ✅ Local backup completed successfully.
echo.

echo Starting restore to cloud...

"C:\Program Files\MongoDB\Tools\100\bin\mongorestore.exe" ^
  --uri "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261" ^
  --drop ./backup/mit261

if errorlevel 1 (
    echo ❌ Restore failed!
    pause
    exit /b
)

echo ✅ Restore to cloud completed successfully.
echo.
pause
