@echo off
echo LinkedIn Selenium Scraper
echo -----------------------
set /p search="Enter search term (e.g., AI Engineer): "
set /p max="Enter maximum number of profiles to scrape (e.g., 5): "

python selenium_scraper.py --search "%search%" --max %max%
echo.
echo Check the linkedin_data directory for results.
pause 