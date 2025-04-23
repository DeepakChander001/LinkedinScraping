from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import argparse
import os
import sys

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_spider(domain):
    """Run the LinkedIn spider with the specified domain."""
    from LinkedinScraper.spiders.linkedin_spider import LinkedinSpider
    
    # Get project settings
    settings = get_project_settings()
    
    # Create and configure the crawler process
    process = CrawlerProcess(settings)
    
    # Add the spider to the process
    process.crawl(LinkedinSpider, domain=domain)
    
    # Start the crawling process
    process.start()  # This will block until the crawling is finished

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run LinkedIn scraper with a specific domain')
    parser.add_argument('domain', type=str, help='Domain to search for on LinkedIn (e.g., "AI Engineer")')
    args = parser.parse_args()
    
    print(f"Starting LinkedIn scraper for domain: {args.domain}")
    run_spider(args.domain) 