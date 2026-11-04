import random
import re

from playwright.sync_api import Locator, expect

from src.pages.base_page import BasePage


class ItemPage(BasePage):
    VARIANTS_CONTAINER = "[data-testid='x-msku-evo']"
    # eBay renders variants as custom listboxes; a native <select> is kept as fallback.
    VARIANT_LISTBOX_BUTTONS = f"{VARIANTS_CONTAINER} button.listbox-button__control"
    # Hidden select.listbox__native is the listbox's own backing element, not a separate variant.
    VARIANT_NATIVE_SELECTS = f"{VARIANTS_CONTAINER} select:not([hidden]):not(.listbox__native)"
    AVAILABLE_OPTION = "[role='option'][data-sku-value-name]:not([aria-disabled='true'])"

    ADD_TO_CART = "#atcBtn_btn_1, [data-testid='x-atc-action'] a, [data-testid='x-atc-action'] button"
    ADDED_CONFIRMATION = re.compile(r"added to (your )?cart|view in cart", re.I)

    def select_random_variants(self) -> dict[str, str]:
        """Pick a random available value in every variant dropdown (size/color/...)."""
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
        self.page.locator(self.ADD_TO_CART).first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.ensure_not_blocked()
        # eBay either opens the cart page or shows an "Added to cart" layer.
        if "cart." not in self.page.url:
            expect(self.page.get_by_text(self.ADDED_CONFIRMATION).first).to_be_visible()
