import scrapy


class LinkedinUserItem(scrapy.Item):
    # Profile URL
    url = scrapy.Field()
    
    # Basic information
    name = scrapy.Field()
    title = scrapy.Field()
    location = scrapy.Field()
    summary = scrapy.Field()
    
    # Experience (list of dictionaries)
    experience = scrapy.Field() 