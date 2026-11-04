import allure
from playwright.sync_api import Page

from config.settings import settings
from src.pages.base_page import BotProtectionError
from src.pages.login_page import LoginPage
from src.utils.logger import get_logger


class AuthService:
    """Login with EBAY_USER / EBAY_PASSWORD from env, guest mode if they are not set."""

    def __init__(self, page: Page):
        self.page = page
        self.log = get_logger("AuthService")

    @allure.step("Authenticate")
    def login(self) -> bool:
        if not settings.has_credentials:
            self.log.info("No EBAY_USER/EBAY_PASSWORD -> continue as guest")
            return False
        login_page = LoginPage(self.page)
        try:
            login_page.open().login(settings.ebay_user, settings.ebay_password)
        except BotProtectionError as error:
            # captcha is out of scope for this task, continue as guest
            self.log.warning("Login blocked by captcha/bot protection, continue as guest: %s", error)
            return False
        signed_in = login_page.is_signed_in()
        self.log.info("Signed in: %s", signed_in)
        return signed_in
