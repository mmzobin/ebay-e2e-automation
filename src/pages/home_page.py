from config.settings import settings
from src.pages.base_page import BasePage
from src.pages.search_results_page import SearchResultsPage


class HomePage(BasePage):
    @property
    def search_input(self):
        return self.page.get_by_role("combobox", name="Search for anything")

    @property
    def search_button(self):
        return self.page.get_by_role("button", name="Search", exact=True)

    def open(self) -> "HomePage":
        return super().open(settings.base_url)

    def search(self, query: str) -> SearchResultsPage:
        self.log.info("Search for '%s'", query)
        self.search_input.fill(query)
        self.search_button.click()
        self.page.wait_for_load_state("domcontentloaded")
        return SearchResultsPage(self.page).wait_loaded()
