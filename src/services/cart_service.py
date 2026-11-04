import allure
from playwright.sync_api import Page

from src.pages.cart_page import CartPage
from src.pages.item_page import ItemPage
from src.utils.logger import get_logger
from src.utils.reporting import attach_screenshot


class CartService:
    def __init__(self, page: Page):
        self.page = page  # the search tab
        self.log = get_logger("CartService")

    @allure.step("Add items to cart")
    def add_items_to_cart(self, urls: list[str]) -> None:
        for index, url in enumerate(urls, start=1):
            with allure.step(f"Add item {index}/{len(urls)}: {url}"):
                item_tab = self.page.context.new_page()  # item opens in its own tab, as on eBay
                item_page = ItemPage(item_tab).open(url)
                item_page.select_random_variants()
                item_page.add_to_cart()
                attach_screenshot(item_tab, f"item_{index}_added_to_cart")
                self.log.info("Added to cart: %s", url)
                item_tab.close()
                self.page.bring_to_front()  # back to the search tab

    @allure.step("Assert cart total <= {budget_per_item} x {items_count}")
    def assert_cart_total_not_exceeds(self, budget_per_item: float, items_count: int) -> None:
        cart = CartPage(self.page).open()
        subtotal = cart.get_subtotal()
        threshold = budget_per_item * items_count
        attach_screenshot(self.page, "cart")
        self.log.info("Cart subtotal '%s' -> %.2f, threshold %.2f", cart.get_subtotal_text(), subtotal, threshold)
        assert subtotal <= threshold, (
            f"Cart subtotal {subtotal:.2f} exceeds budget {budget_per_item} x {items_count} = {threshold:.2f}"
        )
