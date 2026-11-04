from src.pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "https://signin.ebay.com/signin/"
    USERNAME = "#userid"
    CONTINUE = "#signin-continue-btn"
    PASSWORD = "#pass"
    SIGN_IN = "#sgnBt"
    SIGNED_IN_MARKER = "#gh-ug, [data-testid='gh-my-ebay']"

    def open(self) -> "LoginPage":
        return super().open(self.URL)

    def login(self, username: str, password: str) -> None:
        self.page.locator(self.USERNAME).fill(username)
        self.page.locator(self.CONTINUE).click()
        self.ensure_not_blocked()  # eBay usually shows a captcha at this step
        self.page.locator(self.PASSWORD).fill(password)
        self.page.locator(self.SIGN_IN).click()
        self.page.wait_for_load_state("domcontentloaded")
        self.ensure_not_blocked()

    def is_signed_in(self) -> bool:
        return self.page.locator(self.SIGNED_IN_MARKER).count() > 0
