from scrapy import signals
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
import random
import logging
import json
import os


class RotateUserAgentMiddleware(UserAgentMiddleware):
    """
    Middleware to rotate user agents to avoid detection
    """
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
    ]
    
    def __init__(self, user_agent=''):
        self.user_agent = user_agent
        self.logger = logging.getLogger(__name__)
    
    def process_request(self, request, spider):
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        self.logger.debug(f"Using User-Agent: {user_agent}")


class LinkedinAuthenticationMiddleware:
    """
    Middleware to handle LinkedIn authentication using cookies
    """
    
    def __init__(self, cookies_file=None):
        self.logger = logging.getLogger(__name__)
        self.cookies_file = cookies_file or 'linkedin_cookies.json'
        self.cookies = None
        self._load_cookies()
    
    @classmethod
    def from_crawler(cls, crawler):
        cookies_file = crawler.settings.get('LINKEDIN_COOKIES_FILE')
        return cls(cookies_file)
    
    def _load_cookies(self):
        """Load cookies from file"""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'r') as f:
                    self.cookies = json.load(f)
                self.logger.info(f"Loaded cookies from {self.cookies_file}")
            else:
                self.logger.warning(f"Cookies file {self.cookies_file} not found")
        except Exception as e:
            self.logger.error(f"Error loading cookies: {e}")
    
    def process_request(self, request, spider):
        """Add cookies to request if available"""
        if self.cookies:
            for cookie in self.cookies:
                request.cookies[cookie['name']] = cookie['value']
            self.logger.debug("Added authentication cookies to request")
        else:
            self.logger.warning("No cookies available for authentication")


class LinkedinScraperSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # raises an exception.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn't have a response associated.
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class LinkedinScraperDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name) 