BOT_NAME = "LinkedinScraper"

SPIDER_MODULES = ["LinkedinScraper.spiders"]
NEWSPIDER_MODULE = "LinkedinScraper.spiders"

# Crawl responsibly by identifying yourself on the user agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 5
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 1
CONCURRENT_REQUESTS_PER_IP = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# LinkedIn authentication
LINKEDIN_COOKIES_FILE = "linkedin_cookies.json"

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# Enable showing throttling stats for every response received
AUTOTHROTTLE_DEBUG = False

# Configure item pipelines
ITEM_PIPELINES = {
    "LinkedinScraper.pipelines.LinkedinScraperPipeline": 300,
    "LinkedinScraper.pipelines.CsvExportPipeline": 400,
}

# Enable middlewares
DOWNLOADER_MIDDLEWARES = {
    'LinkedinScraper.middlewares.RotateUserAgentMiddleware': 400,
    'LinkedinScraper.middlewares.LinkedinAuthenticationMiddleware': 401,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'LinkedinScraper.middlewares.LinkedinScraperDownloaderMiddleware': 500,
}

SPIDER_MIDDLEWARES = {
    'LinkedinScraper.middlewares.LinkedinScraperSpiderMiddleware': 543,
}

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8" 