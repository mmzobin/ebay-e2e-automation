import allure
from playwright.sync_api import Page

from src.utils.logger import get_logger

log = get_logger("reporting")


def attach_screenshot(page: Page, name: str) -> None:
    allure.attach(page.screenshot(full_page=False), name=name, attachment_type=allure.attachment_type.PNG)
    log.info("Screenshot attached: %s", name)
