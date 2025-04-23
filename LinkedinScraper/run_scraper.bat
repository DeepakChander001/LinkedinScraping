@echo off
echo LinkedIn Profile Scraper
echo ======================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking required packages...
pip install selenium webdriver-manager >nul 2>&1
if %errorlevel% neq 0 (
    echo Failed to install required packages
    pause
    exit /b 1
)

echo.
echo Starting the scraper...
echo Note: This may take several hours to complete
echo Progress will be saved automatically
echo.

REM Run the scraper
python run_scraper.py

echo.
echo Scraping completed
pause 