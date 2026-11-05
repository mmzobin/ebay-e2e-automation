from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.sync_api import Locator

from src.models.search import SearchResultItem
from src.pages.base_page import BasePage
from src.utils.price_parser import parse_price


class SearchResultsPage(BasePage):
    # s-card = current layout, s-item = old one.
    # first card "Shop on eBay" is an ad with a fake /itm/ link - it has no data-item-pos
    ITEM_CARDS_XPATH = (
        "//li[contains(concat(' ', normalize-space(@class), ' '), ' s-card ')][@data-item-pos]"
        "[.//a[contains(@href, '/itm/')]]"
        " | //li[contains(concat(' ', normalize-space(@class), ' '), ' s-item ')]"
        "[.//a[contains(@href, '/itm/')]][not(.//*[normalize-space(text())='Shop on eBay'])]"
    )
    CARD_LINK_XPATH = ".//a[contains(@href, '/itm/')]"
    # first span only, there is also hidden text "Opens in a new window or tab"
    CARD_TITLE_XPATH = "(.//*[contains(@class, 's-card__title') or contains(@class, 's-item__title')]//span)[1]"
    # range price comes as 3 spans: "ILS 10", " to ", "ILS 25".
    # reading only these spans, so the crossed-out old price is ignored
    CARD_PRICE_XPATH = ".//*[contains(@class, 's-card__price') or contains(@class, 's-item__price')]"

    MAX_PRICE_INPUT = "input[type='text'][aria-label^='Maximum Value']"
    PRICE_SUBMIT = "button[title='Submit price range']"

    @property
    def next_page_link(self):
        # on the last page "next" is a disabled <button>, not a link, so it won't match
        return self.page.get_by_role("link", name="Go to next search page")

    def wait_loaded(self) -> "SearchResultsPage":
        self.ensure_not_blocked()
        self.page.locator(f"xpath={self.ITEM_CARDS_XPATH}").first.wait_for()
        return self

    def apply_max_price_filter(self, max_price: float) -> "SearchResultsPage":
        # if there is no filter on the page - use the url param instead
        max_input = self.page.locator(self.MAX_PRICE_INPUT).first
        if max_input.count() and max_input.is_visible():
            self.log.info("Apply price filter via UI: max=%s", max_price)
            max_input.fill(str(int(max_price)))
            self.page.locator(self.PRICE_SUBMIT).first.click()
            self.page.wait_for_url("**_udhi=*")
        else:
            self.log.info("Price filter not found on page -> URL parameter _udhi=%s", max_price)
            self.page.goto(self._url_with(_udhi=int(max_price)), wait_until="domcontentloaded")
        return self.wait_loaded()

    def show_buy_it_now_only(self) -> "SearchResultsPage":
        # auctions have only "Place bid", no "Add to cart" - so fixed price items only.
        # tab link is built by eBay from current url, so the price filter stays
        tab = self.page.get_by_role("link", name="Buy It Now", exact=True).first
        if tab.count() and tab.is_visible():
            self.log.info("Filter: Buy It Now")
            tab.click()
            self.page.wait_for_url("**LH_BIN=1*")
        else:
            self.log.info("Buy It Now tab not found -> URL parameter LH_BIN=1")
            self.page.goto(self._url_with(LH_BIN=1), wait_until="domcontentloaded")
        return self.wait_loaded()

    def _url_with(self, **params) -> str:
        parts = urlsplit(self.page.url)
        query = dict(parse_qsl(parts.query))
        query.update({k: str(v) for k, v in params.items()})
        return urlunsplit(parts._replace(query=urlencode(query)))

    def get_items(self) -> list[SearchResultItem]:
        cards = self.page.locator(f"xpath={self.ITEM_CARDS_XPATH}")
        items = [self._parse_card(cards.nth(i)) for i in range(cards.count())]
        self.log.info("Parsed %d product cards on %s", len(items), self.page.url)
        return items

    def _parse_card(self, card: Locator) -> SearchResultItem:
        href = card.locator(f"xpath={self.CARD_LINK_XPATH}").first.get_attribute("href") or ""
        title_el = card.locator(f"xpath={self.CARD_TITLE_XPATH}").first
        title = title_el.inner_text().strip() if title_el.count() else ""
        price_text = " ".join(card.locator(f"xpath={self.CARD_PRICE_XPATH}").all_inner_texts())
        return SearchResultItem(title=title, url=href.split("?")[0], price=parse_price(price_text))

    def has_next_page(self) -> bool:
        next_link = self.next_page_link
        return next_link.count() > 0 and next_link.get_attribute("aria-disabled") != "true"

    def go_to_next_page(self) -> "SearchResultsPage":
        self.log.info("Go to next results page")
        self.next_page_link.click()
        self.page.wait_for_load_state("domcontentloaded")
        return self.wait_loaded()
