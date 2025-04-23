import json
import csv
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

class LinkedInJobScraper:
    def __init__(self, headless=False):
        self.output_dir = 'output'
        self.jobs = []
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--window-size=1920,1080")
        
        # Add common options to prevent crashes
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Set Chrome binary location
        chrome_options.binary_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome-win64", "chrome-win64", "chrome.exe")
        
        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 50)
    
    def login(self):
        """Log in to LinkedIn with improved security handling"""
        try:
            # Replace with your LinkedIn credentials
            email = "example@gmail.com"
            password = "password@123"
            
            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(5)  # Increased initial wait time
            
            # Fill in email and password
            email_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(email)
            
            password_field = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_field.send_keys(password)
            
            # Click login button
            login_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            
            # Wait for login to complete and handle security verification
            time.sleep(10)  # Increased wait time for security checks
            
            # Check for security verification
            try:
                security_check = self.driver.find_element(By.CSS_SELECTOR, "div.challenge-dialog")
                if security_check.is_displayed():
                    print("\nSecurity verification required!")
                    print("Please complete the security verification manually.")
                    print("The script will wait for you to complete the verification...")
                    
                    # Wait for user to complete verification (up to 5 minutes)
                    try:
                        WebDriverWait(self.driver, 300).until(
                            lambda driver: "feed" in driver.current_url
                        )
                        print("Security verification completed successfully!")
                    except TimeoutException:
                        print("Security verification timeout. Please try again.")
                        return False
            except NoSuchElementException:
                # No security check found, continue with normal login
                pass
            
            # Verify login was successful
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: "feed" in driver.current_url or "jobs" in driver.current_url
                )
                print("Login successful")
                return True
            except TimeoutException:
                print("Login verification failed")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def collect_job_urls(self, keyword, max_pages=50):
        """Collect job URLs from all pages and save to file"""
        try:
            job_urls = set()  # Use set to avoid duplicates
            current_page = 1
            
            # Construct the initial search URL with US location and specific parameters
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&geoId=103644278&origin=JOB_SEARCH_PAGE_SEARCH_BUTTON&refresh=true"
            print(f"Navigating to URL: {search_url}")
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            # Get total number of pages
            try:
                # Wait for the pagination element to be present
                pagination = WebDriverWait(self.driver, 50).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ul.artdeco-pagination__pages"))
                )
                page_buttons = pagination.find_elements(By.CSS_SELECTOR, "li.artdeco-pagination__indicator")
                total_pages = len(page_buttons)
                print(f"Total pages found: {total_pages}")
            except Exception as e:
                print(f"Could not determine total pages: {e}")
                total_pages = 1
            
            while current_page <= min(total_pages, max_pages):
                print(f"\nProcessing page {current_page} of {min(total_pages, max_pages)}...")
                
                # Scroll multiple times to ensure all content is loaded
                print("Scrolling to load content...")
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_attempts = 0
                max_scroll_attempts = 5
                
                while scroll_attempts < max_scroll_attempts:
                    # Scroll down
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1, 2))
                    
                    # Scroll up a bit to trigger loading
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 500);")
                    time.sleep(random.uniform(1, 2))
                    
                    # Calculate new scroll height
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    scroll_attempts += 1
                
                # Try to find job cards with multiple selectors
                print("\nTrying to find job cards...")
                job_cards = []
                selectors_to_try = [
                    "div.job-card-container",
                    "div.job-card-list__entity",
                    "li.jobs-search-results__list-item",
                    "div[data-test-job-card]",
                    "div.job-card-list__entity--focused",
                    "div.job-card-container__link",
                    "div.job-card-container__link--wrapper",
                    "div.job-card-container__link-wrapper",
                    "div.job-card-container__link--wrapper--wrapper"
                ]
                
                for selector in selectors_to_try:
                    try:
                        print(f"Trying selector: {selector}")
                        job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if job_cards:
                            print(f"Found {len(job_cards)} jobs using selector: {selector}")
                            break
                    except Exception as e:
                        print(f"Error with selector {selector}: {str(e)}")
                        continue
                
                if not job_cards:
                    print("No job cards found. Taking screenshot for debugging...")
                    self.driver.save_screenshot("debug_screenshot.png")
                    print("Screenshot saved as debug_screenshot.png")
                    break
                
                # Process each job card to get URLs
                print("\nProcessing job cards...")
                for card in job_cards:
                    try:
                        # Try multiple selectors for job link
                        job_link = None
                        link_selectors = [
                            "a.job-card-list__title",
                            "a.job-card-container__link",
                            "a[data-control-name='job_card_click']",
                            "a[data-test-job-card-link]",
                            "a.job-card-list__title--link",
                            "a.job-card-container__link--wrapper",
                            "a.job-card-container__link-wrapper",
                            "a.job-card-container__link--wrapper--wrapper"
                        ]
                        
                        for selector in link_selectors:
                            try:
                                print(f"Trying link selector: {selector}")
                                job_link = card.find_element(By.CSS_SELECTOR, selector)
                                if job_link:
                                    break
                            except Exception as e:
                                print(f"Error with link selector {selector}: {str(e)}")
                                continue
                        
                        if not job_link:
                            print("No job link found in card")
                            continue
                        
                        job_url = job_link.get_attribute("href")
                        if job_url:
                            job_urls.add(job_url)
                            print(f"Found job URL: {job_url}")
                        else:
                            print("No href attribute found in job link")
                        
                    except Exception as e:
                        print(f"Error processing job card: {e}")
                        continue
                
                # Try to navigate to next page
                try:
                    # Find the next page button
                    next_page_selector = f"li[data-test-pagination-page-btn='{current_page + 1}'] button"
                    next_button = WebDriverWait(self.driver, 50).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, next_page_selector))
                    )
                    
                    # Check if we're on the last page
                    if current_page >= total_pages:
                        print("Reached the last page")
                        break
                    
                    # Scroll to the button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    
                    # Click the next button
                    next_button.click()
                    time.sleep(random.uniform(3, 5))
                    current_page += 1
                    
                except NoSuchElementException:
                    print("No next page button found. This may be the last page.")
                    break
                except Exception as e:
                    print(f"Error navigating to next page: {e}")
                    break
            
            # Save URLs to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            urls_file = os.path.join(self.output_dir, f'job_urls_{keyword.replace(" ", "_")}_US_{timestamp}.txt')
            with open(urls_file, 'w', encoding='utf-8') as f:
                for url in job_urls:
                    f.write(f"{url}\n")
            
            print(f"\nSaved {len(job_urls)} job URLs to {urls_file}")
            return urls_file
            
        except Exception as e:
            print(f"Error collecting job URLs: {e}")
            return None

    def scrape_jobs_from_urls(self, urls_file):
        """Scrape job details from a file containing URLs"""
        try:
            # Read URLs from file
            with open(urls_file, 'r', encoding='utf-8') as f:
                job_urls = [line.strip() for line in f if line.strip()]
            
            print(f"Starting to scrape details for {len(job_urls)} jobs...")
            
            for i, url in enumerate(job_urls, 1):
                try:
                    print(f"Scraping job {i}/{len(job_urls)}: {url}")
                    job_data = self.scrape_job_details(url)
                    if job_data:
                        self.jobs.append(job_data)
                        print(f"Successfully scraped: {job_data['job_title']} at {job_data['company_name']}")
                    
                    # Add delay between jobs
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"Error scraping job {url}: {e}")
                    continue
            
            # Save the data
            self._save_data()
            return True
            
        except Exception as e:
            print(f"Error during job details scraping: {e}")
            return False

    def scrape_job_details(self, job_url):
        """Scrape details of a single job"""
        try:
            self.driver.get(job_url)
            time.sleep(random.uniform(2, 4))
            
            job_data = {
                'job_url': job_url,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Get company name
            try:
                company_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__company-name a")
                job_data['company_name'] = company_element.text.strip()
            except:
                job_data['company_name'] = "Not found"
            
            # Get job title
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-title")
                job_data['job_title'] = title_element.text.strip()
            except:
                job_data['job_title'] = "Not found"
            
            # Get location
            try:
                location_element = self.driver.find_element(By.CSS_SELECTOR, ".tvm__text.tvm__text--low-emphasis")
                job_data['location'] = location_element.text.strip()
            except:
                job_data['location'] = "Not found"
            
            # Get job type (Entry level, Mid-Senior level, etc.)
            try:
                employment_level_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__job-insight-view-model-secondary")
                job_data['job_type'] = employment_level_element.text.strip()
            except:
                job_data['job_type'] = "Not found"
            
            # Get job description
            try:
                description_element = self.driver.find_element(By.CSS_SELECTOR, "div.mt4 p[dir='ltr']")
                job_data['description'] = description_element.text.strip()
            except:
                job_data['description'] = "Not found"
            
            # Get all skills
            try:
                skills_element = self.driver.find_element(By.CSS_SELECTOR, ".job-details-how-you-match__skills-item-subtitle")
                skills_text = skills_element.text.strip()
                # Remove any "Skills:" prefix if present
                if skills_text.startswith("Skills:"):
                    skills_text = skills_text[7:].strip()
                job_data['skills'] = skills_text
            except:
                job_data['skills'] = "Not found"
            
            return job_data
            
        except Exception as e:
            print(f"Error scraping job details: {e}")
            return None
    
    def scrape_jobs(self, keyword, max_pages=50):
        """Scrape jobs based on keyword"""
        try:
            # Construct search URL
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location=India"
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            current_page = 1
            total_pages = 1
            
            # First try to get the total number of pages
            try:
                page_state = self.driver.find_element(By.CSS_SELECTOR, "p.jobs-search-pagination__page-state")
                total_pages = int(page_state.text.split("of")[1].strip())
                print(f"Total pages found: {total_pages}")
            except:
                print("Could not determine total pages, defaulting to 1")
            
            while current_page <= min(total_pages, max_pages):
                print(f"\nProcessing page {current_page} of {min(total_pages, max_pages)}...")
                
                # Scroll multiple times to ensure all content is loaded
                for _ in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1, 2))
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(random.uniform(1, 2))
                
                # Try multiple selectors to find job cards
                job_cards = []
                selectors_to_try = [
                    ".job-card-container",
                    ".job-card-list__entity",
                    ".jobs-search-results__list-item",
                    "li.jobs-search-results__list-item",
                    "div[data-test-job-card]"
                ]
                
                for selector in selectors_to_try:
                    try:
                        job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if job_cards:
                            print(f"Found {len(job_cards)} jobs using selector: {selector}")
                            break
                    except:
                        continue
                
                if not job_cards:
                    print("No job cards found on this page")
                    break
                
                # Process each job card
                for card in job_cards:
                    try:
                        # Try multiple selectors for job link
                        job_link = None
                        link_selectors = [
                            "a.job-card-list__title",
                            "a.job-card-container__link",
                            "a[data-control-name='job_card_click']",
                            "a[data-test-job-card-link]",
                            "a.job-card-list__title--link",
                            "a.job-card-container__link--wrapper"
                        ]
                        
                        for selector in link_selectors:
                            try:
                                job_link = card.find_element(By.CSS_SELECTOR, selector)
                                if job_link:
                                    break
                            except:
                                continue
                        
                        if not job_link:
                            continue
                        
                        job_url = job_link.get_attribute("href")
                        if not job_url:
                            continue
                        
                        # Scrape job details
                        job_data = self.scrape_job_details(job_url)
                        if job_data:
                            self.jobs.append(job_data)
                            print(f"Scraped job: {job_data['job_title']} at {job_data['company_name']}")
                        
                        # Add delay between jobs
                        time.sleep(random.uniform(2, 4))
                        
                    except Exception as e:
                        print(f"Error processing job card: {e}")
                        continue
                
                # Try to go to next page
                try:
                    # Find the next button
                    next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='View next page']")
                    
                    # Check if we're on the last page
                    if current_page >= total_pages:
                        print("Reached the last page")
                        break
                    
                    # Scroll to the button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    
                    # Click the next button
                    next_button.click()
                    time.sleep(random.uniform(3, 5))
                    current_page += 1
                    
                except NoSuchElementException:
                    print("No 'Next' button found. This may be the last page.")
                    break
                except Exception as e:
                    print(f"Error navigating to next page: {e}")
                    break
            
            # Save the data
            self._save_data()
            return True
            
        except Exception as e:
            print(f"Error during job scraping: {e}")
            return False
    
    def _scroll_page(self):
        """Scroll the page to load all content"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 2))
                
                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            print(f"Error scrolling page: {e}")
    
    def _save_data(self):
        """Save scraped data to JSON and CSV files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to JSON
            json_file = os.path.join(self.output_dir, f'linkedin_jobs_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.jobs, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(self.jobs)} jobs to JSON: {json_file}")
            
            # Save to CSV
            csv_file = os.path.join(self.output_dir, f'linkedin_jobs_{timestamp}.csv')
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    'Job Title', 'Company Name', 'Location', 'Posting Info',
                    'Job Type', 'Apply Link', 'Job URL', 'Scraped At'
                ])
                # Write data rows
                for job in self.jobs:
                    writer.writerow([
                        job.get('job_title', ''),
                        job.get('company_name', ''),
                        job.get('location', ''),
                        job.get('posting_info', ''),
                        job.get('job_type', ''),
                        job.get('apply_link', ''),
                        job.get('job_url', ''),
                        job.get('scraped_at', '')
                    ])
            print(f"Saved {len(self.jobs)} jobs to CSV: {csv_file}")
            
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper')
    parser.add_argument('--keyword', help='Job search keyword', default='AI Engineer')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum number of pages to scrape')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--collect-urls', action='store_true', help='Only collect job URLs')
    parser.add_argument('--urls-file', help='File containing job URLs to scrape')
    
    args = parser.parse_args()
    
    scraper = LinkedInJobScraper(headless=args.headless)
    
    try:
        if scraper.login():
            if args.collect_urls:
                print(f"Starting to collect job URLs for keyword: {args.keyword}")
                urls_file = scraper.collect_job_urls(args.keyword, max_pages=args.max_pages)
                if urls_file:
                    print(f"Job URLs saved to: {urls_file}")
                    print(f"\nTo scrape job details, run:")
                    print(f"python linkedin_job_scraper.py --urls-file {urls_file}")
            elif args.urls_file:
                # Check if the file exists
                if not os.path.exists(args.urls_file):
                    print(f"Error: File not found: {args.urls_file}")
                    print("Please make sure to use the correct file path from the URL collection step.")
                    print("Run the URL collection first with: python linkedin_job_scraper.py --keyword 'AI Engineer' --collect-urls")
                    exit(1)
                
                print(f"Starting to scrape job details from: {args.urls_file}")
                success = scraper.scrape_jobs_from_urls(args.urls_file)
                if success:
                    print(f"Successfully scraped {len(scraper.jobs)} jobs")
                else:
                    print("Failed to scrape jobs")
            else:
                print("Please specify either --collect-urls or --urls-file")
        else:
            print("Failed to login to LinkedIn")
    finally:
        scraper.close() 