import json
import os
import argparse
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def save_cookies(username, password, output_file="linkedin_cookies.json"):
    """
    Login to LinkedIn using Selenium and save the cookies to a file.
    """
    print("Launching browser...")
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    
    # Create a new Chrome session
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to LinkedIn
        print("Navigating to LinkedIn...")
        driver.get("https://www.linkedin.com/login")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        # Enter login credentials
        print("Entering credentials...")
        driver.find_element(By.ID, "username").send_keys(username)
        driver.find_element(By.ID, "password").send_keys(password)
        
        # Click login button
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        
        # Wait for login to complete
        print("Logging in...")
        WebDriverWait(driver, 30).until(
            EC.url_contains("linkedin.com/feed")
        )
        
        # Wait a bit to ensure all cookies are set
        time.sleep(3)
        
        # Get all cookies
        print("Extracting cookies...")
        cookies = driver.get_cookies()
        
        # Save cookies to file
        with open(output_file, 'w') as f:
            json.dump(cookies, f)
        
        print(f"Successfully saved cookies to {output_file}")
        
        # Navigate to a profile to verify authentication
        print("Verifying authentication...")
        driver.get("https://www.linkedin.com/search/results/people/?keywords=AI%20engineer")
        
        # Wait for the page to load (wait for search results)
        time.sleep(5)
        
        # Check if we see search results or login page
        if "login" in driver.current_url:
            print("Warning: Authentication verification failed. Please check your credentials.")
        else:
            print("Authentication verified successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Close the browser
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save LinkedIn cookies for web scraping")
    parser.add_argument("--username", "-u", required=True, help="LinkedIn username/email")
    parser.add_argument("--password", "-p", required=True, help="LinkedIn password")
    parser.add_argument("--output", "-o", default="linkedin_cookies.json", help="Output file path")
    
    args = parser.parse_args()
    
    save_cookies(args.username, args.password, args.output) 