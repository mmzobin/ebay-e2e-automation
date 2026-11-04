from src.pages.base_page import BasePage
from src.utils.price_parser import parse_price


class CartPage(BasePage):
    URL = "https://cart.ebay.com/"
    SUBTOTAL = "[data-test-id='SUBTOTAL']"
    ITEM_LINKS = "[data-test-id='cart-item-link']"

    def open(self) -> "CartPage":
        return super().open(self.URL)

    def get_subtotal_text(self) -> str | None:
        subtotal = self.page.locator(self.SUBTOTAL).first
        return subtotal.inner_text().strip() if subtotal.count() else None

    def get_subtotal(self) -> float:
        # empty cart has no subtotal at all
        return parse_price(self.get_subtotal_text()) or 0.0

    def get_items_count(self) -> int:
        hrefs = self.page.locator(self.ITEM_LINKS).evaluate_all("els => els.map(e => e.href.split('?')[0])")
        return len(set(hrefs))
