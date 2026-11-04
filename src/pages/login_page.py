from src.pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "https://signin.ebay.com/signin/"
    SIGNED_IN_MARKER = "#gh-ug, [data-testid='gh-my-ebay']"

    @property
    def username_input(self):
        return self.page.get_by_role("textbox", name="Email or username")

    @property
    def continue_button(self):
        return self.page.get_by_role("button", name="Continue", exact=True)

    @property
    def password_input(self):
        # password field has no aria role, so by label
        return self.page.get_by_label("Password", exact=True)

    @property
    def sign_in_button(self):
        return self.page.get_by_role("button", name="Sign in", exact=True)

    def open(self) -> "LoginPage":
        return super().open(self.URL)

    def login(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.continue_button.click()
        self.ensure_not_blocked()  # captcha usually appears here
        self.password_input.fill(password)
        self.sign_in_button.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.ensure_not_blocked()

    def is_signed_in(self) -> bool:
        return self.page.locator(self.SIGNED_IN_MARKER).count() > 0
