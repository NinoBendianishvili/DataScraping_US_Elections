import scrapy

class ElectionResultItem(scrapy.Item):
    # Defines the fields for our item
    state_name = scrapy.Field()
    electoral_votes = scrapy.Field()
    year = scrapy.Field()
    dem_state_percentage = scrapy.Field()
    rep_state_percentage = scrapy.Field()
    state_winner = scrapy.Field()