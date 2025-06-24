import scrapy
import re
from ..items import ElectionResultItem

class StateSpider(scrapy.Spider):
    name = 'state_elections'
    allowed_domains = ['270towin.com']
    start_urls = ['https://www.270towin.com/states/']

    def parse(self, response):
        """
        This method finds all state links from the main /states/ page.
        This selector is confirmed correct from your previously provided HTML.
        """
        self.logger.info(f"Parsing index page: {response.url}")
        # The selector 'a.state-wrapper' is for the main states index page.
        links = response.css('a.state-wrapper::attr(href)').getall()
        if not links:
            self.logger.error(f"FATAL: Could not find any state links on {response.url} using 'a.state-wrapper'. The main index page has changed.")
            return

        self.logger.info(f"Found {len(links)} state links. Following each...")
        for href in links:
            yield response.follow(href, self.parse_state_page)

    def parse_state_page(self, response):
        """
        This method is called for each individual state page (e.g., /states/alabama).
        It extracts the election results and yields the final data items.
        """
        state_name = response.css('h1.page-title::text').get()
        if not state_name:
            # Fallback for pages that might have a different h1 structure
            state_name = response.xpath("//div[@id='primary']//h1/text()").get()

        state_name = state_name.strip() if state_name else "Unknown State"
        self.logger.info(f"Parsing detail page for: '{state_name}' at {response.url}")

        # --- THE CORRECT ELECTORAL VOTE SELECTOR ---
        # It's a span with a specific style attribute.
        ev_text = response.css('span[style*="font-size:4em"] strong::text').get()
        electoral_votes = int(ev_text) if ev_text and ev_text.isdigit() else None
        self.logger.info(f"Found Electoral Votes for {state_name}: {electoral_votes}")

        results_table = response.css('table#recent_elections')
        if not results_table:
            self.logger.error(f"Could not find results table #recent_elections on {response.url}")
            return

        for row in results_table.css('tr.toggle-row'):
            # The year is no longer in an <a> tag in the provided HTML
            year_text = row.css('td:first-child::text').get()
            if not year_text or not year_text.strip().isdigit():
                self.logger.warning(f"Skipping row, could not parse year from: {row.css('td:first-child').get()}")
                continue

            year = int(year_text.strip())

            # --- THE CORRECT PERCENTAGE SELECTORS ---
            # Use the fill-d* and fill-r* classes which are more reliable
            dem_pct_text = row.css('td[class*="fill-d"]::text').get()
            rep_pct_text = row.css('td[class*="fill-r"]::text').get()

            dem_pct = self._parse_percentage(dem_pct_text)
            rep_pct = self._parse_percentage(rep_pct_text)

            self.logger.debug(f"  Year {year}: DEM {dem_pct}% | REP {rep_pct}%")

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
                state_winner=winner,
            )
            self.logger.info(f"SUCCESS: Yielding item for {state_name} - {year}")
            yield item

    def _parse_percentage(self, text: str) -> float | None:
        """Helper to robustly parse percentage strings into floats."""
        if not text: return None
        # The text is like "34.1%", so we find the number.
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None