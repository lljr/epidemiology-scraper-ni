import scrapy
from mapaminsa.items import MinsaItem
from scrapy.loader import ItemLoader
import re


class MinsaSpider(scrapy.Spider):
    name = 'minsa'
    start_urls = ['http://mapasalud.minsa.gob.ni/']

    def get_map_links(self, response):
        """Function extracts and cleans links from 'onclick' svg attribute."""
        url_string_blobs = response.css('svg g[onclick]::attr(onclick)')\
                                   .getall()
        url_strings = []
        for dirty_url in url_string_blobs:
            clean_url = re.search("(?P<url>https?://[^\s]+)", dirty_url)
            url_strings.append(clean_url.group("url")[:-2])  # remove "'", ";",

        yield from response.follow_all(url_strings,
                                       callback=self.parse,
                                       encoding="utf-8")

    def parse(self, response):
        # Sanitizing location string
        location = ""
        location_match_object = re.search(r"salud-.*", response.url)
        if location_match_object is not None:
            location = location_match_object.group(0)[:-1]
            location = location.split("-")[1:]
            location = "_".join(location)

        for table in response.css('.tab-pane'):
            item = ItemLoader(item=MinsaItem(), selector=table)
            item.add_value("location", location)
            item.add_css('title', '.tab-pane::attr(id)')
            item.add_css('year', '.tab-pane::attr(id)')
            item.add_css('data', '.tab-pane table')
            yield item.load_item()

        iframe_url = response.css('iframe::attr(src)').get()
        if iframe_url is not None:
            yield response.follow(iframe_url,
                                  self.get_map_links,
                                  encoding="utf-8")
