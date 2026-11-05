import random

from playwright.sync_api import Locator, expect

from src.pages.base_page import BasePage
from src.pages.cart_page import CartPage


class ItemPage(BasePage):
    VARIANTS_CONTAINER = "[data-testid='x-msku-evo']"
    # variants are custom listboxes on eBay (a button that opens a listbox), <select> just in case
    VARIANT_LISTBOX_BUTTONS = f"{VARIANTS_CONTAINER} button[aria-haspopup='listbox']"
    # skip the hidden select that belongs to the listbox itself
    VARIANT_NATIVE_SELECTS = f"{VARIANTS_CONTAINER} select:not([hidden]):not(.listbox__native)"
    AVAILABLE_OPTION = "[role='option'][data-sku-value-name]:not([aria-disabled='true'])"

    CART_ICON = "a[aria-label^='Your shopping cart contains']"
    # popup after Add to cart, it has class "spinner" while it's still loading
    ADDED_POPUP = "[role='dialog'].x-atc-action__overlay:not(.spinner)"

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
        # button text is "US Shoe Size (Men's):US 9" - the part before ":" is the name
        label = (button.text_content() or "").split(":")[0].strip()
        button.click()
        # [id=...] and not #id: eBay ids can have [ ] and @ inside, they break a css #id selector
        listbox_id = button.get_attribute("aria-controls")
        options = self.page.locator(f"[id='{listbox_id}'] {self.AVAILABLE_OPTION}")
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
        cart_icon = self.page.locator(self.CART_ICON).first
        count_before = cart_icon.get_attribute("aria-label") if cart_icon.count() else None
        self.log.info("Click 'Add to cart' (%s)", count_before)
        self.add_to_cart_button.click()
        # eBay can go to the cart page, open a popup or just update the cart icon in the
        # header - wait for any of them. expect() keeps checking after navigation, no race
        done = self.page.locator(CartPage.ITEMS).or_(self.page.locator(self.ADDED_POPUP))
        if count_before:
            done = done.or_(self.page.locator(f"{self.CART_ICON}:not([aria-label='{count_before}'])"))
        try:
            expect(done.first).to_be_visible()
        except AssertionError:
            self.ensure_not_blocked()  # block page -> skip instead of fail
            raise
