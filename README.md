# Web Scraping Projects

This repository contains web scraping scripts for various job portals.

## Projects

### 1. LinkedIn Job Scraper
A Python script to scrape job listings from LinkedIn.

#### Features:
- Collects job URLs based on keyword search
- Scrapes detailed job information
- Saves data in JSON and CSV formats
- Handles pagination
- Includes error handling and logging

#### Usage:
```bash
# Collect job URLs
python linkedin_job_scraper.py --keyword "AI Engineer" --max-pages 10 --collect-urls

# Scrape job details
python linkedin_job_scraper.py --urls-file output/job_urls_AI_Engineer_YYYYMMDD_HHMMSS.txt
```

### 2. Naukri Job Scraper
A Python script to scrape job listings from Naukri.com.

#### Features:
- Collects job URLs based on keyword, location, and experience
- Scrapes detailed job information
- Saves data in JSON and CSV formats
- Handles pagination
- Includes error handling and logging

#### Usage:
```bash
# Collect job URLs
python naukri_job_scraper.py --keyword "AI ML Engineer" --location "united-states-usa" --experience "0" --max-pages 10 --collect-urls

# Scrape job details
python naukri_job_scraper.py --urls-file output/naukri_job_urls_AI_ML_Engineer_united-states-usa_YYYYMMDD_HHMMSS.txt
```

## Requirements

- Python 3.7+
- Selenium
- ChromeDriver
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/web-scraping.git
cd web-scraping
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download ChromeDriver and place it in your PATH

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 