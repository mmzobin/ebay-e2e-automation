import allure
from playwright.sync_api import Page

from config.settings import settings
from src.pages.home_page import HomePage
from src.utils.logger import get_logger


class SearchService:
    def __init__(self, page: Page):
        self.page = page
        self.log = get_logger("SearchService")

    @allure.step("Search '{query}' with price <= {max_price}, limit {limit}")
    def search_items_by_name_under_price(self, query: str, max_price: float, limit: int = 5) -> list[str]:
        """Returns up to `limit` urls with price <= max_price. Fewer (or 0) is ok."""
        results = (
            HomePage(self.page).open()
            .search(query)
            .apply_max_price_filter(max_price)
            .show_buy_it_now_only()
        )
        urls: list[str] = []
        page_number = 1
        while True:
            for item in results.get_items():
                if item.price is not None and item.price <= max_price and item.url not in urls:
                    urls.append(item.url)
                    self.log.info("Match #%d: %s | %s | %s", len(urls), item.price, item.title[:60], item.url)
                    if len(urls) == limit:
                        return urls
            if page_number >= settings.max_pages or not results.has_next_page():
                break
            results.go_to_next_page()
            page_number += 1
        self.log.info("Found %d of %d requested items (pages scanned: %d)", len(urls), limit, page_number)
        return urls
