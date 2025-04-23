from LinkedinScraper.selenium_linkedin_scraper import LinkedInSeleniumScraper
import time
import random

def read_profile_urls(filename="profile_urls.txt"):
    """Read profile URLs from file"""
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading profile URLs: {e}")
        return []

def main():
    # Initialize the scraper
    scraper = LinkedInSeleniumScraper()
    
    try:
        # Login to LinkedIn
        if not scraper.login():
            print("Failed to login to LinkedIn")
            return
        
        # Read profile URLs from file
        profile_urls = read_profile_urls()
        if not profile_urls:
            print("No profile URLs found in profile_urls.txt")
            return
        
        print(f"Found {len(profile_urls)} profile URLs to scrape")
        
        # Scrape each profile
        for i, url in enumerate(profile_urls, 1):
            try:
                print(f"\nScraping profile {i}/{len(profile_urls)}: {url}")
                profile_data = scraper.scrape_profile(url)
                
                if profile_data:
                    print(f"Successfully scraped profile {i}")
                else:
                    print(f"Failed to scrape profile {i}")
                
                # Add random delay between profiles
                time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                print(f"Error scraping profile {url}: {e}")
                continue
        
        print("\nFinished scraping all profiles")
        
    except Exception as e:
        print(f"Error in main: {e}")
    
    finally:
        # Close the browser
        scraper.driver.quit()

if __name__ == "__main__":
    main() 