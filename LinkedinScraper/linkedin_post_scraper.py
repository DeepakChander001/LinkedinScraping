import json
import csv
import time
import random
import os
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urlparse

class LinkedInPostScraper:
    def __init__(self, headless=False):
        self.output_dir = 'output'
        self.posts = []
        self.existing_posts = self._load_existing_posts()
        
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
        
        # Initialize the driver
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
    
    def _load_existing_posts(self):
        """Load existing posts from the most recent JSON file"""
        try:
            # Get the most recent JSON file
            json_files = [f for f in os.listdir(self.output_dir) if f.startswith('linkedin_posts_') and f.endswith('.json')]
            if not json_files:
                return []
            
            latest_file = max(json_files, key=lambda x: os.path.getctime(os.path.join(self.output_dir, x)))
            with open(os.path.join(self.output_dir, latest_file), 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading existing posts: {e}")
            return []
    
    def _is_post_new(self, post_data):
        """Check if a post is already in the existing posts"""
        for existing_post in self.existing_posts:
            # Compare captions to check if it's the same post
            if post_data.get('caption') == existing_post.get('caption'):
                return False
        return True
    
    def login(self):
        """Log in to LinkedIn"""
        try:
            # Replace with your LinkedIn credentials
            email = "example@gmail.com"
            password = "password@123"
            
            # Navigate to LinkedIn login page
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(5)
            
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
            
            # Wait for login to complete
            time.sleep(10)
            
            # Verify login was successful
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: "feed" in driver.current_url
                )
                print("Login successful")
                return True
            except TimeoutException:
                print("Login verification failed")
                return False
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def scrape_posts(self, profile_url, max_posts=5):
        """Scrape posts from a LinkedIn profile"""
        try:
            # Navigate to profile's activity page
            activity_url = f"{profile_url}/recent-activity/all/"
            print(f"Navigating to URL: {activity_url}")
            self.driver.get(activity_url)
            time.sleep(random.uniform(3, 5))
            
            # Wait for posts to load
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.feed-shared-update-v2"))
                )
                print("Posts container found")
            except TimeoutException:
                print("Could not find posts container")
                return False
            
            # Scroll to load more posts
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            posts_scraped = 0
            scroll_attempts = 0
            max_scroll_attempts = 3  # Reduced since we only need 5 posts
            
            while posts_scraped < max_posts and scroll_attempts < max_scroll_attempts:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(2, 3))
                
                # Find all posts using multiple selectors
                posts = self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2, div.update-components-update-v2")
                print(f"Found {len(posts)} posts after scroll {scroll_attempts + 1}")
                
                # Process each post
                for post in posts:
                    if posts_scraped >= max_posts:
                        break
                    
                    try:
                        post_data = self._extract_post_data(post)
                        if post_data and self._is_post_new(post_data):
                            self.posts.append(post_data)
                            posts_scraped += 1
                            print(f"Scraped new post {posts_scraped}/{max_posts}")
                        else:
                            print("Post already exists, skipping...")
                    except Exception as e:
                        print(f"Error processing post: {e}")
                        continue
                
                # Check if we've reached the bottom
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                    if scroll_attempts >= max_scroll_attempts:
                        print("Reached maximum scroll attempts")
                        break
                last_height = new_height
            
            if self.posts:
                # Save the data
                self._save_data()
                return True
            else:
                print("No new posts found to scrape")
                return False
            
        except Exception as e:
            print(f"Error scraping posts: {e}")
            return False
    
    def _extract_post_data(self, post_element):
        """Extract data from a single post"""
        try:
            post_data = {}
            
            # Get post time
            try:
                # Find the time element using the exact class
                time_element = post_element.find_element(By.CSS_SELECTOR, "span.update-components-actor__sub-description span[aria-hidden='true']")
                time_text = time_element.text.strip()
                # Extract just the time part (e.g., "1d")
                post_data['post_time'] = time_text.split('•')[0].strip()
                print(f"Found post time: {post_data['post_time']}")
            except:
                try:
                    # Fallback to the visually-hidden span
                    time_element = post_element.find_element(By.CSS_SELECTOR, "span.visually-hidden")
                    time_text = time_element.text.strip()
                    # Extract just the time part (e.g., "1d")
                    post_data['post_time'] = time_text.split('•')[0].strip()
                    print(f"Found post time: {post_data['post_time']}")
                except:
                    post_data['post_time'] = "Not found"
                    print("Could not find post time")
            
            # Get likes count
            try:
                likes_element = post_element.find_element(By.CSS_SELECTOR, "span.social-details-social-counts__reactions-count")
                post_data['likes'] = likes_element.text.strip()
                print(f"Found likes: {post_data['likes']}")
            except:
                post_data['likes'] = "0"
                print("Could not find likes count")
            
            # Get comments count
            try:
                comments_button = post_element.find_element(By.CSS_SELECTOR, "button.social-details-social-counts__btn")
                comments_text = comments_button.get_attribute("aria-label")
                # Extract just the number from "1 comment" or "2 comments"
                post_data['comments'] = comments_text.split()[0]
                print(f"Found comments: {post_data['comments']}")
            except:
                try:
                    # Alternative selector for comments
                    comments_element = post_element.find_element(By.CSS_SELECTOR, "span.social-details-social-counts__comments")
                    comments_text = comments_element.text.strip()
                    post_data['comments'] = comments_text.split()[0]
                    print(f"Found comments: {post_data['comments']}")
                except:
                    post_data['comments'] = "0"
                    print("Could not find comments count")
            
            # Get caption
            try:
                caption_element = post_element.find_element(By.CSS_SELECTOR, "div.feed-shared-update-v2__description-wrapper span[dir='ltr'], div.update-components-text span[dir='ltr']")
                post_data['caption'] = caption_element.text.strip()
                print(f"Found caption: {post_data['caption'][:50]}...")
            except:
                post_data['caption'] = "Not found"
                print("Could not find caption")
            
            # Get images
            try:
                image_elements = post_element.find_elements(By.CSS_SELECTOR, "img.feed-shared-image__image, img.update-components-image__image")
                post_data['images'] = []
                
                for img in image_elements:
                    img_url = img.get_attribute("src")
                    if img_url:
                        post_data['images'].append(img_url)
                        print(f"Found image URL: {img_url}")
                        
                        # Download image
                        self._download_image(img_url)
            except:
                post_data['images'] = []
                print("Could not find images")
            
            return post_data
            
        except Exception as e:
            print(f"Error extracting post data: {e}")
            return None
    
    def _download_image(self, img_url):
        """Download and save an image"""
        try:
            # Create images directory if it doesn't exist
            images_dir = os.path.join(self.output_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Get filename from URL
            filename = os.path.basename(urlparse(img_url).path)
            if not filename:
                filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Download image
            response = requests.get(img_url)
            if response.status_code == 200:
                with open(os.path.join(images_dir, filename), 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded image: {filename}")
            
        except Exception as e:
            print(f"Error downloading image: {e}")
    
    def _save_data(self):
        """Save scraped data to JSON and CSV files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Combine existing and new posts
            all_posts = self.existing_posts + self.posts
            
            # Save to JSON
            json_file = os.path.join(self.output_dir, f'linkedin_posts_{timestamp}.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(all_posts, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(all_posts)} posts to JSON: {json_file}")
            
            # Save to CSV
            csv_file = os.path.join(self.output_dir, f'linkedin_posts_{timestamp}.csv')
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write header
                writer.writerow(['Post Time', 'Likes', 'Comments', 'Caption', 'Images'])
                # Write data rows
                for post in all_posts:
                    writer.writerow([
                        post.get('post_time', ''),
                        post.get('likes', '0'),
                        post.get('comments', '0'),
                        post.get('caption', ''),
                        ', '.join(post.get('images', []))
                    ])
            print(f"Saved {len(all_posts)} posts to CSV: {csv_file}")
            
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def close(self):
        """Close the browser"""
        self.driver.quit()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Post Scraper')
    parser.add_argument('--profile-url', help='LinkedIn profile URL', required=True)
    parser.add_argument('--max-posts', type=int, default=5, help='Maximum number of posts to scrape')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    scraper = LinkedInPostScraper(headless=args.headless)
    
    try:
        if scraper.login():
            print(f"Starting to scrape posts from: {args.profile_url}")
            success = scraper.scrape_posts(args.profile_url, max_posts=args.max_posts)
            if success:
                print(f"Successfully scraped {len(scraper.posts)} posts")
            else:
                print("Failed to scrape posts")
        else:
            print("Failed to login to LinkedIn")
    finally:
        scraper.close() 