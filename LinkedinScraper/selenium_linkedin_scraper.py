import json
import os
import time
import csv
import random
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementNotInteractableException, WebDriverException
import sys
import psutil

class LinkedInSeleniumScraper:
    def __init__(self, headless=False, use_profile=False, profile_path=None):
        self.output_dir = 'output'
        self.cookies_file = os.path.join(self.output_dir, 'linkedin_cookies.json')
        self.profiles = []
        self.experiences = []
        self.education = []
        self.skills = []
        self.contact_info = []
        self.open_to_work_profiles = []
        self.salesql_enabled = False
        
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
    
    def _load_cookies(self):
        """Load cookies from the cookies file"""
        try:
            # First go to LinkedIn so we can set cookies
            self.driver.get("https://www.linkedin.com")
            time.sleep(3)
            
            # Load cookies
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                for cookie in cookies:
                    # Some cookies can cause issues, skip them
                    if 'expiry' in cookie:
                        del cookie['expiry']
                    
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Error adding cookie: {e}")
            else:
                print(f"Warning: Cookies file not found: {self.cookies_file}")
        except Exception as e:
            print(f"Error loading cookies: {e}")
    
    def login(self):
        """Log in to LinkedIn with email and password"""
        try:
            # Replace with your LinkedIn credentials
            email = "example@gmail.com"
            password = "password@1234"
            
            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(2)
            
            # Check if cookies exist and try loading them first
            if os.path.exists(self.cookies_file):
                print("Attempting to log in with cookies...")
                self._load_cookies()
                self.driver.get("https://www.linkedin.com/feed/")
                time.sleep(5)
                
                # Check if login was successful
                if "feed" in self.driver.current_url:
                    print("Successfully logged in with cookies")
                    return True
                else:
                    print("Login with cookies failed, trying with credentials...")
            
            # Fill in email and password
            self.driver.find_element(By.ID, "username").send_keys(email)
            self.driver.find_element(By.ID, "password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Verify login was successful
            if "feed" in self.driver.current_url:
                print("Login successful")
                
                # Save cookies for future use
                with open(self.cookies_file, 'w') as f:
                    json.dump(self.driver.get_cookies(), f)
                
                print(f"Cookies saved to {self.cookies_file}")
                return True
            else:
                print("Login failed, check credentials or possible CAPTCHA")
                return False
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def search_profiles(self, search_term, max_profiles=10):
        """Search for profiles based on search term and automatically handle pagination"""
        try:
            print(f"Searching for profiles matching: {search_term}")
            
            # Navigate to LinkedIn search page
            self.driver.get("https://www.linkedin.com/search/results/people/")
            time.sleep(2)
            
            # Find and fill the search input field
            search_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.search-global-typeahead__input")))
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for search results to load
            time.sleep(5)
            
            profile_count = 0
            current_page = 1
            
            while profile_count < max_profiles:
                print(f"\nScanning page {current_page} for profiles...")
                
                # Extended wait for profile cards to load
                time.sleep(3)
                
                # Get page source for debugging
                page_source = self.driver.page_source
                if "No results found" in page_source:
                    print("LinkedIn reports no results found for this search.")
                    break
                
                # Try multiple selectors to find profile cards
                profile_cards = []
                selectors_to_try = [
                    ".entity-result__item",
                    ".reusable-search__result-container",
                    "li.reusable-search__result-container",
                    "li.search-result",
                    "li.search-entity",
                    "div[data-test-search-result]",
                    "li[data-test-search-result]",
                    "div.search-result",
                    "div.search-entity",
                    "li.artdeco-list__item"
                ]
                
                for selector in selectors_to_try:
                    try:
                        profile_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if profile_cards:
                            print(f"Found {len(profile_cards)} profiles using selector: {selector}")
                            break
                    except:
                        continue
                
                if not profile_cards:
                    print("Could not find profile cards with any known selectors.")
                    print("Trying XPath selectors for profile cards...")
                    
                    # Try different XPath expressions
                    xpath_selectors = [
                        "//li[contains(@class, 'reusable-search__result-container')]",
                        "//li[contains(@class, 'search-result')]",
                        "//div[contains(@class, 'search-result')]",
                        "//a[contains(@href, '/in/')]/..",
                        "//li[.//a[contains(@href, '/in/')]]",
                        "//div[.//a[contains(@href, '/in/')]]"
                    ]
                    
                    for xpath in xpath_selectors:
                        try:
                            profile_cards = self.driver.find_elements(By.XPATH, xpath)
                            if profile_cards:
                                print(f"Found {len(profile_cards)} profiles using XPath: {xpath}")
                                break
                        except Exception as e:
                            continue
                
                # Final attempt: look directly for profile links
                if not profile_cards:
                    print("Attempting to find profile links directly...")
                    try:
                        profile_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
                        
                        # Deduplicate links
                        unique_urls = set()
                        for link in profile_links:
                            try:
                                url = link.get_attribute("href")
                                if "/in/" in url and "linkedin.com" in url:
                                    unique_urls.add(url)
                            except:
                                continue
                        
                        if unique_urls:
                            print(f"Found {len(unique_urls)} direct profile links")
                            
                            for url in unique_urls:
                                if profile_count >= max_profiles:
                                    break
                                
                                profile_id_match = re.search(r'/in/([^/?]+)', url)
                                if not profile_id_match:
                                    continue
                                
                                profile_id = profile_id_match.group(1)
                                
                                # Basic profile info
                                profile_data = {
                                    "profile_id": profile_id,
                                    "name": f"Profile {profile_id}",
                                    "headline": "See detailed profile",
                                    "location": "Location pending",
                                    "profile_url": url,
                                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                
                                self.profiles.append(profile_data)
                                profile_count += 1
                                print(f"Added profile: {url}")
                            
                            if profile_count > 0:
                                break  # Exit the page scanning loop if we found profiles
                    except Exception as e:
                        print(f"Error finding direct links: {e}")
                
                print(f"Found {len(profile_cards)} profiles on this page")
                
                # Process each profile card
                for card in profile_cards:
                    if profile_count >= max_profiles:
                        break
                    
                    try:
                        # Try to extract profile link
                        link_element = None
                        profile_url = None
                        
                        # Try different selectors for profile links
                        link_selectors = [
                            "a.app-aware-link",
                            "a[data-control-name='search_srp_result']",
                            "a[href*='/in/']",
                            "a.search-result__result-link",
                            "a.artdeco-entity-lockup__link",
                            "a"
                        ]
                        
                        for selector in link_selectors:
                            try:
                                link_elements = card.find_elements(By.CSS_SELECTOR, selector)
                                for element in link_elements:
                                    href = element.get_attribute("href")
                                    if href and "/in/" in href:
                                        link_element = element
                                        profile_url = href
                                        break
                                if link_element:
                                    break
                            except:
                                continue
                        
                        if not link_element and not profile_url:
                            # Try with XPath as last resort
                            try:
                                link_element = card.find_element(By.XPATH, ".//a[contains(@href, '/in/')]")
                                profile_url = link_element.get_attribute("href")
                            except:
                                continue
                        
                        # Ensure we have a valid LinkedIn profile URL
                        if not profile_url or "/in/" not in profile_url:
                            continue
                        
                        # Extract the profile ID from the URL
                        profile_id_match = re.search(r'/in/([^/?]+)', profile_url)
                        if not profile_id_match:
                            continue
                        
                        profile_id = profile_id_match.group(1)
                        
                        # Try to get name
                        name = f"Profile {profile_id}"
                        try:
                            # Try multiple selectors for name
                            name_selectors = [
                                ".entity-result__title-text",
                                ".app-aware-link span[aria-hidden='true']",
                                ".actor-name",
                                ".search-result__title",
                                ".artdeco-entity-lockup__title"
                            ]
                            
                            for selector in name_selectors:
                                try:
                                    name_element = card.find_element(By.CSS_SELECTOR, selector)
                                    name_text = name_element.text.strip()
                                    if name_text:
                                        name = name_text
                                        break
                                except:
                                    continue
                                    
                            if name == f"Profile {profile_id}":
                                # Try with XPath
                                name_elements = card.find_elements(By.XPATH, ".//span[contains(@class, 'name') or contains(@class, 'title')]")
                                for element in name_elements:
                                    name_text = element.text.strip()
                                    if name_text and len(name_text) < 40:  # Avoid getting long text
                                        name = name_text
                                        break
                        except:
                            pass
                        
                        # Try to get headline/title
                        headline = "Not available"
                        try:
                            # Try multiple selectors for headline
                            headline_selectors = [
                                ".entity-result__primary-subtitle",
                                ".entity-result__description",
                                ".search-result__subtitle",
                                ".artdeco-entity-lockup__subtitle"
                            ]
                            
                            for selector in headline_selectors:
                                try:
                                    headline_element = card.find_element(By.CSS_SELECTOR, selector)
                                    headline_text = headline_element.text.strip()
                                    if headline_text:
                                        headline = headline_text
                                        break
                                except:
                                    continue
                        except:
                            pass
                        
                        # Try to get location
                        location = "Not available"
                        try:
                            # Try multiple selectors for location
                            location_selectors = [
                                ".entity-result__secondary-subtitle",
                                ".search-result__location",
                                ".artdeco-entity-lockup__caption"
                            ]
                            
                            for selector in location_selectors:
                                try:
                                    location_element = card.find_element(By.CSS_SELECTOR, selector)
                                    location_text = location_element.text.strip()
                                    if location_text:
                                        location = location_text
                                        break
                                except:
                                    continue
                        except:
                            pass
                        
                        # Print and store profile information
                        print(f"Found profile: {name} - {headline} ({profile_url})")
                        
                        # Collect profile data
                        profile_data = {
                            "profile_id": profile_id,
                            "name": name,
                            "headline": headline,
                            "location": location,
                            "profile_url": profile_url,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        self.profiles.append(profile_data)
                        profile_count += 1
                        
                        # Add a random delay between processing profiles to avoid detection
                        time.sleep(random.uniform(1, 3))
                        
                    except Exception as e:
                        print(f"Error extracting profile data: {e}")
                        continue
                
                # If we need more profiles, click the "Next" button to go to the next page
                if profile_count < max_profiles and profile_cards:
                    try:
                        # Try to find the Next button
                        next_button = self.driver.find_element(By.CSS_SELECTOR, "button.artdeco-pagination__button--next")
                        
                        # Check if the next button is disabled
                        if next_button.get_attribute("disabled"):
                            print("Reached the last page of results")
                            break
                        
                        # Scroll to the button to make it visible
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                        time.sleep(1)
                        
                        # Click the next button
                        next_button.click()
                        
                        # Wait for the next page to load
                        time.sleep(5)
                        page += 1
                        
                    except NoSuchElementException:
                        print("No 'Next' button found. This may be the last page.")
                        break
                    except Exception as e:
                        print(f"Error navigating to next page: {e}")
                        break
                else:
                    break  # Either we have enough profiles or no profiles were found
            
            print(f"Successfully collected data for {len(self.profiles)} profiles")
            return True
            
        except Exception as e:
            print(f"Error during profile search: {e}")
            return False
    
    def _check_open_to_work(self, profile):
        """Check if a profile has the 'Open to Work' status"""
        try:
            print("Checking if profile is open to work...")
            is_open_to_work = False
            open_to_work_details = None
            
            # Multiple methods to detect "Open to Work"
            
            # Method 1: Check the profile image title for "#OPEN_TO_WORK"
            try:
                profile_img = self.driver.find_element(By.XPATH, "//img[contains(@class, 'pv-top-card-profile-picture__image') or contains(@alt, '#OPEN_TO_WORK')]")
                img_title = profile_img.get_attribute('title') or profile_img.get_attribute('alt') or ''
                
                if '#OPEN_TO_WORK' in img_title:
                    print("Detected 'Open to Work' from profile image")
                    is_open_to_work = True
                    open_to_work_details = "Indicated in profile picture"
            except Exception as e:
                print(f"Could not check profile image for 'Open to Work': {e}")
            
            # Method 2: Check for the open-to-work section/banner
            if not is_open_to_work:
                try:
                    open_to_work_element = self.driver.find_element(By.XPATH, 
                        "//div[contains(@class, 'open-to-work') or contains(@class, 'pv-open-to-work')]")
                    
                    if open_to_work_element:
                        print("Found 'Open to Work' banner/section")
                        is_open_to_work = True
                        
                        # Try to get more details about the open to work status
                        try:
                            details_element = open_to_work_element.find_element(By.XPATH, ".//span")
                            open_to_work_details = details_element.text.strip()
                        except:
                            open_to_work_details = "Open to Work (no details available)"
                except Exception as e:
                    print(f"Could not find 'Open to Work' section: {e}")
            
            # Method 3: Check for text indicators in the page
            if not is_open_to_work:
                try:
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text
                    open_to_work_phrases = [
                        "#OPENTOWORK", 
                        "#OPEN_TO_WORK", 
                        "OPEN TO WORK",
                        "Open to job opportunities"
                    ]
                    
                    for phrase in open_to_work_phrases:
                        if phrase in body_text:
                            print(f"Found 'Open to Work' text indicator: {phrase}")
                            is_open_to_work = True
                            open_to_work_details = f"Indicated by text: {phrase}"
                            break
                except Exception as e:
                    print(f"Could not check page text for 'Open to Work' indicators: {e}")
            
            # Update the profile with open to work status
            profile['is_open_to_work'] = is_open_to_work
            if is_open_to_work:
                profile['open_to_work_details'] = open_to_work_details
                # Add timestamp when the profile was detected as open to work
                profile['open_to_work_detected_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Create a copy of the profile for the open_to_work list
                open_to_work_profile = dict(profile)
                self.open_to_work_profiles.append(open_to_work_profile)
                print(f"Added profile to 'Open to Work' list: {profile.get('name', 'Unknown')}")
                
                # Save open to work profiles immediately
                self._save_open_to_work_profiles()
            
            return is_open_to_work
            
        except Exception as e:
            print(f"Error checking for 'Open to Work' status: {e}")
            profile['is_open_to_work'] = False
            return False
    
    def _save_open_to_work_profiles(self):
        """Save profiles that are open to work to a separate JSON file"""
        try:
            if self.open_to_work_profiles:
                open_to_work_file = os.path.join(self.output_dir, 'open_to_work_profiles.json')
                
                with open(open_to_work_file, 'w', encoding='utf-8') as f:
                    json.dump(self.open_to_work_profiles, f, indent=2, ensure_ascii=False)
                
                print(f"Saved {len(self.open_to_work_profiles)} 'Open to Work' profiles to {open_to_work_file}")
            else:
                print("No 'Open to Work' profiles to save")
        except Exception as e:
            print(f"Error saving 'Open to Work' profiles: {e}")
    
    def _extract_salesql_emails(self, profile):
        """Extract email addresses using SalesQL extension"""
        try:
            if not self.salesql_enabled:
                print("SalesQL extension not enabled, skipping SalesQL email extraction")
                return False
                
            print("Attempting to extract emails using SalesQL extension...")
            
            # Wait for SalesQL to initialize and scan the profile
            time.sleep(5)  # Allow SalesQL time to scan the profile
            
            # Look for SalesQL button/icon and click it if needed
            try:
                # Try different selectors for SalesQL button
                salesql_button_selectors = [
                    "//button[contains(@class, 'salesql')]",
                    "//div[contains(@class, 'salesql')]",
                    "//button[contains(@title, 'SalesQL')]",
                    "//div[contains(@id, 'salesql')]",
                    "//div[contains(@class, 'sql-')]//button",
                    "//div[contains(@class, '_2uhMtp0sIVUqJ-73kplv')]"
                ]
                
                for selector in salesql_button_selectors:
                    try:
                        salesql_buttons = self.driver.find_elements(By.XPATH, selector)
                        if salesql_buttons:
                            print(f"Found {len(salesql_buttons)} SalesQL elements with selector: {selector}")
                            for button in salesql_buttons:
                                if button.is_displayed():
                                    print("Clicking SalesQL button to reveal emails")
                                    self.driver.execute_script("arguments[0].click();", button)
                                    time.sleep(2)  # Wait for emails to be revealed
                                    break
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error clicking SalesQL button: {e}")
            
            # Now try to extract emails from SalesQL elements
            emails_data = []
            try:
                # Based on the HTML example, find all contact-value elements
                email_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'contact-value')]")
                print(f"Found {len(email_elements)} potential email elements")
                
                for element in email_elements:
                    try:
                        # Extract the email address
                        email_div = element.find_element(By.XPATH, ".//div[contains(@class, 'value')]")
                        email = email_div.text.strip()
                        
                        # Check if it's a valid email format
                        if "@" not in email or "." not in email:
                            continue
                            
                        # Check if it's verified
                        is_verified = False
                        try:
                            verified_icon = element.find_element(By.XPATH, ".//i[contains(@class, 'verified')]")
                            if verified_icon:
                                is_verified = True
                        except:
                            pass
                            
                        # Determine email type (Work/Direct)
                        email_type = "Unknown"
                        try:
                            tag_div = element.find_element(By.XPATH, ".//div[contains(@class, 'tag')]//span")
                            email_type = tag_div.text.strip()
                        except:
                            pass
                            
                        # Store all the email data
                        email_data = {
                            "email": email,
                            "type": email_type,
                            "verified": is_verified,
                            "source": "SalesQL"
                        }
                        emails_data.append(email_data)
                        print(f"Found email: {email} ({email_type})")
                        
                    except Exception as e:
                        print(f"Error extracting email from element: {e}")
                
            except Exception as e:
                print(f"Error extracting emails from SalesQL elements: {e}")
            
            # Prioritize Direct emails over Work emails
            direct_emails = [e for e in emails_data if e.get("type", "").lower() == "direct"]
            verified_emails = [e for e in emails_data if e.get("verified", False)]
            
            # Update profile with email information
            if not profile.get('emails'):
                profile['emails'] = []
                
            # Add all extracted emails to the profile
            for email_data in emails_data:
                profile['emails'].append(email_data)
            
            # Update contact_info with the best email (Direct and Verified preferred)
            if 'contact_info' not in profile:
                profile['contact_info'] = {}
                
            if direct_emails and verified_emails:
                # Find emails that are both direct and verified
                best_emails = [e for e in direct_emails if e.get("verified", False)]
                
                if best_emails:
                    profile['contact_info']['email'] = best_emails[0]['email']
                    profile['contact_info']['email_details'] = best_emails[0]
                elif direct_emails:
                    profile['contact_info']['email'] = direct_emails[0]['email']
                    profile['contact_info']['email_details'] = direct_emails[0]
                elif verified_emails:
                    profile['contact_info']['email'] = verified_emails[0]['email']
                    profile['contact_info']['email_details'] = verified_emails[0]
                elif emails_data:
                    profile['contact_info']['email'] = emails_data[0]['email']
                    profile['contact_info']['email_details'] = emails_data[0]
            
            return len(emails_data) > 0
            
        except Exception as e:
            print(f"Error extracting emails with SalesQL: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _extract_contact_info(self, profile):
        """Extract contact information from the profile's contact info overlay"""
        try:
            print("Attempting to extract contact information...")
            # If we don't have contact_info in the profile yet, initialize it
            if 'contact_info' not in profile:
                profile['contact_info'] = {}
                
            # Set up basic contact info structure    
            contact_data = {
                'profile_id': profile.get('profile_id', ''),
                'name': profile.get('name', 'Unknown'),
                'linkedin_url': profile.get('profile_url', ''),
                'email': None,
                'phone': None,
                'websites': [],
                'connected_date': None,
                'twitter': None,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # First try to extract emails using SalesQL extension
            salesql_success = self._extract_salesql_emails(profile)
            
            # If SalesQL found emails, we may already have the email in the contact_info
            if salesql_success and profile.get('contact_info', {}).get('email'):
                contact_data['email'] = profile['contact_info']['email']
                
            # Continue with normal LinkedIn contact info extraction
            try:
                # Look for the contact info link using various selectors
                contact_link_selectors = [
                    "//a[@id='top-card-text-details-contact-info']",
                    "//a[contains(@href, '/overlay/contact-info/')]",
                    "//a[contains(text(), 'Contact info')]",
                    "//button[contains(@aria-label, 'Contact info')]",
                    "//button[contains(@class, 'contact-info')]"
                ]
                
                contact_link = None
                for selector in contact_link_selectors:
                    try:
                        contact_link = self.driver.find_element(By.XPATH, selector)
                        print(f"Found contact info link using selector: {selector}")
                        break
                    except:
                        continue
                
                if not contact_link:
                    print("Could not find contact info link")
                    # Save the contact data even without additional info
                    self.contact_info.append(contact_data)
                    profile['contact_info'] = contact_data
                    return
                
                # Click the contact link to open the overlay
                try:
                    self.driver.execute_script("arguments[0].click();", contact_link)
                    print("Clicked on contact info link")
                    time.sleep(2)
                except:
                    try:
                        contact_link.click()
                        time.sleep(2)
                    except:
                        print("Could not click contact info link")
                        return
                
                # Try to locate the contact info modal
                try:
                    modal_content = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'artdeco-modal__content')]"))
                    )
                    print("Found contact info modal")
                except:
                    print("Could not find contact info modal")
                    modal_content = self.driver
                
                # Extract LinkedIn profile URL
                try:
                    linkedin_section = modal_content.find_element(By.XPATH, ".//section[.//h3[contains(text(), \"'s Profile\")]]")
                    linkedin_link = linkedin_section.find_element(By.XPATH, ".//a")
                    contact_data['linkedin_url'] = linkedin_link.text.strip()
                    print(f"Found LinkedIn URL: {contact_data['linkedin_url']}")
                except Exception as e:
                    print(f"Could not find LinkedIn URL section: {e}")
                
                # Extract websites
                try:
                    website_section = modal_content.find_element(By.XPATH, ".//section[.//h3[contains(text(), 'Website')]]")
                    website_links = website_section.find_elements(By.XPATH, ".//a")
                    
                    for link in website_links:
                        website_data = {
                            'url': link.get_attribute('href'),
                            'text': link.text.strip()
                        }
                        # Try to get website type if available
                        try:
                            type_span = link.find_element(By.XPATH, "./following-sibling::span")
                            if type_span:
                                website_data['type'] = type_span.text.strip().replace('(', '').replace(')', '')
                        except:
                            pass
                        
                        contact_data['websites'].append(website_data)
                    
                    print(f"Found {len(contact_data['websites'])} websites")
                except Exception as e:
                    print(f"Could not find website section: {e}")
                
                # Extract email address (if not already found with SalesQL)
                if not contact_data['email']:
                    try:
                        email_section = modal_content.find_element(By.XPATH, ".//section[.//h3[contains(text(), 'Email')]]")
                        email_link = email_section.find_element(By.XPATH, ".//a")
                        contact_data['email'] = email_link.text.strip()
                        print(f"Found email: {contact_data['email']}")
                    except Exception as e:
                        print(f"Could not find email section: {e}")
                
                # Extract phone number
                try:
                    phone_section = modal_content.find_element(By.XPATH, ".//section[.//h3[contains(text(), 'Phone')]]")
                    phone_span = phone_section.find_element(By.XPATH, ".//span[contains(@class, 't-14')]")
                    contact_data['phone'] = phone_span.text.strip()
                    print(f"Found phone: {contact_data['phone']}")
                except Exception as e:
                    print(f"Could not find phone section: {e}")
                
                # Extract Twitter handle
                try:
                    twitter_section = modal_content.find_element(By.XPATH, ".//section[.//h3[contains(text(), 'Twitter')]]")
                    twitter_link = twitter_section.find_element(By.XPATH, ".//a")
                    contact_data['twitter'] = twitter_link.text.strip()
                    print(f"Found Twitter: {contact_data['twitter']}")
                except Exception as e:
                    print(f"Could not find Twitter section: {e}")
                
                # Extract connected date
                try:
                    connected_section = modal_content.find_element(By.XPATH, ".//section[.//h3[contains(text(), 'Connected')]]")
                    connected_span = connected_section.find_element(By.XPATH, ".//span[contains(@class, 't-14')]")
                    contact_data['connected_date'] = connected_span.text.strip()
                    print(f"Found connected date: {contact_data['connected_date']}")
                except Exception as e:
                    print(f"Could not find connected date section: {e}")
                
                # Try to close the modal
                try:
                    close_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'artdeco-modal__dismiss')]")
                    close_button.click()
                    time.sleep(1)
                except:
                    print("Could not find close button for modal")
                    # Try clicking escape key to close the modal
                    try:
                        from selenium.webdriver.common.keys import Keys
                        webdriver.ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(1)
                    except:
                        print("Could not close modal with escape key")
            
            except Exception as e:
                print(f"Error accessing contact info: {e}")
            
            # Merge the contact data with any existing contact info from SalesQL
            merged_contact_data = dict(contact_data)
            
            # If we already have contact_info from SalesQL, prioritize SalesQL email
            if 'contact_info' in profile and profile['contact_info'].get('email'):
                merged_contact_data['email'] = profile['contact_info'].get('email')
                if 'email_details' in profile['contact_info']:
                    merged_contact_data['email_details'] = profile['contact_info']['email_details']
            
            # Add the merged contact data to list and profile
            self.contact_info.append(merged_contact_data)
            profile['contact_info'] = merged_contact_data
            
        except Exception as e:
            print(f"Error extracting contact info: {e}")
            import traceback
            traceback.print_exc()

    def scrape_profile(self, profile_url):
        """Scrape a single LinkedIn profile"""
        print(f"Scraping profile: {profile_url}")
        try:
            # Random delay before accessing profile (to appear more human-like)
            time.sleep(random.uniform(3, 7))
            
            self.driver.get(profile_url)
            
            # Wait for profile to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract profile ID for saving data
            profile_id = profile_url.split('/in/')[-1].split('?')[0]
            
            # Scroll down slowly to load all sections
            self._scroll_profile_page()
            
            # Extract basic profile data
            profile_data = {}
            profile_data['profile_id'] = profile_id
            profile_data['profile_url'] = profile_url
            
            # Extract name
            try:
                name_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//h1"))
                )
                profile_data['name'] = name_element.text.strip()
            except:
                profile_data['name'] = "Name not found"
                print(f"Could not find name for profile {profile_url}")
            
            # Get headline/title
            try:
                headline = self.driver.find_element(By.XPATH, "//div[contains(@class, 'pv-text-details__left-panel')]/div").text.strip()
                profile_data['headline'] = headline
            except:
                try:
                    headline = self.driver.find_element(By.XPATH, "//div[contains(@class, 'text-body-medium')]").text.strip()
                    profile_data['headline'] = headline
                except:
                    profile_data['headline'] = "Headline not found"
            
            # Get location
            try:
                location = self.driver.find_element(By.XPATH, "//span[contains(@class, 'text-body-small') and contains(@class, 'inline')]").text.strip()
                profile_data['location'] = location
            except:
                profile_data['location'] = "Location not found"
            
            # Extract About section
            self._extract_about(profile_data)
            
            # Get number of connections
            try:
                conn_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'distance-badge') or contains(@class, 'connection-info')]")
                profile_data['connections'] = conn_element.text.strip()
            except:
                profile_data['connections'] = "Unknown"
            
            # Check if profile is open to work
            self._check_open_to_work(profile_data)
            
            # Add timestamp
            profile_data['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Extract contact information (now includes SalesQL extraction)
            self._extract_contact_info(profile_data)
            
            # Extract experience data 
            self._extract_experience(profile_data)
            
            # Extract education data
            self._extract_education(profile_data)
            
            # Extract skills data
            self._extract_skills(profile_data)
            
            # Save the data as we go
            self._save_data()
            
            return profile_data
             
        except Exception as e:
            print(f"Error scraping profile {profile_url}: {e}")
            return {
                'profile_id': profile_url.split('/in/')[-1].split('?')[0],
                'profile_url': profile_url,
                'name': "Error extracting profile",
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def _scroll_profile_page(self):
        """Scroll down the profile page to load all dynamic content"""
        try:
            print("Scrolling page to load all content...")
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down incrementally with realistic pauses
            for i in range(10):  # Increased from 5 to 10 for more thorough scrolling
                # Scroll down with human-like behavior (variable scroll amount)
                scroll_amount = random.randint(300, 800)  # More random scroll behavior
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                
                # Random pause (more human-like)
                time.sleep(random.uniform(0.5, 2.0))
                
                # Sometimes simulate a small scroll up (like a human reading)
                if random.random() > 0.7:  # 30% chance
                    self.driver.execute_script("window.scrollBy(0, -100);")
                    time.sleep(random.uniform(0.3, 0.7))
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                print(f"Scroll iteration {i+1}/10: height {last_height} -> {new_height}")
                
                if new_height == last_height:
                    print("Page fully loaded, no more content to scroll.")
                    break
                last_height = new_height
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            print("Page scrolling complete")
            
        except Exception as e:
            print(f"Error during profile scrolling: {e}")
    
    def _extract_about(self, profile):
        """Extract the About section using specific HTML selectors"""
        try:
            print("Attempting to extract About section...")
            
            about_text = None
            # Try finding the about section using the new HTML structure
            try:
                # Look for the element with ID "about"
                about_div = self.driver.find_element(By.ID, "about")
                # Navigate to the parent section
                about_section = about_div.find_element(By.XPATH, "./ancestor::section")
                
                # Find the about text in the inline-show-more-text element
                about_text_element = about_section.find_element(
                    By.XPATH, 
                    ".//div[contains(@class, 'inline-show-more-text')]"
                )
                
                about_text = about_text_element.text.strip()
                print(f"Found About section text: {about_text[:100]}...")
                
            except Exception as e:
                print(f"Failed to find About using new structure: {e}")
                
                # Fall back to older methods
                try:
                    # Try with alternate selectors
                    selectors = [
                        "//section[@id='about']//div[contains(@class, 'inline-show-more-text')]",
                        "//div[@id='about']//div[contains(@class, 'inline-show-more-text')]",
                        "//section[.//div[contains(text(), 'About')]]//div[contains(@class, 'display-flex')]",
                        "//section[contains(@class, 'summary')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            about_element = self.driver.find_element(By.XPATH, selector)
                            about_text = about_element.text.strip()
                            if about_text:
                                break
                        except:
                            continue
                
                except Exception as e:
                    print(f"Error finding About section with alternate selectors: {e}")
            
            # Update the profile with about text if found
            if about_text:
                profile['about'] = about_text
            else:
                profile['about'] = "About section not found"
                
        except Exception as e:
            print(f"Error extracting About section: {e}")
            profile['about'] = "Error extracting About section"

    def _extract_experience(self, profile):
        """Extract experience items from profile using specific HTML selectors"""
        try:
            print("Attempting to extract experience data...")
            
            # Try to find the experience section using multiple selectors
            experience_section = None
            
            # First try by ID (most reliable)
            try:
                # Find div with id="experience" and get parent section
                experience_div = self.driver.find_element(By.ID, "experience")
                experience_section = experience_div.find_element(By.XPATH, "./ancestor::section")
                print("Found experience section by ID")
            except Exception as e:
                print(f"Could not find experience section by ID: {e}")
                
                # Try direct section with experience header
                try:
                    experience_section = self.driver.find_element(
                        By.XPATH, 
                        "//section[.//h2[contains(text(), 'Experience')]]"
                    )
                    print("Found experience section by header text")
                except Exception as e:
                    print(f"Could not find experience section by header: {e}")
                    
                    # Try other selectors as fallback
                    selectors_to_try = [
                        "//section[.//div[contains(text(), 'Experience')]]",
                        "//section[contains(@class, 'experience-section')]",
                        "//div[contains(@id, 'experience')]/ancestor::section",
                        "//section[contains(@id, 'experience')]",
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            experience_section = self.driver.find_element(By.XPATH, selector)
                            if experience_section:
                                print(f"Found experience section using selector: {selector}")
                                break
                        except:
                            continue
            
            if not experience_section:
                print("Could not find experience section with any selector")
                with open(f"{self.output_dir}/experience_not_found.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                profile['experiences'] = []
                return
            
            # Scroll to make section visible
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", experience_section)
            time.sleep(2)
            
            # Extract experience list items using the specific HTML structure
            # First try the specific class from the example
            experience_items = []
            try:
                experience_items = experience_section.find_elements(
                    By.XPATH, 
                    ".//li[contains(@class, 'artdeco-list__item')]"
                )
                print(f"Found {len(experience_items)} experience items with artdeco-list__item class")
            except Exception as e:
                print(f"Could not find experience items with artdeco-list__item class: {e}")
                # Try alternate selectors
                try:
                    experience_items = experience_section.find_elements(By.XPATH, ".//li")
                    print(f"Found {len(experience_items)} experience items with li tag")
                except:
                    print("Could not find any experience items")
            
            if not experience_items:
                print("No experience items found")
                profile['experiences'] = []
                return
            
            profile_experiences = []
            
            for idx, item in enumerate(experience_items):
                try:
                    experience = {
                        'profile_id': profile.get('profile_id', ''),
                        'role': None,
                        'company': None,
                        'start_date': None,
                        'end_date': None,
                        'duration': None,
                        'location': None,
                        'description': None
                    }
                    
                    # Extract role - look for the specific class in the HTML example
                    try:
                        role_element = item.find_element(
                            By.XPATH, 
                            ".//div[contains(@class, 'mr1') and contains(@class, 't-bold')]"
                        )
                        experience['role'] = role_element.text.strip()
                        print(f"Found role: {experience['role']}")
                    except Exception as e:
                        print(f"Could not find role with primary selector: {e}")
                        # Try alternate selectors
                        try:
                            role_element = item.find_element(By.XPATH, ".//span[contains(@class, 't-bold')]")
                            experience['role'] = role_element.text.strip()
                        except:
                            # Try more generic element containing the role
                            try:
                                role_element = item.find_element(By.XPATH, ".//h3")
                                experience['role'] = role_element.text.strip()
                            except:
                                print("Could not find role with any selector")
                                continue  # Skip if no role found
                    
                    # Extract company - using the structure from the example
                    try:
                        # Look for the specific span with class t-14 t-normal
                        company_element = item.find_element(
                            By.XPATH, 
                            ".//span[@class='t-14 t-normal']"
                        )
                        company_text = company_element.text.strip()
                        
                        # Handle format: "Company · Type"
                        if '·' in company_text:
                            parts = company_text.split('·')
                            experience['company'] = parts[0].strip()
                            # Store company type if available (e.g., Internship)
                            if len(parts) > 1:
                                experience['type'] = parts[1].strip()
                        else:
                            experience['company'] = company_text
                            
                        print(f"Found company: {experience['company']}")
                    except Exception as e:
                        print(f"Could not find company with primary selector: {e}")
                        # Try alternate selectors
                        try:
                            company_element = item.find_element(
                                By.XPATH, 
                                ".//span[contains(@class, 't-14') and contains(@class, 't-normal')]"
                            )
                            company_text = company_element.text.strip()
                            if '·' in company_text:
                                experience['company'] = company_text.split('·')[0].strip()
                            else:
                                experience['company'] = company_text
                        except:
                            print("Could not find company with any selector")
                    
                    # Extract date range - using the structure from example
                    try:
                        date_element = item.find_element(
                            By.XPATH, 
                            ".//span[contains(@class, 'pvs-entity__caption-wrapper')]"
                        )
                        date_text = date_element.text.strip()
                        
                        # Handle date format like "Jul 2024 - Aug 2024 · 2 mos"
                        if '·' in date_text:
                            parts = date_text.split('·')
                            date_range = parts[0].strip()
                            experience['duration'] = parts[1].strip()
                            
                            if ' - ' in date_range:
                                dates = date_range.split(' - ')
                                experience['start_date'] = dates[0].strip()
                                experience['end_date'] = dates[1].strip()
                                
                        elif ' - ' in date_text:
                            dates = date_text.split(' - ')
                            experience['start_date'] = dates[0].strip()
                            experience['end_date'] = dates[1].strip()
                            
                        print(f"Found dates: {experience['start_date']} to {experience['end_date']}")
                    except Exception as e:
                        print(f"Could not find date with primary selector: {e}")
                        # Try alternate date selector
                        try:
                            date_element = item.find_element(
                                By.XPATH, 
                                ".//span[contains(@class, 't-14') and contains(@class, 't-black--light')]"
                            )
                            date_text = date_element.text.strip()
                            
                            if ' - ' in date_text:
                                dates = date_text.split(' - ')
                                experience['start_date'] = dates[0].strip()
                                experience['end_date'] = dates[1].strip()
                        except:
                            print("Could not find date with any selector")
                    
                    # Extract location - using the structure from example
                    try:
                        location_element = item.find_element(
                            By.XPATH, 
                            ".//span[@class='t-14 t-normal t-black--light'][last()]"
                        )
                        location_text = location_element.text.strip()
                        if "Remote" in location_text or "·" in location_text:
                            experience['location'] = location_text
                            print(f"Found location: {experience['location']}")
                    except Exception as e:
                        print(f"Could not find location: {e}")
                    
                    # Extract description if available
                    try:
                        desc_element = item.find_element(
                            By.XPATH, 
                            ".//div[contains(@class, 'inline-show-more-text')]"
                        )
                        experience['description'] = desc_element.text.strip()
                        print(f"Found description: {experience['description'][:50]}...")
                    except:
                        print("No description found or not available")
                    
                    # Only add if we found at least role and company
                    if experience['role'] and (experience['company'] or experience['start_date']):
                        profile_experiences.append(experience)
                        self.experiences.append(experience)
                        print(f"Added experience: {experience['role']} at {experience['company']}")
                    
                except Exception as e:
                    print(f"Error processing experience item {idx}: {e}")
            
            # Add experiences to profile
            profile['experiences'] = profile_experiences
            print(f"Extracted {len(profile_experiences)} experience items")
            
        except Exception as e:
            print(f"Error extracting experiences: {e}")
            import traceback
            traceback.print_exc()
            profile['experiences'] = []

    def _extract_education(self, profile):
        """Extract education items from profile using specific HTML selectors"""
        try:
            print("Attempting to extract education data...")
            
            # Try to find the education section using multiple selectors
            education_section = None
            
            # First try by ID (most reliable)
            try:
                # Find div with id="education" and get parent section
                education_div = self.driver.find_element(By.ID, "education")
                education_section = education_div.find_element(By.XPATH, "./ancestor::section")
                print("Found education section by ID")
            except Exception as e:
                print(f"Could not find education section by ID: {e}")
                
                # Try direct section with education header
                try:
                    education_section = self.driver.find_element(
                        By.XPATH, 
                        "//section[.//h2[contains(text(), 'Education')]]"
                    )
                    print("Found education section by header text")
                except Exception as e:
                    print(f"Could not find education section by header: {e}")
                    
                    # Try other selectors as fallback
                    selectors_to_try = [
                        "//section[.//div[contains(text(), 'Education')]]",
                        "//section[contains(@class, 'education-section')]",
                        "//div[contains(@id, 'education')]/ancestor::section",
                        "//section[contains(@id, 'education')]",
                    ]
                    
                    for selector in selectors_to_try:
                        try:
                            education_section = self.driver.find_element(By.XPATH, selector)
                            if education_section:
                                print(f"Found education section using selector: {selector}")
                                break
                        except:
                            continue
            
            if not education_section:
                print("Could not find education section with any selector")
                with open(f"{self.output_dir}/education_not_found.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                profile['education'] = []
                return
            
            # Scroll to make section visible
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", education_section)
            time.sleep(2)
            
            # Extract education list items using the specific HTML structure
            # First try the specific class from the example
            education_items = []
            try:
                education_items = education_section.find_elements(
                    By.XPATH, 
                    ".//li[contains(@class, 'artdeco-list__item')]"
                )
                print(f"Found {len(education_items)} education items with artdeco-list__item class")
            except Exception as e:
                print(f"Could not find education items with artdeco-list__item class: {e}")
                # Try alternate selectors
                try:
                    education_items = education_section.find_elements(By.XPATH, ".//li")
                    print(f"Found {len(education_items)} education items with li tag")
                except:
                    print("Could not find any education items")
            
            if not education_items:
                print("No education items found")
                profile['education'] = []
                return
            
            profile_education = []
            
            for idx, item in enumerate(education_items):
                try:
                    education = {
                        'profile_id': profile.get('profile_id', ''),
                        'school': None,
                        'degree': None,
                        'field_of_study': None,
                        'start_date': None,
                        'end_date': None,
                        'grade': None,
                        'activities': None
                    }
                    
                    # Extract school name - based on the HTML example
                    try:
                        school_element = item.find_element(
                            By.XPATH, 
                            ".//div[contains(@class, 'mr1') and contains(@class, 't-bold')]"
                        )
                        education['school'] = school_element.text.strip()
                        print(f"Found school: {education['school']}")
                    except Exception as e:
                        print(f"Could not find school with primary selector: {e}")
                        # Try alternate selectors
                        try:
                            school_element = item.find_element(By.XPATH, ".//span[contains(@class, 't-bold')]")
                            education['school'] = school_element.text.strip()
                        except:
                            # Try more generic approaches
                            try:
                                school_element = item.find_element(By.XPATH, ".//h3")
                                education['school'] = school_element.text.strip()
                            except:
                                print("Could not find school with any selector")
                                continue  # Skip if no school found
                    
                    # Extract degree and field of study - based on HTML example
                    try:
                        degree_element = item.find_element(
                            By.XPATH, 
                            ".//span[@class='t-14 t-normal']"
                        )
                        degree_text = degree_element.text.strip()
                        
                        # Handle format: "Degree, Field of Study"
                        if ',' in degree_text:
                            parts = degree_text.split(',', 1)
                            education['degree'] = parts[0].strip()
                            if len(parts) > 1:
                                education['field_of_study'] = parts[1].strip()
                        else:
                            education['degree'] = degree_text
                            
                        print(f"Found degree: {education['degree']}")
                    except Exception as e:
                        print(f"Could not find degree with primary selector: {e}")
                        # Try alternate selectors
                        try:
                            degree_element = item.find_element(
                                By.XPATH, 
                                ".//span[contains(@class, 't-14') and contains(@class, 't-normal')]"
                            )
                            degree_text = degree_element.text.strip()
                            
                            if ',' in degree_text:
                                parts = degree_text.split(',', 1)
                                education['degree'] = parts[0].strip()
                                if len(parts) > 1:
                                    education['field_of_study'] = parts[1].strip()
                            else:
                                education['degree'] = degree_text
                        except:
                            print("Could not find degree with any selector")
                    
                    # Extract date range - using the format from the example
                    try:
                        date_element = item.find_element(
                            By.XPATH, 
                            ".//span[contains(@class, 'pvs-entity__caption-wrapper')]"
                        )
                        date_text = date_element.text.strip()
                        
                        # Handle date formats - typically "2022 - 2025"
                        if ' - ' in date_text:
                            dates = date_text.split(' - ')
                            education['start_date'] = dates[0].strip()
                            education['end_date'] = dates[1].strip()
                            
                        print(f"Found dates: {education['start_date']} to {education['end_date']}")
                    except Exception as e:
                        print(f"Could not find date with primary selector: {e}")
                        # Try alternate date selector
                        try:
                            date_element = item.find_element(
                                By.XPATH, 
                                ".//span[contains(@class, 't-14') and contains(@class, 't-black--light')]"
                            )
                            date_text = date_element.text.strip()
                            
                            if ' - ' in date_text:
                                dates = date_text.split(' - ')
                                education['start_date'] = dates[0].strip()
                                education['end_date'] = dates[1].strip()
                        except:
                            print("Could not find date with any selector")
                    
                    # Look for grade - special format shown in the HTML example
                    try:
                        # Find all text elements that might contain grade info
                        possible_grade_elements = item.find_elements(
                            By.XPATH,
                            ".//div[contains(@class, 'inline-show-more-text')]"
                        )
                        
                        for element in possible_grade_elements:
                            text = element.text.strip()
                            if "Grade:" in text:
                                education['grade'] = text
                                print(f"Found grade: {education['grade']}")
                                break
                    except Exception as e:
                        print(f"Could not find grade information: {e}")
                    
                    # Extract activities if available
                    try:
                        activities_element = item.find_element(
                            By.XPATH, 
                            ".//div[contains(@class, 'activities') or contains(text(), 'Activities')]"
                        )
                        education['activities'] = activities_element.text.strip()
                        print(f"Found activities: {education['activities'][:50]}...")
                    except:
                        print("No activities found or not available")
                    
                    # Only add if we found at least school name
                    if education['school']:
                        profile_education.append(education)
                        self.education.append(education)
                        print(f"Added education: {education['degree']} at {education['school']}")
                    
                except Exception as e:
                    print(f"Error processing education item {idx}: {e}")
            
            # Add education to profile
            profile['education'] = profile_education
            print(f"Extracted {len(profile_education)} education items")
            
        except Exception as e:
            print(f"Error extracting education: {e}")
            import traceback
            traceback.print_exc()
            profile['education'] = []

    def _extract_skills(self, profile):
        """Extract skills from profile"""
        try:
            # Scroll to skills section
            try:
                # Try to find the skills section
                skills_section = self.driver.find_element(By.XPATH, "//section[.//div[contains(text(), 'Skills')]]")
                self.driver.execute_script("arguments[0].scrollIntoView();", skills_section)
                time.sleep(2)
            except:
                print("Could not scroll to skills section")
                return
            
            # Check if there's a "Show more" button to expand the skills section
            try:
                show_more_button = skills_section.find_element(By.XPATH, ".//button[contains(text(), 'Show more')]")
                show_more_button.click()
                time.sleep(2)
            except:
                # No "Show more" button or can't click it - continue with what's visible
                pass
            
            # Find all skill items
            skill_items = []
            try:
                # Try different selectors for skills
                skill_items = skills_section.find_elements(By.XPATH, ".//span[@class='mr1 hoverable-link-text t-bold']")
            except:
                try:
                    skill_items = skills_section.find_elements(By.XPATH, ".//span[contains(@class, 't-bold')]")
                except:
                    print("Could not find skills using primary selectors")
                    # Try alternative method with li elements
                    try:
                        skill_items = skills_section.find_elements(By.XPATH, ".//li")
                    except:
                        print("Could not find skills using alternative selectors")
                        return
            
            if not skill_items:
                print("No skills found")
                return
            
            profile_skills = []
            
            for item in skill_items:
                try:
                    skill_text = item.text.strip()
                    if skill_text and not skill_text.startswith("Show "):  # Filter out "Show more" buttons
                        # Create skill entry
                        skill = {
                            'profile_id': profile.get('profile_id', ''),
                            'skill': skill_text,
                            'endorsements': None
                        }
                        
                        # Try to get endorsement count if available
                        try:
                            # Look for endorsement count near the skill
                            endorsement_element = item.find_element(By.XPATH, "./following-sibling::span[1]")
                            endorsement_text = endorsement_element.text.strip()
                            if endorsement_text and endorsement_text.isdigit():
                                skill['endorsements'] = int(endorsement_text)
                        except:
                            # No endorsement count found
                            pass
                        
                        profile_skills.append(skill)
                        self.skills.append(skill)
                except Exception as e:
                    print(f"Error extracting skill: {e}")
            
            # Add skills to profile
            profile['skills'] = profile_skills
            print(f"Extracted {len(profile_skills)} skills")
            
        except Exception as e:
            print(f"Error extracting skills: {e}")
    
    def _save_data(self):
        """Save all profile data to JSON and CSV files"""
        try:
            if not self.profiles:
                print("No profiles to save")
                return
            
            # Create a comprehensive data structure with all profile data
            complete_profiles = []
            
            for profile in self.profiles:
                # Start with the base profile data
                complete_profile = dict(profile)
                
                # Remove nested structures that will be added properly below
                if 'experiences' in complete_profile:
                    del complete_profile['experiences']
                if 'education' in complete_profile:
                    del complete_profile['education']
                if 'skills' in complete_profile:
                    del complete_profile['skills']
                if 'contact_info' in complete_profile:
                    del complete_profile['contact_info']
                
                # Add experiences for this profile
                complete_profile['experiences'] = []
                profile_id = profile.get('profile_id', '')
                for exp in self.experiences:
                    if exp.get('profile_id', '') == profile_id:
                        complete_profile['experiences'].append(exp)
                
                # Add education for this profile
                complete_profile['education'] = []
                for edu in self.education:
                    if edu.get('profile_id', '') == profile_id:
                        complete_profile['education'].append(edu)
                
                # Add skills for this profile
                complete_profile['skills'] = []
                for skill in self.skills:
                    if skill.get('profile_id', '') == profile_id:
                        complete_profile['skills'].append(skill)
                
                # Add contact info for this profile
                for contact in self.contact_info:
                    if contact.get('profile_id', '') == profile_id:
                        complete_profile['contact_info'] = contact
                        break
                
                # Add timestamp if not already present
                if 'scraped_at' not in complete_profile:
                    complete_profile['scraped_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                complete_profiles.append(complete_profile)
            
            # Save all data to a comprehensive JSON file
            profiles_file = os.path.join(self.output_dir, 'linkedin_profiles.json')
            with open(profiles_file, 'w', encoding='utf-8') as f:
                json.dump(complete_profiles, f, indent=2, ensure_ascii=False)
            
            print(f"Saved complete data for {len(complete_profiles)} profiles to {profiles_file}")
            
            # Save to CSV
            csv_file = os.path.join(self.output_dir, 'linkedin_profiles.csv')
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'Profile ID', 'Name', 'Headline', 'Location', 'Profile URL',
                    'Email', 'Phone', 'Website', 'Twitter',
                    'Current Company', 'Current Position', 'Experience Count',
                    'Education Count', 'Skills Count', 'Open to Work',
                    'Scraped At'
                ])
                
                # Write data rows
                for profile in complete_profiles:
                    contact_info = profile.get('contact_info', {})
                    experiences = profile.get('experiences', [])
                    current_exp = experiences[0] if experiences else {}
                    
                    writer.writerow([
                        profile.get('profile_id', ''),
                        profile.get('name', ''),
                        profile.get('headline', ''),
                        profile.get('location', ''),
                        profile.get('profile_url', ''),
                        contact_info.get('email', ''),
                        contact_info.get('phone', ''),
                        contact_info.get('website', ''),
                        contact_info.get('twitter', ''),
                        current_exp.get('company', ''),
                        current_exp.get('role', ''),
                        len(experiences),
                        len(profile.get('education', [])),
                        len(profile.get('skills', [])),
                        profile.get('is_open_to_work', False),
                        profile.get('scraped_at', '')
                    ])
            
            print(f"Saved CSV data for {len(complete_profiles)} profiles to {csv_file}")
            
            # Save open to work profiles separately
            self._save_open_to_work_profiles()
                
        except Exception as e:
            print(f"Error saving data: {e}")
            import traceback
            traceback.print_exc()
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

    def scrape_profiles_from_urls(self, profile_urls):
        """Scrape profiles directly from a list of URLs"""
        if not profile_urls:
            print("No profile URLs provided")
            return False
            
        print(f"Preparing to scrape {len(profile_urls)} profile URLs")
        
        # Create a new list for detailed profiles
        for i, url in enumerate(profile_urls):
            print(f"Processing URL {i+1}/{len(profile_urls)}: {url}")
            
            # Validate URL format
            if not url.startswith("https://www.linkedin.com/in/"):
                print(f"Skipping invalid LinkedIn profile URL: {url}")
                continue
                
            try:
                # Extract profile ID
                profile_id = url.split('/in/')[-1].split('?')[0]
                
                # Create a basic profile entry
                basic_profile = {
                    "profile_id": profile_id,
                    "name": f"Profile {profile_id}",
                    "profile_url": url,
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Add to profiles list
                self.profiles.append(basic_profile)
                
                # Now scrape the detailed profile
                detailed_profile = self.scrape_profile(url)
                
                if detailed_profile:
                    # Update the basic profile with detailed info
                    for i, profile in enumerate(self.profiles):
                        if profile["profile_id"] == profile_id:
                            self.profiles[i] = detailed_profile
                            break
                    
                    # Save after each profile in case of interruption
                    self._save_data()
                
                # Add a random delay between profiles
                delay = random.uniform(5, 10)
                print(f"Waiting {delay:.1f} seconds before next profile...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"Error processing profile URL {url}: {e}")
        
        print(f"Completed scraping {len(profile_urls)} profile URLs")
        return True

    def search_and_save_profile_urls(self, search_term, max_profiles=23, output_file="profile_urls.txt"):
        """Search for profiles based on keyword and save just the URLs to a text file"""
        try:
            print(f"Searching for profiles matching: {search_term}")
            
            # Navigate to LinkedIn search page
            self.driver.get("https://www.linkedin.com/search/results/people/")
            time.sleep(2)
            
            # Find and fill the search input field
            search_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input.search-global-typeahead__input")))
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            
            # Wait for search results to load
            time.sleep(5)
            
            profile_urls = set()  # Use a set to avoid duplicates
            current_page = 1
            
            # Get total number of pages
            try:
                page_state = self.driver.find_element(By.CSS_SELECTOR, "span.artdeco-pagination__state--a11y")
                total_pages = int(page_state.text.split("of")[1].strip())
                print(f"Total pages found: {total_pages}")
            except:
                print("Could not determine total pages, defaulting to 10")
                total_pages = 10
            
            while len(profile_urls) < max_profiles and current_page <= total_pages:
                print(f"Scanning page {current_page} of {total_pages} for profile URLs...")
                
                # Extended wait for page to load fully
                time.sleep(3)
                
                # Get all profile links on this page
                try:
                    # Find all profile links (using various methods)
                    print("Looking for profile links...")
                    
                    # Method 1: Direct link search
                    profile_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/in/')]")
                    
                    page_urls = set()
                    for link in profile_links:
                        try:
                            url = link.get_attribute("href")
                            # Ensure it's a valid profile URL and not a company page or something else
                            if url and "/in/" in url and "linkedin.com" in url:
                                # Clean the URL to remove tracking parameters
                                clean_url = url.split('?')[0]
                                # Only include if it seems like a profile URL
                                if "/in/" in clean_url and len(clean_url.split("/in/")[1]) > 0:
                                    page_urls.add(clean_url)
                        except:
                            continue
                    
                    print(f"Found {len(page_urls)} profile URLs on page {current_page}")
                    profile_urls.update(page_urls)
                    
                    # If we have enough profiles or found none on this page, break
                    if len(profile_urls) >= max_profiles or not page_urls:
                        break
                    
                    # Try to find and click the next page number
                    try:
                        # Find the page number button
                        page_buttons = self.driver.find_elements(By.CSS_SELECTOR, "li.artdeco-pagination__indicator--number button")
                        next_page_found = False
                        
                        for button in page_buttons:
                            try:
                                page_num = int(button.text.strip())
                                if page_num == current_page + 1:
                                    # Scroll to the button
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                                    time.sleep(1)
                                    
                                    # Click using JavaScript
                                    self.driver.execute_script("arguments[0].click();", button)
                                    next_page_found = True
                                    break
                            except:
                                continue
                        
                        if not next_page_found:
                            print("Could not find next page button")
                            break
                        
                        # Wait for the next page to load
                        time.sleep(5)
                        current_page += 1
                        
                    except Exception as e:
                        print(f"Error navigating to next page: {e}")
                        break
                
                except Exception as e:
                    print(f"Error extracting profile links: {e}")
                    break
            
            # Limit to the requested number of profiles
            profile_urls_list = list(profile_urls)[:max_profiles]
            
            # Save profile URLs to file
            with open(output_file, 'w') as f:
                for url in profile_urls_list:
                    f.write(f"{url}\n")
            
            print(f"Saved {len(profile_urls_list)} profile URLs to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error during profile URL search: {e}")
            return False

    def scrape_from_url(self, search_url, max_profiles=10):
        """Scrape profiles from a specific LinkedIn search URL"""
        try:
            # Extract page number from URL
            page_num = 1
            if 'page=' in search_url:
                page_num = int(search_url.split('page=')[1].split('&')[0])
            
            print(f"Scraping profiles from page {page_num}")
            
            # Navigate to the search URL
            self.driver.get(search_url)
            time.sleep(5)  # Wait for page to load
            
            profile_count = 0
            
            # Try multiple selectors to find profile cards
            profile_cards = []
            selectors_to_try = [
                ".entity-result__item",
                ".reusable-search__result-container",
                "li.reusable-search__result-container",
                "li.search-result",
                "li.search-entity",
                "div[data-test-search-result]",
                "li[data-test-search-result]",
                "div.search-result",
                "div.search-entity",
                "li.artdeco-list__item"
            ]
            
            for selector in selectors_to_try:
                try:
                    profile_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if profile_cards:
                        print(f"Found {len(profile_cards)} profiles using selector: {selector}")
                        break
                except:
                    continue
            
            if not profile_cards:
                print("Could not find profile cards with any known selectors.")
                return False
            
            # Process each profile card on current page
            for card in profile_cards:
                if profile_count >= max_profiles:
                    break
                
                try:
                    # Extract profile URL
                    profile_link = None
                    try:
                        profile_link = card.find_element(By.CSS_SELECTOR, "a.app-aware-link")
                    except:
                        try:
                            profile_link = card.find_element(By.CSS_SELECTOR, "a[data-control-name='search_srp_result']")
                        except:
                            try:
                                profile_link = card.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
                            except:
                                continue
                    
                    if not profile_link:
                        continue
                        
                    profile_url = profile_link.get_attribute("href")
                    if not profile_url or "/in/" not in profile_url:
                        continue
                    
                    # Clean the URL to remove tracking parameters
                    profile_url = profile_url.split('?')[0]
                    
                    # Extract profile ID
                    profile_id = profile_url.split('/in/')[-1]
                    
                    # Check if we already have this profile
                    if any(p.get('profile_id') == profile_id for p in self.profiles):
                        print(f"Skipping already scraped profile: {profile_id}")
                        continue
                    
                    # Create basic profile entry
                    profile_data = {
                        "profile_id": profile_id,
                        "profile_url": profile_url,
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Add to profiles list
                    self.profiles.append(profile_data)
                    profile_count += 1
                    
                    # Scrape the detailed profile
                    detailed_profile = self.scrape_profile(profile_url)
                    if detailed_profile:
                        # Update the basic profile with detailed info
                        for i, profile in enumerate(self.profiles):
                            if profile["profile_id"] == profile_id:
                                self.profiles[i] = detailed_profile
                                break
                    
                    # Save after each profile in case of interruption
                    self._save_data()
                    
                    # Add a random delay between profiles
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    print(f"Error processing profile card: {e}")
                    continue
            
            print(f"\nSuccessfully collected data for {len(self.profiles)} profiles from page {page_num}")
            return True
            
        except Exception as e:
            print(f"Error during profile scraping: {e}")
            return False

    def scrape_multiple_pages(self, base_url, start_page=1, end_page=10, profiles_per_page=20):
        """Scrape profiles from multiple pages of search results"""
        try:
            for page in range(start_page, end_page + 1):
                # Construct URL for current page
                current_url = base_url.split('page=')[0] + f'page={page}' + '&' + base_url.split('page=')[1].split('&', 1)[1]
                
                # Scrape profiles from current page
                success = self.scrape_from_url(current_url, max_profiles=profiles_per_page)
                
                # Add delay between pages
                time.sleep(random.uniform(3, 7))
        except Exception as e:
            print(f"Error during multi-page scraping: {e}")
            return False

    def generate_search_urls(self, domain, job_title=None, total_pages=100):
        """Generate LinkedIn search URLs for a given domain and job title"""
        base_url = "https://www.linkedin.com/search/results/people/"
        
        # Construct search query based on domain and job title
        if job_title:
            search_query = f"{job_title} {domain}"
        else:
            search_query = domain
            
        encoded_query = search_query.replace(' ', '%20')
        links = []

        for page in range(1, total_pages + 1):
            url = f"{base_url}?keywords={encoded_query}&origin=GLOBAL_SEARCH_HEADER&page={page}"
            links.append(url)

        return links

    def scrape_profiles_from_search_urls(self, domain, job_title=None, total_pages=100, max_profiles_per_page=10):
        """Scrape profiles from generated search URLs for a specific domain and job title"""
        try:
            # Generate search URLs
            search_urls = self.generate_search_urls(domain, job_title, total_pages)
            print(f"Generated {len(search_urls)} search URLs for {domain} {job_title if job_title else ''}")
            
            total_profiles_collected = 0
            profile_urls = set()  # Use a set to avoid duplicates
            
            for url in search_urls:
                try:
                    print(f"\nProcessing search URL: {url}")
                    self.driver.get(url)
                    time.sleep(random.uniform(5, 8))  # Increased initial delay
                    
                    # Get current page number
                    current_page = self._get_current_page()
                    print(f"Current page: {current_page}")
                    
                    # Scroll multiple times to load all profiles
                    self._scroll_page_multiple_times()
                    
                    # Try multiple selectors to find profile links
                    profile_links = self._find_profile_links()
                    
                    page_profiles = set()
                    for link in profile_links:
                        try:
                            profile_url = link.get_attribute("href")
                            if profile_url and "/in/" in profile_url and "linkedin.com" in profile_url:
                                # Clean the URL to remove tracking parameters
                                clean_url = profile_url.split('?')[0]
                                if clean_url not in profile_urls:
                                    page_profiles.add(clean_url)
                        except:
                            continue
                    
                    print(f"Found {len(page_profiles)} new profiles on this page")
                    profile_urls.update(page_profiles)
                    total_profiles_collected = len(profile_urls)
                    
                    # Save URLs after each page
                    self._save_profile_urls(profile_urls, domain, job_title)
                    
                    # Add longer random delay between pages
                    time.sleep(random.uniform(8, 15))
                    
                    if total_profiles_collected >= max_profiles_per_page * total_pages:
                        print(f"Reached maximum number of profiles ({total_profiles_collected})")
                        break
                        
                except Exception as e:
                    print(f"Error processing search URL {url}: {e}")
                    # Add longer delay on error
                    time.sleep(random.uniform(10, 15))
                    continue
            
            print(f"\nTotal unique profile URLs collected: {total_profiles_collected}")
            return True
            
        except Exception as e:
            print(f"Error in scrape_profiles_from_search_urls: {e}")
            return False

    def _get_current_page(self):
        """Get the current page number from the pagination"""
        try:
            # Try to find the active page button
            active_page = self.driver.find_element(By.CSS_SELECTOR, "li.artdeco-pagination__indicator--number.active.selected button")
            return int(active_page.get_attribute("aria-label").split("Page ")[1])
        except:
            try:
                # Try to get it from the page state
                page_state = self.driver.find_element(By.CSS_SELECTOR, "div.artdeco-pagination__page-state")
                return int(page_state.text.split("Page ")[1].split(" of")[0])
            except:
                return 1

    def _navigate_to_page(self, page_number):
        """Navigate to a specific page number"""
        try:
            # Find the page button
            page_button = self.driver.find_element(By.CSS_SELECTOR, f"li[data-test-pagination-page-btn='{page_number}'] button")
            
            # Scroll to the button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", page_button)
            time.sleep(random.uniform(1, 2))
            
            # Click the button
            page_button.click()
            time.sleep(random.uniform(3, 5))
            
            return True
        except:
            return False

    def _click_next_button(self):
        """Click the next page button"""
        try:
            # Find the next button
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button.artdeco-pagination__button--next")
            
            # Check if the button is disabled
            if "disabled" in next_button.get_attribute("class"):
                return False
            
            # Scroll to the button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(random.uniform(1, 2))
            
            # Click the button
            next_button.click()
            time.sleep(random.uniform(3, 5))
            
            return True
        except:
            return False

    def _scroll_page_multiple_times(self):
        """Scroll the page multiple times with random delays to load all content"""
        try:
            # Scroll down multiple times with random pauses
            for _ in range(5):  # Increased number of scrolls
                # Random scroll amount
                scroll_amount = random.randint(300, 800)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                time.sleep(random.uniform(1, 3))
                
                # Sometimes scroll back up a bit (like a human would)
                if random.random() > 0.7:  # 30% chance
                    self.driver.execute_script("window.scrollBy(0, -100);")
                    time.sleep(random.uniform(0.5, 1))
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                current_position = self.driver.execute_script("return window.pageYOffset")
                
                if current_position + self.driver.execute_script("return window.innerHeight") >= new_height:
                    break
                    
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"Error during scrolling: {e}")

    def _find_profile_links(self):
        """Find profile links using multiple selectors and methods"""
        profile_links = set()
        
        # List of selectors to try based on the HTML structure
        selectors = [
            "//a[contains(@class, 'app-aware-link')]",
            "//a[contains(@class, 'search-result__result-link')]",
            "//a[contains(@class, 'entity-result__title-text')]",
            "//a[contains(@class, 'reusable-search__result-container')]",
            "//a[contains(@class, 'artdeco-entity-lockup__link')]",
            "//a[contains(@href, '/in/')]"
        ]
        
        # Try each selector
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    try:
                        href = element.get_attribute("href")
                        if href and "/in/" in href and "linkedin.com" in href:
                            profile_links.add(element)
                    except:
                        continue
            except:
                continue
        
        # If we still don't have enough links, try a more general approach
        if len(profile_links) < 10:
            try:
                # Find all links and filter for profiles
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                for link in all_links:
                    try:
                        href = link.get_attribute("href")
                        if href and "/in/" in href and "linkedin.com" in href:
                            profile_links.add(link)
                    except:
                        continue
            except:
                pass
        
        return list(profile_links)

    def _save_profile_urls(self, profile_urls, domain, job_title=None):
        """Save profile URLs to a file with domain-specific naming"""
        try:
            # Create filename based on domain and job title
            filename = f"profile_urls_{domain.lower().replace(' ', '_')}"
            if job_title:
                filename += f"_{job_title.lower().replace(' ', '_')}"
            filename += ".txt"
            
            with open(filename, 'w') as f:
                for url in sorted(profile_urls):
                    f.write(f"{url}\n")
            print(f"Saved {len(profile_urls)} profile URLs to {filename}")
        except Exception as e:
            print(f"Error saving profile URLs: {e}")

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

    def collect_100_profiles(self, search_term, max_profiles=500):
        """Collect profiles from LinkedIn search results"""
        print(f"Starting to collect data from up to {max_profiles} profiles for search term: {search_term}")
        
        # Navigate to LinkedIn search page
        self.driver.get("https://www.linkedin.com/search/results/people/")
        time.sleep(random.uniform(2, 4))
        
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
                search_input = self.wait_for_element(selector, timeout=10)
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
        
        # Fill in search input
        try:
            search_input.clear()
            search_input.send_keys(search_term)
            time.sleep(random.uniform(1, 2))
            search_input.send_keys(Keys.RETURN)
            time.sleep(random.uniform(2, 4))
        except Exception as e:
            print(f"Error interacting with search input: {e}")
            return False
        
        # Initialize variables for pagination
        unique_urls = set()
        consecutive_empty_pages = 0
        max_consecutive_empty = 3
        current_page = 1
        
        while len(unique_urls) < max_profiles and consecutive_empty_pages < max_consecutive_empty:
            print(f"\nProcessing page {current_page}...")
            print(f"Current unique profiles collected: {len(unique_urls)}")
            
            # Scroll multiple times to ensure all content is loaded
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 2))
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(random.uniform(1, 2))
            
            # Try multiple selectors to find profile links
            selectors = [
                'a.app-aware-link[href*="/in/"]',
                'a[data-control-name="search_srp_result"]',
                'a[href*="/in/"]'
            ]
            
            profile_links = []
            for selector in selectors:
                links = self.wait_for_elements(selector)
                if links:
                    profile_links.extend(links)
                    break
            
            if not profile_links:
                print("No profile links found on this page")
                consecutive_empty_pages += 1
                current_page += 1
                continue
            
            # Reset consecutive empty pages counter
            consecutive_empty_pages = 0
            
            # Process each profile link
            page_urls = set()
            for link in profile_links:
                if len(unique_urls) >= max_profiles:
                    break
                    
                try:
                    profile_url = link.get_attribute('href')
                    if profile_url and "/in/" in profile_url and "linkedin.com" in profile_url:
                        # Clean the URL to remove tracking parameters
                        clean_url = profile_url.split('?')[0]
                        if clean_url not in unique_urls:
                            page_urls.add(clean_url)
                            print(f"Found profile URL: {clean_url}")
                except Exception as e:
                    print(f"Error getting URL from link: {e}")
                    continue
            
            # Add new URLs to the set
            unique_urls.update(page_urls)
            
            # Save URLs after each page
            if page_urls:
                output_file = f"profile_urls_{search_term.lower().replace(' ', '_')}.txt"
                with open(output_file, 'w') as f:
                    for url in sorted(unique_urls):
                        f.write(f"{url}\n")
                print(f"Saved {len(unique_urls)} profile URLs to {output_file}")
            
            # Try to navigate to next page
            try:
                next_button = self.wait_for_element('button[aria-label="Next"]')
                if next_button and next_button.is_enabled():
                    # Scroll to the button
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    
                    # Click using JavaScript
                    self.driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(random.uniform(2, 4))
                    current_page += 1
                else:
                    print("No more pages available")
                    break
            except Exception as e:
                print(f"Error navigating to next page: {str(e)}")
                break
        
        print(f"\nFinished collecting profiles. Total unique profiles found: {len(unique_urls)}")
        
        # Final save of all URLs
        if unique_urls:
            output_file = f"profile_urls_{search_term.lower().replace(' ', '_')}.txt"
            with open(output_file, 'w') as f:
                for url in sorted(unique_urls):
                    f.write(f"{url}\n")
            print(f"Final save: {len(unique_urls)} profile URLs saved to {output_file}")
        
        return len(unique_urls) > 0

    def wait_for_element(self, selector, timeout=10):
        """Wait for an element to be present and return it"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except:
            return None

    def wait_for_elements(self, selector, timeout=10):
        """Wait for elements to be present and return them"""
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
            return elements
        except:
            return []

if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description='LinkedIn Profile Scraper')
    parser.add_argument('--search', help='Search term for LinkedIn profiles')
    parser.add_argument('--max', type=int, default=100, help='Maximum number of profiles to collect')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--use-profile', action='store_true', help='Use Chrome profile')
    parser.add_argument('--profile-path', help='Path to Chrome profile')
    parser.add_argument('--cookies', help='Path to cookies file')
    parser.add_argument('--output', help='Output directory')
    parser.add_argument('--urls-file', help='File containing profile URLs to scrape')
    
    args = parser.parse_args()
    
    # Create timestamp for filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.urls_file:
        scraper = LinkedInSeleniumScraper(
            headless=args.headless,
            use_profile=args.use_profile,
            profile_path=args.profile_path
        )
        
        try:
            if scraper.login():
                print(f"Starting to scrape profiles from {args.urls_file}")
                # Read URLs from file
                with open(args.urls_file, 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                
                print(f"Found {len(urls)} URLs to scrape")
                success = scraper.scrape_profiles_from_urls(urls)
                
                if success:
                    print(f"Successfully scraped {len(scraper.profiles)} profiles")
                    output_dir = args.output or 'output'
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Save to JSON
                    json_file = os.path.join(output_dir, f'linkedin_profiles_{timestamp}.json')
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(scraper.profiles, f, ensure_ascii=False, indent=2)
                    print(f"Data saved to JSON: {json_file}")
                    
                    # Save to CSV
                    csv_file = os.path.join(output_dir, f'linkedin_profiles_{timestamp}.csv')
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # Write header
                        writer.writerow([
                            'Profile ID', 'Name', 'Headline', 'Location', 'Profile URL',
                            'Email', 'Phone', 'Website', 'Twitter',
                            'Current Company', 'Current Position', 'Experience Count',
                            'Education Count', 'Skills Count', 'Open to Work',
                            'Scraped At'
                        ])
                        # Write data rows
                        for profile in scraper.profiles:
                            contact_info = profile.get('contact_info', {})
                            experiences = profile.get('experiences', [])
                            current_exp = experiences[0] if experiences else {}
                            
                            writer.writerow([
                                profile.get('profile_id', ''),
                                profile.get('name', ''),
                                profile.get('headline', ''),
                                profile.get('location', ''),
                                profile.get('profile_url', ''),
                                contact_info.get('email', ''),
                                contact_info.get('phone', ''),
                                contact_info.get('website', ''),
                                contact_info.get('twitter', ''),
                                current_exp.get('company', ''),
                                current_exp.get('role', ''),
                                len(experiences),
                                len(profile.get('education', [])),
                                len(profile.get('skills', [])),
                                profile.get('is_open_to_work', False),
                                profile.get('scraped_at', '')
                            ])
                    print(f"Data saved to CSV: {csv_file}")
                else:
                    print("Failed to scrape profiles")
            else:
                print("Failed to login to LinkedIn")
        finally:
            scraper.close()
    elif args.search:
        scraper = LinkedInSeleniumScraper(
            headless=args.headless,
            use_profile=args.use_profile,
            profile_path=args.profile_path
        )
        
        try:
            if scraper.login():
                print(f"Starting to collect {args.max} profiles for search term: {args.search}")
                success = scraper.collect_100_profiles(args.search, max_profiles=args.max)
                
                if success:
                    print(f"Successfully collected {len(scraper.profiles)} profiles")
                    output_dir = args.output or 'output'
                    os.makedirs(output_dir, exist_ok=True)
                    
                    # Save to JSON
                    json_file = os.path.join(output_dir, f'linkedin_profiles_{args.search.replace(" ", "_")}_{timestamp}.json')
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(scraper.profiles, f, ensure_ascii=False, indent=2)
                    print(f"Data saved to JSON: {json_file}")
                    
                    # Save to CSV
                    csv_file = os.path.join(output_dir, f'linkedin_profiles_{args.search.replace(" ", "_")}_{timestamp}.csv')
                    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        # Write header
                        writer.writerow([
                            'Profile ID', 'Name', 'Headline', 'Location', 'Profile URL',
                            'Email', 'Phone', 'Website', 'Twitter',
                            'Current Company', 'Current Position', 'Experience Count',
                            'Education Count', 'Skills Count', 'Open to Work',
                            'Scraped At'
                        ])
                        # Write data rows
                        for profile in scraper.profiles:
                            contact_info = profile.get('contact_info', {})
                            experiences = profile.get('experiences', [])
                            current_exp = experiences[0] if experiences else {}
                            
                            writer.writerow([
                                profile.get('profile_id', ''),
                                profile.get('name', ''),
                                profile.get('headline', ''),
                                profile.get('location', ''),
                                profile.get('profile_url', ''),
                                contact_info.get('email', ''),
                                contact_info.get('phone', ''),
                                contact_info.get('website', ''),
                                contact_info.get('twitter', ''),
                                current_exp.get('company', ''),
                                current_exp.get('role', ''),
                                len(experiences),
                                len(profile.get('education', [])),
                                len(profile.get('skills', [])),
                                profile.get('is_open_to_work', False),
                                profile.get('scraped_at', '')
                            ])
                    print(f"Data saved to CSV: {csv_file}")
                else:
                    print("Failed to collect profiles")
            else:
                print("Failed to login to LinkedIn")
        finally:
            scraper.close()
    else:
        print("Please provide either a search term using --search or a file of URLs using --urls-file")