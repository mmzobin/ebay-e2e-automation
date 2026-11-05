import random
import re

from playwright.sync_api import Locator, expect

from src.pages.base_page import BasePage
from src.pages.cart_page import CartPage


class ItemPage(BasePage):
    VARIANTS_CONTAINER = "[data-testid='x-msku-evo']"
    # variants are custom listboxes on eBay, <select> just in case
    VARIANT_LISTBOX_BUTTONS = f"{VARIANTS_CONTAINER} button.listbox-button__control"
    # skip the hidden select that belongs to the listbox itself
    VARIANT_NATIVE_SELECTS = f"{VARIANTS_CONTAINER} select:not([hidden]):not(.listbox__native)"
    AVAILABLE_OPTION = "[role='option'][data-sku-value-name]:not([aria-disabled='true'])"

    ADDED_CONFIRMATION = re.compile(r"added to (your )?cart|view in cart", re.I)

    @property
    def add_to_cart_button(self):
        # eBay sets aria-hidden on the page when a popup is open, then the role locator
        # doesn't see the button - test id as a backup
        by_role = self.page.get_by_role("button", name="Add to cart", exact=True)
        return by_role.or_(self.page.locator("[data-testid='x-atc-action'] [role='button']")).first

    def select_random_variants(self) -> dict[str, str]:
        # size, color etc. - random value from the ones in stock
        chosen: dict[str, str] = {}
        buttons = self.page.locator(self.VARIANT_LISTBOX_BUTTONS)
        for i in range(buttons.count()):
            label, value = self._select_in_listbox(buttons.nth(i))
            chosen[label] = value
        selects = self.page.locator(self.VARIANT_NATIVE_SELECTS)
        for i in range(selects.count()):
            label, value = self._select_in_native(selects.nth(i))
            chosen[label] = value
        self.log.info("Variants chosen: %s", chosen or "no variants on this listing")
        return chosen

    def _select_in_listbox(self, button: Locator) -> tuple[str, str]:
        label = button.locator(".btn__label").inner_text().strip()
        button.click()
        options = self.page.locator(f"#{button.get_attribute('aria-controls')} {self.AVAILABLE_OPTION}")
        if options.count() == 0:
            raise AssertionError(f"No available values for variant '{label}' on {self.page.url}")
        option = options.nth(random.randrange(options.count()))
        value = option.get_attribute("data-sku-value-name")
        option.click()
        expect(button).to_have_attribute("aria-expanded", "false")
        return label, value

    def _select_in_native(self, select: Locator) -> tuple[str, str]:
        values = [
            v for v in select.locator("option:not([disabled])").evaluate_all("els => els.map(e => e.value)")
            if v and v != "-1"
        ]
        value = random.choice(values)
        select.select_option(value)
        return select.get_attribute("name") or "select", value

    def add_to_cart(self) -> None:
        self.log.info("Click 'Add to cart'")
        self.add_to_cart_button.click()
        # sometimes eBay goes to the cart, sometimes shows a popup - wait for any of them.
        # expect() keeps checking after navigation, so no race with page load
        popup = self.page.get_by_text(self.ADDED_CONFIRMATION)
        cart = self.page.locator(CartPage.ITEMS)
        try:
            expect(popup.or_(cart).first).to_be_visible()
        except AssertionError:
            self.ensure_not_blocked()  # block page -> skip instead of fail
            raise
