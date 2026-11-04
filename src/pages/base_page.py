from playwright.sync_api import Page

from src.utils.logger import get_logger
from src.utils.reporting import attach_screenshot


class BotProtectionError(Exception):
    """eBay showed its anti-bot / error page."""


class BasePage:
    BLOCK_PAGE_TITLES = ("error page | ebay", "pardon our interruption", "security measure")
    CAPTCHA = "iframe[title*='captcha' i], #captcha_loading, div[id*='captcha' i]"

    def __init__(self, page: Page):
        self.page = page
        self.log = get_logger(type(self).__name__)

    def open(self, url: str):
        self.log.info("Open %s", url)
        self.page.goto(url, wait_until="domcontentloaded")
        self.ensure_not_blocked()
        return self

    def ensure_not_blocked(self) -> None:
        # better to stop here than wait 15s for a locator that will never show up
        title = self.page.title().lower()
        if any(marker in title for marker in self.BLOCK_PAGE_TITLES) or self.page.locator(self.CAPTCHA).count():
            attach_screenshot(self.page, "bot_protection_page")
            raise BotProtectionError(f"Blocked by eBay bot protection on {self.page.url} (title: '{title}')")
