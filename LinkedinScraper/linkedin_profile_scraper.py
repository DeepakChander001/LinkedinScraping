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
import argparse
import urllib.parse
from dotenv import load_dotenv
from selenium.webdriver.common.keys import Keys

class LinkedInProfileScraper:
    def __init__(self, headless=False):
        self.output_dir = 'output'
        self.profiles = []
        
        # Load environment variables
        load_dotenv()
        
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
        
        # Add user agent and other headers
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        
        # Execute CDP commands to prevent detection
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        
        # Login to LinkedIn
        self._login()
    
    def _login(self):
        """Login to LinkedIn"""
        try:
            print("Attempting to login to LinkedIn...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(random.uniform(2, 3))
            
            # Get credentials from environment variables
            email = os.getenv('LINKEDIN_EMAIL')
            password = os.getenv('LINKEDIN_PASSWORD')
            
            if not email or not password:
                print("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")
                return False
            
            # Enter email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(email)
            time.sleep(random.uniform(0.5, 1))
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            time.sleep(random.uniform(0.5, 1))
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            time.sleep(random.uniform(3, 5))
            
            # Check if login was successful
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.global-nav")))
                print("Successfully logged in to LinkedIn")
                return True
            except TimeoutException:
                print("Login failed. Please check your credentials")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def collect_profile_urls(self, keyword, max_pages=10):
        """Collect profile URLs from LinkedIn search results"""
        print(f"Starting to collect profile URLs for keyword: {keyword}")
        
        try:
            # First navigate to LinkedIn homepage
            self.driver.get("https://www.linkedin.com")
            time.sleep(random.uniform(3, 5))
            
            # Check if we're on the login page
            try:
                login_form = self.driver.find_element(By.ID, "username")
                if login_form:
                    print("Login form detected. Attempting to login...")
                    self._login()
                    time.sleep(random.uniform(3, 5))
            except:
                print("No login form detected, proceeding with search...")
            
            # Now navigate to the search page
            self.driver.get("https://www.linkedin.com/search/results/people/")
            time.sleep(random.uniform(3, 5))
            
            # Wait for the search input to be present
            try:
                # Try multiple selectors for the search input
                search_selectors = [
                    'input.search-global-typeahead__input',
                    'input[aria-label="Search"]',
                    'input[placeholder="Search"]',
                    'input[type="text"]',
                    'input.search-global-typeahead__input[type="text"]'
                ]
                
                search_input = None
                for selector in search_selectors:
                    try:
                        search_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if search_input:
                            print(f"Found search input using selector: {selector}")
                            break
                    except:
                        continue
                
                if not search_input:
                    print("Could not find search input with any selector")
                    # Take a screenshot for debugging
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_path = os.path.join(self.output_dir, f'search_input_error_{timestamp}.png')
                    self.driver.save_screenshot(screenshot_path)
                    print(f"Saved screenshot to: {screenshot_path}")
                    return False
                
                # Clear and fill the search input
                search_input.clear()
                time.sleep(random.uniform(1, 2))
                search_input.send_keys(keyword)
                time.sleep(random.uniform(1, 2))
                search_input.send_keys(Keys.RETURN)
                time.sleep(random.uniform(3, 5))
                
                # Wait for search results to load
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-results-container"))
                    )
                    print("Search results loaded successfully")
                except:
                    print("Could not find search results container")
                    return False
                
                # Rest of the method remains the same...
                # Initialize variables for pagination
                unique_urls = set()
                consecutive_empty_pages = 0
                max_consecutive_empty = 3
                current_page = 1
                
                while current_page <= max_pages:
                    print(f"\nProcessing page {current_page} of {max_pages}...")
                    
                    # Scroll to load all content
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(2, 3))
                    
                    # Try multiple selectors for profile cards
                    profile_cards = []
                    selectors = [
                        "li.CEcHrdwtjVAgeTjyccnvzMDqSMamhug",  # New LinkedIn profile card container
                        "div.AofmRLXothgrTDeNYFzddCoETJMAUMYFc",
                        "div.kSLYBkmXErFexHCzSQiOgYSWnzHbAqDUErI"
                    ]
                    
                    for selector in selectors:
                        try:
                            cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if cards:
                                print(f"Found {len(cards)} profiles using selector: {selector}")
                                profile_cards = cards
                                break
                        except Exception as e:
                            print(f"Error with selector {selector}: {e}")
                            continue
                    
                    if not profile_cards:
                        print("No profile cards found. The page structure might have changed.")
                        # Take a screenshot for debugging
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = os.path.join(self.output_dir, f'debug_screenshot_{timestamp}.png')
                        self.driver.save_screenshot(screenshot_path)
                        print(f"Saved debug screenshot to: {screenshot_path}")
                        return None
                    
                    # Extract URLs from profile cards
                    for card in profile_cards:
                        try:
                            # Try multiple selectors for profile links
                            link_selectors = [
                                "a.FQrEAtfvSjbUKApCKOmfvUpdJrfSzUyuMTw",  # New LinkedIn profile link class
                                "a[data-test-app-aware-link]",
                                "a.app-aware-link",
                                "a.search-result__result-link",
                                "span.wdAwqyOwjonaSuRELGiCNMWxImNKWGw a"  # New selector for profile name link
                            ]
                            
                            for selector in link_selectors:
                                try:
                                    links = card.find_elements(By.CSS_SELECTOR, selector)
                                    for link in links:
                                        href = link.get_attribute("href")
                                        if href and "/in/" in href and not "search/results" in href:
                                            # Clean the URL to remove tracking parameters
                                            clean_url = href.split('?')[0]
                                            if clean_url not in unique_urls:
                                                unique_urls.add(clean_url)
                                                print(f"Found profile URL: {clean_url}")
                                except Exception as e:
                                    print(f"Error with link selector {selector}: {e}")
                                    continue
                        except Exception as e:
                            print(f"Error extracting profile URL: {e}")
                    
                    print(f"Found {len(unique_urls)} unique profile URLs so far")
                    
                    # Try to navigate to next page
                    try:
                        # Try multiple selectors for the next button
                        next_button = None
                        button_selectors = [
                            "button.artdeco-pagination__button--next",
                            "button.artdeco-pagination__button--next.ember-view",
                            "button[aria-label='Next']",
                            "button[aria-label='Next Page']",
                            "button.artdeco-pagination__button--next[aria-label='Next']"
                        ]
                        
                        for selector in button_selectors:
                            try:
                                next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                break
                            except:
                                continue
                        
                        if not next_button:
                            print("Next button not found. No more pages to scrape.")
                            break
                        
                        if next_button.get_attribute("disabled"):
                            print("Next button is disabled. No more pages to scrape.")
                            break
                        
                        next_button.click()
                        time.sleep(random.uniform(3, 5))
                        current_page += 1
                        
                    except Exception as e:
                        print(f"Error navigating to next page: {e}")
                        break
                
                # Save URLs to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                urls_file = os.path.join(self.output_dir, f'linkedin_profile_urls_{keyword.replace(" ", "_")}_{timestamp}.txt')
                with open(urls_file, 'w', encoding='utf-8') as f:
                    for url in unique_urls:
                        f.write(f"{url}\n")
                
                print(f"\nSaved {len(unique_urls)} profile URLs to {urls_file}")
                return urls_file
                
            except Exception as e:
                print(f"Error collecting profile URLs: {e}")
                return None
            
        except Exception as e:
            print(f"Error collecting profile URLs: {e}")
            return None
    
    def scrape_profile_details(self, profile_url):
        """Scrape details of a single profile"""
        try:
            print(f"Navigating to: {profile_url}")
            self.driver.get(profile_url)
            
            # Wait for page to load completely
            try:
                # Wait for either the login form or the profile content
                try:
                    self.wait.until(EC.presence_of_element_located((By.ID, "username")))
                    print("Login form detected. Attempting to login...")
                    self._login()
                except TimeoutException:
                    print("No login form detected, proceeding with scraping...")
                
                # Wait for profile content
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.profile-background-image")))
                time.sleep(random.uniform(2, 3))
                
                # Scroll to load all content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"Error loading page: {e}")
                return None
            
            profile_data = {
                'profile_url': profile_url,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Get name
            try:
                name_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "h1.MYDYEHKtjEkacpWodAYzOTrrbVonjEpJ"))
                )
                profile_data['name'] = name_element.text.strip()
            except:
                profile_data['name'] = "Not found"
            
            # Get headline
            try:
                headline_element = self.driver.find_element(By.CSS_SELECTOR, "div.text-body-medium")
                profile_data['headline'] = headline_element.text.strip()
            except:
                profile_data['headline'] = "Not found"
            
            # Get about section
            try:
                about_element = self.driver.find_element(By.CSS_SELECTOR, "div.display-flex.ph5.pv3")
                profile_data['about'] = about_element.text.strip()
            except:
                profile_data['about'] = "Not found"
            
            # Get experience
            try:
                # Find the experience section
                experience_section = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section.artdeco-card.pv-profile-card"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", experience_section)
                time.sleep(random.uniform(2, 3))
                
                # Find all experience items
                experience_items = self.driver.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item.wkrNTMpQfdFYIwmycbBWjUiRSpYBuzg")
                experiences = []
                
                for item in experience_items:
                    try:
                        # Get role
                        role_element = item.find_element(By.CSS_SELECTOR, "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold span")
                        role = role_element.text.strip()
                        
                        # Skip if role is empty or looks like a connection
                        if not role or any(keyword in role.lower() for keyword in ['followers', 'connections', 'connection']):
                            continue
                        
                        # Get company and job type
                        try:
                            company_info = item.find_element(By.CSS_SELECTOR, "span.t-14.t-normal span").text.strip()
                            company_parts = company_info.split("·")
                            company = company_parts[0].strip()
                            job_type = company_parts[1].strip() if len(company_parts) > 1 else "Not specified"
                        except:
                            company = "Not specified"
                            job_type = "Not specified"
                        
                        # Get duration
                        try:
                            duration_element = item.find_element(By.CSS_SELECTOR, "span.pvs-entity__caption-wrapper")
                            duration = duration_element.text.strip()
                        except:
                            duration = "Not specified"
                        
                        # Get location
                        try:
                            location_element = item.find_element(By.CSS_SELECTOR, "span.t-14.t-normal.t-black--light span")
                            location = location_element.text.strip()
                        except:
                            location = "Not specified"
                        
                        # Get summary
                        try:
                            summary_element = item.find_element(By.CSS_SELECTOR, "div.orheyVIPKSobbaJfzlhjeLPlhOJQzZY span")
                            summary = summary_element.text.strip()
                        except:
                            summary = "Not found"
                        
                        experiences.append({
                            'role': role,
                            'company': company,
                            'job_type': job_type,
                            'duration': duration,
                            'location': location,
                            'summary': summary
                        })
                    except Exception as e:
                        print(f"Error extracting experience: {e}")
                        continue
                
                profile_data['experience'] = experiences
            except Exception as e:
                print(f"Error extracting experience section: {e}")
                profile_data['experience'] = []
            
            # Get education
            try:
                # Find the education section
                education_section = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "section.artdeco-card.pv-profile-card"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", education_section)
                time.sleep(random.uniform(2, 3))
                
                # Find all education items
                education_items = self.driver.find_elements(By.CSS_SELECTOR, "li.artdeco-list__item.wkrNTMpQfdFYIwmycbBWjUiRSpYBuzg")
                education = []
                
                for item in education_items:
                    try:
                        # Get school name
                        school_element = item.find_element(By.CSS_SELECTOR, "div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold span")
                        school = school_element.text.strip()
                        
                        # Skip if school name is empty or looks like a connection
                        if not school or any(keyword in school.lower() for keyword in ['followers', 'connections', 'connection']):
                            continue
                        
                        # Get degree and field of study
                        try:
                            degree_element = item.find_element(By.CSS_SELECTOR, "span.t-14.t-normal span")
                            degree_info = degree_element.text.strip()
                            degree_parts = degree_info.split(", ")
                            degree = degree_parts[0].strip()
                            field_of_study = degree_parts[1].strip() if len(degree_parts) > 1 else "Not specified"
                        except:
                            degree = "Not specified"
                            field_of_study = "Not specified"
                        
                        education.append({
                            'school': school,
                            'degree': degree,
                            'field_of_study': field_of_study
                        })
                    except Exception as e:
                        print(f"Error extracting education: {e}")
                        continue
                
                profile_data['education'] = education
            except Exception as e:
                print(f"Error extracting education section: {e}")
                profile_data['education'] = []
            
            return profile_data
            
        except Exception as e:
            print(f"Error scraping profile details: {e}")
            return None
    
    def scrape_profiles_from_urls(self, urls_file):
        """Scrape profile details from a file containing URLs"""
        try:
            # Read URLs from file
            with open(urls_file, 'r', encoding='utf-8') as f:
                profile_urls = [line.strip() for line in f if line.strip()]
            
            print(f"Starting to scrape details for {len(profile_urls)} profiles...")
            
            for i, url in enumerate(profile_urls, 1):
                try:
                    print(f"Scraping profile {i}/{len(profile_urls)}: {url}")
                    profile_data = self.scrape_profile_details(url)
                    if profile_data:
                        self.profiles.append(profile_data)
                        print(f"Successfully scraped: {profile_data['name']}")
                    
                    # Add delay between profiles
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"Error scraping profile {url}: {e}")
                    continue
            
            # Save the data
            self._save_data()
            return True
            
        except Exception as e:
            print(f"Error during profile details scraping: {e}")
            return False
    
    def _save_data(self):
        """Save scraped data to JSON and CSV files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to JSON
            json_file = os.path.join(self.output_dir, f'linkedin_profiles_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(self.profiles)} profiles to JSON: {json_file}")
            
            # Save to CSV
            csv_file = os.path.join(self.output_dir, f'linkedin_profiles_{timestamp}.csv')
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    'Name', 'Headline', 'About', 'Experience', 'Education', 'Profile URL', 'Scraped At'
                ])
                # Write data rows
                for profile in self.profiles:
                    writer.writerow([
                        profile.get('name', ''),
                        profile.get('headline', ''),
                        profile.get('about', ''),
                        str(profile.get('experience', [])),
                        str(profile.get('education', [])),
                        profile.get('profile_url', ''),
                        profile.get('scraped_at', '')
                    ])
            print(f"Saved {len(self.profiles)} profiles to CSV: {csv_file}")
            
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='LinkedIn Profile Scraper')
    parser.add_argument('--keyword', help='Search keyword (e.g., "Interior Designers", "Data Scientists")')
    parser.add_argument('--max-pages', type=int, default=10, help='Maximum number of pages to scrape')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--collect-urls', action='store_true', help='Only collect profile URLs')
    parser.add_argument('--urls-file', help='File containing profile URLs to scrape')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.urls_file and not args.keyword:
        parser.error("Either --keyword or --urls-file must be provided")
    if args.collect_urls and not args.keyword:
        parser.error("--keyword is required when using --collect-urls")
    
    scraper = LinkedInProfileScraper(headless=args.headless)
    
    try:
        if args.collect_urls:
            print(f"Starting to collect profile URLs for keyword: {args.keyword}")
            urls_file = scraper.collect_profile_urls(
                args.keyword,
                max_pages=args.max_pages
            )
            if urls_file:
                print(f"Profile URLs saved to: {urls_file}")
                print(f"\nTo scrape profile details, run:")
                print(f"python linkedin_profile_scraper.py --urls-file {urls_file}")
        elif args.urls_file:
            print(f"Starting to scrape profile details from: {args.urls_file}")
            success = scraper.scrape_profiles_from_urls(args.urls_file)
            if success:
                print(f"Successfully scraped {len(scraper.profiles)} profiles")
            else:
                print("Failed to scrape profiles")
        else:
            print("Please specify either --collect-urls or --urls-file")
    finally:
        scraper.close() 