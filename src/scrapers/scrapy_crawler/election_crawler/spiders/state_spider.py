# src/scrapers/scrapy_crawler/election_crawler/spiders/state_spider.py
import scrapy
import re
from ..items import ElectionResultItem

class StateSpider(scrapy.Spider):
    name = 'state_elections'
    allowed_domains = ['270towin.com']
    start_urls = ['https://www.270towin.com/states/']

    def parse(self, response):
        """
        Finds all state page links and yields new requests to be followed.
        """
        # --- FIX: Use a single, more specific selector to get the links ---
        # This selects all <a> tags that are descendants of the table.
        links = response.css('table.states-table a')

        for link in links:
            # We get the href attribute from the link selector object
            href = link.attrib.get('href')
            if href and href.startswith('/states/'):
                yield response.follow(href, self.parse_state_page)

    def parse_state_page(self, response):
        """
        Extracts election results from an individual state page.
        """
        state_name = response.css('h1.page-title::text').get('').strip()

        # This selector is correct.
        ev_text = response.css('div.ev-display::text').re_first(r'(\d+)\s+ELECTORAL')
        electoral_votes = int(ev_text) if ev_text else None

        results_table = response.css('table#recent_elections')
        for row in results_table.css('tr.toggle-row'):
            year_text = row.css('td:first-child a::text').get()
            if not year_text or not year_text.isdigit():
                continue

            year = int(year_text)

            dem_pct_text = row.css('td:nth-child(2) table tr td:nth-child(1)::text').get()
            rep_pct_text = row.css('td:nth-child(2) table tr td:nth-child(3)::text').get()

            dem_pct = self._parse_percentage(dem_pct_text)
            rep_pct = self._parse_percentage(rep_pct_text)

            winner = None
            if dem_pct is not None and rep_pct is not None:
                if dem_pct > rep_pct: winner = "Democratic"
                elif rep_pct > dem_pct: winner = "Republican"
                else: winner = "Other"

            item = ElectionResultItem(
                state_name=state_name,
                electoral_votes=electoral_votes,
                year=year,
                dem_state_percentage=dem_pct,
                rep_state_percentage=rep_pct,
                state_winner=winner
            )
            yield item

    def _parse_percentage(self, text: str) -> float | None:
        """Helper to robustly parse percentage strings into floats."""
        if not text: return None
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None