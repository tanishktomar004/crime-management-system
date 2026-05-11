@echo off
title Crime Management System
echo Starting Crime Management System...
echo.
python crime_management_system.py
if errorlevel 1 (
    echo.
    echo ERROR: Could not start the application.
    echo Make sure Python is installed and added to PATH.
    pause
)
