import allure
import pytest
from playwright.sync_api import Page

from src.services.auth_service import AuthService
from src.services.cart_service import CartService
from src.services.search_service import SearchService
from src.utils.data_loader import load_search_scenarios

SCENARIOS = load_search_scenarios()


@allure.feature("eBay shopping flow")
@pytest.mark.e2e
@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.id for s in SCENARIOS])
def test_search_add_to_cart_and_check_total(page: Page, scenario):
    AuthService(page).login()

    urls = SearchService(page).search_items_by_name_under_price(scenario.query, scenario.max_price, scenario.limit)
    allure.attach("\n".join(urls) or "(none)", name="found_item_urls", attachment_type=allure.attachment_type.TEXT)

    cart = CartService(page)
    cart.add_items_to_cart(urls)
    cart.assert_cart_total_not_exceeds(scenario.max_price, len(urls))
