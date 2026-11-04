from config.settings import settings
from src.pages.base_page import BasePage
from src.pages.search_results_page import SearchResultsPage


class HomePage(BasePage):
    SEARCH_INPUT = "#gh-ac"
    SEARCH_BUTTON = "#gh-search-btn"

    def open(self) -> "HomePage":
        return super().open(settings.base_url)

    def search(self, query: str) -> SearchResultsPage:
        self.log.info("Search for '%s'", query)
        self.page.locator(self.SEARCH_INPUT).fill(query)
        self.page.locator(self.SEARCH_BUTTON).click()
        self.page.wait_for_load_state("domcontentloaded")
        return SearchResultsPage(self.page).wait_loaded()
