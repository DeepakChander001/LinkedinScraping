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

class NaukriJobScraper:
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
        chrome_options.add_argument("--disable-v-shm-usage")
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
    
    def collect_job_urls(self, keyword, location, experience, max_pages=50):
        """Collect job URLs from all pages and save to file"""
        try:
            job_urls = set()  # Use set to avoid duplicates
            current_page = 1
            
            # Format keyword and location for URL
            formatted_keyword = keyword.lower().replace(" ", "-")
            formatted_location = location.lower().replace(" ", "-")
            
            # Construct the search URL with proper parameters for US jobs
            search_url = f"https://www.naukri.com/{formatted_keyword}-jobs-in-{formatted_location}?k={formatted_keyword}&l={formatted_location}&experience={experience}&location=united-states"
            print(f"Navigating to URL: {search_url}")
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))
            
            # Scroll to load all content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
            
            # Get total number of jobs
            try:
                # Try multiple selectors for job count
                selectors = [
                    "span[class*='search-count']",
                    "span[class*='job-count']",
                    "span[class*='total-jobs']"
                ]
                
                jobs_count_element = None
                for selector in selectors:
                    try:
                        jobs_count_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        break
                    except:
                        continue
                
                if jobs_count_element:
                jobs_count_text = jobs_count_element.text
                total_jobs = int(jobs_count_text.split()[0].replace(',', ''))
                print(f"Total jobs found: {total_jobs}")
                
                # Calculate total pages (20 jobs per page)
                total_pages = (total_jobs + 19) // 20
                print(f"Total pages to scrape: {total_pages}")
                else:
                    print("Could not find job count element, will try to scrape available pages")
                    total_pages = max_pages
                    
            except Exception as e:
                print(f"Could not determine total pages: {e}")
                total_pages = max_pages
            
            while current_page <= min(total_pages, max_pages):
                print(f"\nProcessing page {current_page} of {min(total_pages, max_pages)}...")
                
                # Scroll to load all content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
                # Find all job cards
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.srp-jobtuple-wrapper")
                print(f"Found {len(job_cards)} jobs on this page")
                
                # Extract URLs from job cards
                for card in job_cards:
                    try:
                        job_link = card.find_element(By.CSS_SELECTOR, "a.title")
                        job_url = job_link.get_attribute("href")
                        if job_url:
                            job_urls.add(job_url)
                            print(f"Found job URL: {job_url}")
                    except Exception as e:
                        print(f"Error extracting job URL: {e}")
                
                # Try to navigate to next page
                try:
                    # Construct the next page URL
                    next_page = current_page + 1
                    if next_page > min(total_pages, max_pages):
                        print("Reached maximum number of pages")
                        break
                    
                    # For page 2, the URL format is different
                    if next_page == 2:
                        next_page_url = f"https://www.naukri.com/{formatted_keyword}-jobs-in-{formatted_location}-{next_page}?k={formatted_keyword}&l={formatted_location}&experience={experience}&location=united-states"
                    else:
                        next_page_url = f"https://www.naukri.com/{formatted_keyword}-jobs-in-{formatted_location}-{next_page}?k={formatted_keyword}&l={formatted_location}&experience={experience}&location=united-states"
                    
                    print(f"Navigating to page {next_page}: {next_page_url}")
                    self.driver.get(next_page_url)
                    time.sleep(random.uniform(3, 5))
                    current_page += 1
                    
                except Exception as e:
                    print(f"Error navigating to next page: {e}")
                    break
            
            # Save URLs to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            urls_file = os.path.join(self.output_dir, f'naukri_job_urls_{formatted_keyword}_{formatted_location}_{timestamp}.txt')
            with open(urls_file, 'w', encoding='utf-8') as f:
                for url in job_urls:
                    f.write(f"{url}\n")
            
            print(f"\nSaved {len(job_urls)} job URLs to {urls_file}")
            return urls_file
            
        except Exception as e:
            print(f"Error collecting job URLs: {e}")
            return None
    
    def scrape_job_details(self, job_url):
        """Scrape details of a single job"""
        try:
            print(f"Navigating to: {job_url}")
            self.driver.get(job_url)
            
            # Wait for page to load completely
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(random.uniform(3, 5))
                
                # Check if we're on a valid job page
                if "job-listings" not in self.driver.current_url:
                    print("Not a valid job listing page")
                    return None
                
                # Scroll to load all content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
            except Exception as e:
                print(f"Error loading page: {e}")
                return None
            
            job_data = {
                'job_url': job_url,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Get job title - try multiple selectors
            try:
                selectors = [
                    "a.title",
                    "h1[class*='title']",
                    "h1[class*='job-title']",
                    "h1[class*='header']"
                ]
                for selector in selectors:
                    try:
                        title_element = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        job_data['job_role'] = title_element.text.strip()
                        print(f"Found job title: {job_data['job_role']}")
                        break
            except:
                        continue
            except Exception as e:
                print(f"Error finding job title: {e}")
                job_data['job_role'] = "Not found"
            
            # Get company name
            try:
                company_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles_jd-header-comp-name__MvqAI a"))
                )
                job_data['company_name'] = company_element.text.strip()
                print(f"Found company: {job_data['company_name']}")
            except Exception as e:
                print(f"Error finding company name: {e}")
                job_data['company_name'] = "Not found"
            
            # Get experience
            try:
                exp_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles_jhc__exp__k_giM span"))
                )
                job_data['experience'] = exp_element.text.strip()
                print(f"Found experience: {job_data['experience']}")
            except Exception as e:
                print(f"Error finding experience: {e}")
                job_data['experience'] = "Not found"
            
            # Get salary
            try:
                salary_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles_jhc__salary__jdfEC span"))
                )
                job_data['salary'] = salary_element.text.strip()
                print(f"Found salary: {job_data['salary']}")
            except Exception as e:
                print(f"Error finding salary: {e}")
                job_data['salary'] = "Not found"
            
            # Get location
            try:
                location_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.styles_jhc__loc___Du2H span.styles_jhc__location__W_pVs"))
                )
                # Get all location links
                location_links = location_element.find_elements(By.TAG_NAME, "a")
                locations = [link.text.strip() for link in location_links]
                job_data['location'] = ", ".join(locations)
                print(f"Found location: {job_data['location']}")
            except Exception as e:
                print(f"Error finding location: {e}")
                job_data['location'] = "Not found"
            
            # Get role
            try:
                # Find all details sections
                details_sections = self.driver.find_elements(By.CSS_SELECTOR, "div.styles_details__Y424J")
                for section in details_sections:
                    try:
                        label = section.find_element(By.TAG_NAME, "label")
                        if "Role:" in label.text:
                            role_link = section.find_element(By.TAG_NAME, "a")
                            job_data['role'] = role_link.text.strip()
                            print(f"Found role: {job_data['role']}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error finding role: {e}")
                job_data['role'] = "Not found"
            
            # Get industry type
            try:
                # Find all details sections
                details_sections = self.driver.find_elements(By.CSS_SELECTOR, "div.styles_details__Y424J")
                for section in details_sections:
                    try:
                        label = section.find_element(By.TAG_NAME, "label")
                        if "Industry Type:" in label.text:
                            industry_link = section.find_element(By.TAG_NAME, "a")
                            job_data['industry_type'] = industry_link.text.strip()
                            print(f"Found industry type: {job_data['industry_type']}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error finding industry type: {e}")
                job_data['industry_type'] = "Not found"
            
            # Get department
            try:
                # Find all details sections
                details_sections = self.driver.find_elements(By.CSS_SELECTOR, "div.styles_details__Y424J")
                for section in details_sections:
                    try:
                        label = section.find_element(By.TAG_NAME, "label")
                        if "Department:" in label.text:
                            dept_link = section.find_element(By.TAG_NAME, "a")
                            job_data['department'] = dept_link.text.strip()
                            print(f"Found department: {job_data['department']}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error finding department: {e}")
                job_data['department'] = "Not found"
            
            # Get employment type
            try:
                # Find all details sections
                details_sections = self.driver.find_elements(By.CSS_SELECTOR, "div.styles_details__Y424J")
                for section in details_sections:
                    try:
                        label = section.find_element(By.TAG_NAME, "label")
                        if "Employment Type:" in label.text:
                            emp_span = section.find_element(By.CSS_SELECTOR, "span span")
                            job_data['employment_type'] = emp_span.text.strip()
                            print(f"Found employment type: {job_data['employment_type']}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error finding employment type: {e}")
                job_data['employment_type'] = "Not found"
            
            # Get role category
            try:
                # Find all details sections
                details_sections = self.driver.find_elements(By.CSS_SELECTOR, "div.styles_details__Y424J")
                for section in details_sections:
                    try:
                        label = section.find_element(By.TAG_NAME, "label")
                        if "Role Category:" in label.text:
                            role_cat_span = section.find_element(By.CSS_SELECTOR, "span span")
                            job_data['role_category'] = role_cat_span.text.strip()
                            print(f"Found role category: {job_data['role_category']}")
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Error finding role category: {e}")
                job_data['role_category'] = "Not found"
            
            # Get education
            try:
                # Get UG education
                education_section = self.driver.find_element(By.CSS_SELECTOR, "div.styles_education__KXFkO")
                education_details = education_section.find_elements(By.CSS_SELECTOR, "div.styles_details__Y424J")
                for detail in education_details:
                    try:
                        label = detail.find_element(By.TAG_NAME, "label")
                        if "UG:" in label.text:
                            ug_span = detail.find_element(By.TAG_NAME, "span")
                            job_data['education_ug'] = ug_span.text.strip()
                        elif "PG:" in label.text:
                            pg_span = detail.find_element(By.TAG_NAME, "span")
                            job_data['education_pg'] = pg_span.text.strip()
                    except:
                        continue
                print(f"Found education: UG - {job_data['education_ug']}, PG - {job_data['education_pg']}")
            except Exception as e:
                print(f"Error finding education: {e}")
                job_data['education_ug'] = "Not found"
                job_data['education_pg'] = "Not found"
            
            # Get job description - try multiple selectors
            try:
                selectors = [
                    "div.styles_JDC__dang-inner-html__h0K4t",
                    "div[class*='description']",
                    "div[class*='job-desc']",
                    "div[class*='jd']"
                ]
                for selector in selectors:
                    try:
                        desc_element = self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                job_data['description'] = desc_element.text.strip()
                        print("Found job description")
                        break
            except:
                        continue
            except Exception as e:
                print(f"Error finding job description: {e}")
                job_data['description'] = "Not found"
            
            # Get skills - try multiple selectors
            try:
                selectors = [
                    "a.styles_chip__7YCfG span",
                    "span[class*='skill']",
                    "a[class*='skill']",
                    "div[class*='skill'] span"
                ]
                for selector in selectors:
                    try:
                        skills_elements = self.wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                skills = [skill.text.strip() for skill in skills_elements]
                job_data['skills'] = ", ".join(skills)
                        print(f"Found skills: {job_data['skills']}")
                        break
            except:
                        continue
            except Exception as e:
                print(f"Error finding skills: {e}")
                job_data['skills'] = "Not found"
            
            return job_data
            
        except Exception as e:
            print(f"Error scraping job details: {e}")
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
                        print(f"Successfully scraped: {job_data['job_role']} at {job_data['company_name']}")
                    
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
    
    def _save_data(self):
        """Save scraped data to JSON and CSV files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Save to JSON
            json_file = os.path.join(self.output_dir, f'naukri_jobs_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.jobs, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(self.jobs)} jobs to JSON: {json_file}")
            
            # Save to CSV
            csv_file = os.path.join(self.output_dir, f'naukri_jobs_{timestamp}.csv')
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow([
                    'Job Role', 'Company Name', 'Location', 'Experience',
                    'Salary', 'Description', 'Skills', 'Job URL', 'Scraped At'
                ])
                # Write data rows
                for job in self.jobs:
                    writer.writerow([
                        job.get('job_role', ''),
                        job.get('company_name', ''),
                        job.get('location', ''),
                        job.get('experience', ''),
                        job.get('salary', ''),
                        job.get('description', ''),
                        job.get('skills', ''),
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
    
    parser = argparse.ArgumentParser(description='Naukri Job Scraper')
    parser.add_argument('--keyword', help='Job search keyword (e.g., "AI Engineer", "Data Scientist")', default='AI Engineer')
    parser.add_argument('--location', help='Job location (e.g., "united-states-usa", "bengaluru")', default='united-states-usa')
    parser.add_argument('--experience', help='Experience level (0 for fresher, 1 for 1-3 years, etc.)', default='0')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum number of pages to scrape')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--collect-urls', action='store_true', help='Only collect job URLs')
    parser.add_argument('--urls-file', help='File containing job URLs to scrape')
    
    args = parser.parse_args()
    
    # Format the keyword for URL
    keyword = args.keyword.lower().replace(" ", "-")
    
    scraper = NaukriJobScraper(headless=args.headless)
    
    try:
        if args.collect_urls:
            print(f"Starting to collect job URLs for keyword: {args.keyword}")
            print(f"Location: {args.location}")
            print(f"Experience: {args.experience} years")
            urls_file = scraper.collect_job_urls(
                keyword,
                args.location,
                args.experience,
                max_pages=args.max_pages
            )
            if urls_file:
                print(f"Job URLs saved to: {urls_file}")
                print(f"\nTo scrape job details, run:")
                print(f"python naukri_job_scraper.py --urls-file {urls_file}")
        elif args.urls_file:
            print(f"Starting to scrape job details from: {args.urls_file}")
            success = scraper.scrape_jobs_from_urls(args.urls_file)
            if success:
                print(f"Successfully scraped {len(scraper.jobs)} jobs")
            else:
                print("Failed to scrape jobs")
        else:
            print("Please specify either --collect-urls or --urls-file")
    finally:
        scraper.close() 