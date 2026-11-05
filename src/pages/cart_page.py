from playwright.sync_api import expect

from src.pages.base_page import BasePage
from src.utils.price_parser import parse_price


class CartPage(BasePage):
    URL = "https://cart.ebay.com/"
    SUBTOTAL = "[data-test-id='SUBTOTAL']"
    ITEMS = "[data-test-id='cart-bucket']"

    def open(self) -> "CartPage":
        return super().open(self.URL)

    def get_subtotal(self) -> float:
        subtotal = self.page.locator(self.SUBTOTAL).first
        # cart is drawn by js - without waiting we could read "nothing" and take it as 0
        expect(subtotal).to_be_visible()
        text = subtotal.inner_text().strip()
        price = parse_price(text)
        assert price is not None, f"Can't parse cart subtotal: '{text}'"
        self.log.info("Cart subtotal: %s", text)
        return price
