import scrapy
import json
import re
from LinkedinScraper.items import LinkedinUserItem
from scrapy.http import Request
from urllib.parse import urlencode


class LinkedinSpider(scrapy.Spider):
    name = 'linkedin'
    allowed_domains = ['linkedin.com']
    
    # Custom settings for this spider
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'COOKIES_ENABLED': True,
    }
    
    def __init__(self, domain=None, *args, **kwargs):
        super(LinkedinSpider, self).__init__(*args, **kwargs)
        self.domain = domain or "AI Engineer"  # Default search domain
        
    def start_requests(self):
        """
        Start with a search for the specified domain
        """
        self.logger.info(f"Starting search for domain: {self.domain}")
        
        # Search URL for LinkedIn
        encoded_keywords = urlencode({'keywords': self.domain})
        search_url = f"https://www.linkedin.com/search/results/people/?{encoded_keywords}"
        
        yield Request(
            url=search_url,
            callback=self.parse_search_results,
            meta={'domain': self.domain}
        )
    
    def parse_search_results(self, response):
        """
        Parse the search results page to extract profile links
        """
        self.logger.info(f"Parsing search results for domain: {response.meta['domain']}")
        
        try:
            # Safe way to check URL without relying on response.css
            if "login" in response.url or "auth/login" in response.url or "uas/login" in response.url:
                self.logger.error("Authentication failed. Please check your cookies file.")
                self.logger.error(f"Redirected to: {response.url}")
                return
            
            # Save the HTML for debugging
            with open('linkedin_search_response.html', 'wb') as f:
                f.write(response.body)
            self.logger.info("Saved response HTML to linkedin_search_response.html for debugging")
            
            # Extract profile links using basic string operations to avoid encoding issues
            response_text = response.body.decode('utf-8', errors='ignore')
            
            # Log a sample of the HTML for debugging
            sample = response_text[:1000]  # First 1000 characters
            self.logger.info(f"HTML sample: {sample}")
            
            # Find profile URLs using multiple patterns
            profile_links = []
            
            # Pattern 1: Standard href to profile
            pattern1 = re.compile(r'href=[\'"](?:https?://)?(?:www\.)?linkedin\.com(/in/[^"\']*)[\'"]+')
            matches1 = pattern1.findall(response_text)
            self.logger.info(f"Pattern 1 matches: {len(matches1)}")
            
            # Pattern 2: Relative links
            pattern2 = re.compile(r'href=[\'"](/in/[^"\']*)[\'"]+')
            matches2 = pattern2.findall(response_text)
            self.logger.info(f"Pattern 2 matches: {len(matches2)}")
            
            # Pattern 3: Another common format
            pattern3 = re.compile(r'href=\\\\?"(/in/[^\\\\"]+)\\\\?"')
            matches3 = pattern3.findall(response_text)
            self.logger.info(f"Pattern 3 matches: {len(matches3)}")
            
            # Combine all matches
            all_matches = matches1 + matches2 + matches3
            
            # Add found URLs to our list
            for match in all_matches:
                # Clean up the URL
                clean_url = match.split('?')[0]  # Remove query parameters
                if clean_url not in profile_links:
                    profile_links.append(clean_url)
            
            self.logger.info(f"Found {len(profile_links)} profiles to scrape: {profile_links[:5]}")
            
            # Visit each profile
            for profile_url in profile_links:
                # Ensure we have the full URL
                if not profile_url.startswith('http'):
                    profile_url = f"https://www.linkedin.com{profile_url}"
                
                self.logger.info(f"Scheduling profile: {profile_url}")
                yield Request(
                    url=profile_url,
                    callback=self.parse_profile,
                )
            
            # Check for pagination and follow next page
            next_page = response.xpath('//button[contains(@aria-label, "Next")]/@href').get()
            if next_page:
                yield Request(
                    url=response.urljoin(next_page),
                    callback=self.parse_search_results,
                    meta={'domain': response.meta['domain']}
                )
                
        except Exception as e:
            self.logger.error(f"Error processing search results: {str(e)}")
            # Save the HTML for debugging
            with open('linkedin_error_response.html', 'wb') as f:
                f.write(response.body)
            self.logger.error("Saved error response to linkedin_error_response.html")
    
    def parse_profile(self, response):
        """
        Parse an individual LinkedIn profile to extract user data
        """
        self.logger.info(f"Parsing profile: {response.url}")
        
        try:
            # Check if we're logged in and can access the profile
            if "auth/login" in response.url or "uas/login" in response.url:
                self.logger.error("Authentication failed when accessing profile. Please check your cookies.")
                return
            
            # Save the profile HTML for debugging
            with open('linkedin_profile_response.html', 'wb') as f:
                f.write(response.body)
            self.logger.info("Saved profile response to linkedin_profile_response.html")
            
            item = LinkedinUserItem()
            
            # Extract basic information
            item['url'] = response.url
            
            # Extract name
            item['name'] = self.extract_name(response)
            self.logger.info(f"Extracted name: {item['name']}")
            
            # Extract title/headline
            item['title'] = self.extract_title(response)
            self.logger.info(f"Extracted title: {item['title']}")
            
            # Extract location
            item['location'] = self.extract_location(response)
            self.logger.info(f"Extracted location: {item['location']}")
            
            # Extract summary
            item['summary'] = self.extract_summary(response)
            
            # Extract experience details
            item['experience'] = self.extract_experience(response)
            self.logger.info(f"Extracted {len(item['experience'])} experience items")
            
            return item
            
        except Exception as e:
            self.logger.error(f"Error processing profile {response.url}: {str(e)}")
            # Save the HTML for debugging
            with open('linkedin_profile_error.html', 'wb') as f:
                f.write(response.body)
            self.logger.error("Saved profile error response to linkedin_profile_error.html")
    
    def extract_name(self, response):
        """Extract name from profile"""
        # Try various selectors based on the HTML structure provided
        selectors = [
            'h1.oBETlcohuWevkUfWDhTfZwaGdnmMtHYnHwZ::text', 
            'h1.text-heading-xlarge::text',
            'h1.inline.t-24::text',
            'h1.vDzVOEZNeMKylKcKaNYHHwtjAYZncUQaHAXY::text',
            'span.ZbzRjoSntypyNirWLBEUMfKJSZdpNCMkzswQ span.t-16 a span::text'
        ]
        
        for selector in selectors:
            name = response.css(selector).get()
            if name:
                return name.strip()
        
        return None
    
    def extract_title(self, response):
        """Extract professional title/headline"""
        # Try various selectors based on the HTML structure provided
        selectors = [
            'div.text-body-medium::text',
            'div.KlNYbwvtpVleCIAlSVxATnZQdaLhHlVndFyBFk::text'
        ]
        
        for selector in selectors:
            title = response.css(selector).get()
            if title:
                return title.strip()
        
        return None
    
    def extract_location(self, response):
        """Extract location information"""
        # Try various selectors based on the HTML structure provided
        selectors = [
            'span.text-body-small.inline::text',
            'div.tsrbCGLJiTMIIXWSjYgkxHeRpkdUdpBKsD::text'
        ]
        
        for selector in selectors:
            location = response.css(selector).get()
            if location:
                return location.strip()
        
        return None
    
    def extract_summary(self, response):
        """Extract profile summary/about section"""
        # Try various selectors based on the HTML structure provided
        selectors = [
            'div.pv-about-section .pv-shared-text-with-see-more::text',
            'p.uWkDXkOBbsnmfrrwgRflIjjWveWUqzwpBkE::text'
        ]
        
        for selector in selectors:
            summary_parts = response.css(selector).getall()
            if summary_parts:
                return ''.join(summary_parts).strip()
        
        return None
    
    def extract_experience(self, response):
        """Extract experience details"""
        experiences = []
        
        # Try to find all experience sections using different selectors
        experience_items = response.css('li.artdeco-list__item, div.bvCwMXcVdlosVVcMnnOtWjKSzrihCZfARvf')
        
        for exp in experience_items:
            # Try different selectors for role
            role_selectors = [
                'div.display-flex.align-items-center.mr1.hoverable-link-text.t-bold::text',
                'div.display-flex.align-items-center.mr1.t-bold::text'
            ]
            
            role = None
            for selector in role_selectors:
                role = exp.css(selector).get()
                if role:
                    role = role.strip()
                    break
            
            if not role:
                continue
                
            # Try different selectors for company
            company_selectors = [
                'span.t-14.t-normal::text',
                'span.t-14.t-normal a span::text'
            ]
            
            company = None
            for selector in company_selectors:
                company_text = exp.css(selector).get()
                if company_text:
                    # Company text might contain additional info separated by '·'
                    company = company_text.split('·')[0].strip()
                    break
            
            # Try different selectors for date range
            date_selectors = [
                'span.t-14.t-normal.t-black--light .pvs-entity__caption-wrapper::text',
                'span.t-14.t-normal.t-black--light::text'
            ]
            
            date_range = None
            for selector in date_selectors:
                date_range = exp.css(selector).get()
                if date_range:
                    break
            
            # Parse dates and duration
            start_date = None
            end_date = None
            duration = None
            
            if date_range:
                # Extract dates and duration from the date_range text
                date_parts = date_range.split('·')
                if len(date_parts) >= 1:
                    dates = date_parts[0].strip()
                    
                    # Pattern like "Jan 2023 - Present"
                    date_match = re.search(r'(\w+ \d{4}) - (\w+ \d{4}|\w+)', dates)
                    if date_match:
                        start_date = date_match.group(1)
                        end_date = date_match.group(2)
                
                # Extract duration if available
                if len(date_parts) >= 2:
                    duration_text = date_parts[1].strip()
                    duration = duration_text
            
            # Try different selectors for description
            desc_selectors = [
                'div.inline-show-more-text--is-collapsed::text',
                'div.guoMOndwQfrqcNISpQhIvArpasFrRno::text',
                'div.ebFElzMcESSQzCWjCYCOuunyVnfSjQw::text'
            ]
            
            description = None
            for selector in desc_selectors:
                desc_text = exp.css(selector).get()
                if desc_text:
                    description = desc_text.strip()
                    break
            
            experience_entry = {
                'role': role,
                'company': company,
                'start_date': start_date,
                'end_date': end_date,
                'duration': duration,
                'description': description
            }
            
            experiences.append(experience_entry)
        
        return experiences 