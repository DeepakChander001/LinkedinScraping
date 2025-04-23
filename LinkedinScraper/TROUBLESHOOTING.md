# LinkedIn Scraper Troubleshooting Guide

This guide will help you solve common issues with the LinkedIn scraper.

## Authentication Issues

The most common issue is related to authentication with LinkedIn. Follow these steps to ensure proper authentication:

### Step 1: Generate fresh cookies

1. Run the cookie extraction script:
```
get_cookies.bat
```
Or manually:
```
python save_cookies.py --username "your_email" --password "your_password"
```

2. Make sure the script completes successfully and reports "Authentication verified successfully!"
3. Check that `linkedin_cookies.json` has been created and contains valid cookies.

### Step 2: Verify cookie file format

The `linkedin_cookies.json` file should look like this:
```json
[
  {
    "name": "cookie_name",
    "value": "cookie_value",
    "domain": ".linkedin.com",
    "path": "/",
    ...
  },
  ...
]
```

If your file is empty or doesn't follow this format, you'll need to regenerate the cookies.

### Step 3: Check for essential cookies

LinkedIn requires specific cookies for authentication. Ensure these cookies are present in your file:
- li_at
- JSESSIONID
- lidc

If any of these are missing, try logging in again to generate new cookies.

## Debugging

If you're still having issues, the scraper now generates debugging files:

- `linkedin_search_response.html`: HTML from the search results page
- `linkedin_error_response.html`: HTML from pages that cause errors
- `linkedin_profile_error.html`: HTML from profile pages that cause errors

Examine these files to understand what LinkedIn is returning.

## Specific Error Solutions

### Encoding Errors

If you see encoding errors like `LookupError: unknown encoding`, try these solutions:

1. Use XPath instead of CSS selectors (already implemented in the updated spider)
2. Increase the DOWNLOAD_DELAY to 5-10 seconds to avoid being flagged by LinkedIn

### Redirect to Login Page

If you're being redirected to the login page despite having cookies:

1. LinkedIn may have detected your scraping activity - wait a few hours before trying again
2. Your cookies may have expired - generate new ones
3. Try using a different IP address (VPN or proxy)

## Running the Scraper

After fixing the authentication issues:

1. Run the scraper with:
```
python run_spider.py "AI Engineer"
```

2. Check the `linkedin_data` directory for the scraped data:
   - `linkedin_profiles.json`: Complete profile data
   - `linkedin_profiles.csv`: Basic profile information
   - `linkedin_experiences.csv`: Detailed experience data

## LinkedIn Rate Limits

Be aware that LinkedIn has strict rate limits. If you scrape too aggressively, your account might be temporarily restricted or even banned. Consider:

- Increasing the DOWNLOAD_DELAY in settings.py
- Limiting the number of profiles you scrape in a single session
- Adding random delays between requests
- Scraping during off-peak hours 