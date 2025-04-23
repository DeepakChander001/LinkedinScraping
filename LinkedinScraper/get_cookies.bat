@echo off
echo LinkedIn Cookie Extractor
echo -----------------------
set /p username="Enter your LinkedIn email: "
set /p password="Enter your LinkedIn password: "
python save_cookies.py --username "%username%" --password "%password%"
echo.
echo If successful, cookies have been saved to linkedin_cookies.json
echo You can now run the scraper.
pause 