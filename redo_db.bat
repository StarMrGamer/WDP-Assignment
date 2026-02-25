@echo off
echo Removing database.db...
if exist database.db del /f database.db

echo Seeding base data...
python seed_db.py
if errorlevel 1 (
    echo seed_db.py failed. Aborting.
    exit /b 1
)

echo Seeding usage data...
python seed_usage.py
if errorlevel 1 (
    echo seed_usage.py failed.
    exit /b 1
)

echo Done.
