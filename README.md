# eBay E2E tests (Playwright + Python)

E2E scenario on eBay: search for items, filter by price, add them to the cart and check the cart
total. Page Object Model, OOP, test data from a YAML file, Allure report.

The bugs review task is in [ReadMeAIBugs.md](ReadMeAIBugs.md).

## How to run

Requirements:
- Python 3.10+
- for the HTML report: [Allure](https://allurereport.org/docs/install/) (`brew install allure`, needs Java)

Install:
```bash
git clone https://github.com/mmzobin/ebay-e2e-automation.git
cd ebay-e2e-automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Run:
```bash
pytest                         # default profile, browser is visible
TEST_PROFILE=headless pytest   # headless
pytest -k shoes                # only one scenario
pytest --slowmo 500            # slower, easier to follow
PWDEBUG=1 pytest -k shoes      # step by step in Playwright Inspector
```

Reports:
```bash
allure serve reports/allure-results
allure generate reports/allure-results -o reports/allure-report --clean --single-file
playwright show-trace reports/traces/<test name>.zip
```
JUnit XML is written to `reports/junit.xml` on every run.

## Config

Settings are taken from (top wins):
1. environment variables, e.g. `HEADLESS=true MAX_PAGES=3 pytest`
2. `.env` file (see `.env.example`)
3. profile file `config/profiles/<TEST_PROFILE>.yaml` (`default` or `headless`)

Variables: `TEST_PROFILE`, `BASE_URL`, `HEADLESS`, `MAX_PAGES`, `EBAY_USER`, `EBAY_PASSWORD`.

Test data is in `data/search_scenarios.yaml`. Every item there is a separate test case:
```yaml
- id: shoes_under_220
  query: shoes
  max_price: 220
  limit: 5
```

## Project structure

```
config/
  settings.py              # profile + .env + env vars
  profiles/                # default.yaml, headless.yaml
data/
  search_scenarios.yaml    # test data
src/
  pages/                   # page objects: locators and page actions
    base_page.py           # open page, detect eBay block page
    home_page.py
    search_results_page.py # parse items with xpath, price filter, paging
    item_page.py           # random variants, add to cart
    cart_page.py           # subtotal
    login_page.py
  services/                # the 4 functions from the task
    auth_service.py        # login()
    search_service.py      # search_items_by_name_under_price()
    cart_service.py        # add_items_to_cart(), assert_cart_total_not_exceeds()
  models/                  # dataclasses
  utils/                   # price parser, data loader, logger, allure helper
tests/e2e/
  test_shopping_flow.py    # full scenario, parametrized from yaml
conftest.py                # browser settings from profile, trace, screenshot on failure
```

Test calls services, services use pages. There are no locators in the test and no business logic
in pages.

### The 4 functions

**`AuthService.login()`** - if `EBAY_USER` / `EBAY_PASSWORD` are set, logs in. Otherwise continues
as guest. If eBay shows a captcha it also continues as guest (captcha is out of scope).

**`search_items_by_name_under_price(query, max_price, limit=5)`** - searches, sets max price in the
price filter on the page (if there is no filter, adds `_udhi` to the url), takes items with xpath and
keeps the ones with price <= max_price. If there are not enough on the page, clicks Next until it has
`limit` items or pages end. Returns 0 to `limit` urls.

**`add_items_to_cart(urls)`** - opens every item in a new tab, picks a random value in each variant
(size, color...) from the ones in stock, clicks Add to cart, saves a screenshot, closes the tab and
goes back to the search tab.

**`assert_cart_total_not_exceeds(budget_per_item, items_count)`** - opens the cart, reads Subtotal
and checks `subtotal <= budget_per_item * items_count`. Saves a screenshot of the cart.

### Things I handled on eBay pages

- Search results come in two layouts, new `li.s-card` and old `li.s-item`. Both are supported.
- First card "Shop on eBay" is an ad with a fake `/itm/` link. Real items have `data-item-pos`, the
  ad doesn't, so it's filtered out.
- Prices: `$12.99`, `ILS 1,234.56`, `US $...`. A price range ("ILS 10.00 to ILS 25.00") comes as
  separate spans; I take the higher price because the variant is chosen randomly later. The
  crossed-out old price is ignored.
- Variants are custom dropdowns, not `<select>`. Out of stock options have `aria-disabled="true"` and
  are skipped. Normal `<select>` is supported too just in case.
- No `sleep()`, only Playwright auto-waiting and `expect()`.
- If eBay shows its block page or a captcha, the test is skipped with the reason and a screenshot
  instead of failing on a timeout.

### Report

In Allure: steps of each function, screenshot of every item added to the cart, screenshot of the
cart, Playwright trace of the whole test, screenshot on failure. All actions are also logged to the
console.

## Limitations / assumptions

- **eBay blocks automated browsers.** When I worked on this (Nov 2026) eBay returned "Error Page" to
  every browser controlled by Playwright: Chromium, Chrome and Firefox, headless and headed. A normal
  browser on the same network worked fine. Getting around bot protection is not part of the task
  (captcha doesn't need to be handled), so the test detects this page and is skipped. I checked the
  locators on real eBay pages saved from a normal browser (search results, item with sizes, cart).
- **Login:** guest by default. eBay lets you add to cart without an account, and automated login
  usually gets a captcha anyway. Credentials only from env / `.env`, never in the repo. Login page
  locators are the standard eBay ones but I couldn't check them live.
- **Currency:** eBay shows prices in the local currency (ILS from Israel, USD from the US).
  `max_price` and the subtotal are compared in whatever currency the site shows. Search results and
  cart use the same one.
- **Quantity is always 1.** Size and color are random, but random quantity would break the
  `budget_per_item * items_count` check.
- **Paging** stops after `max_pages` (5 by default, `MAX_PAGES` to change), just as a safety limit.
- **Subtotal** (items without shipping) is used as the cart total.
- The cart is not cleared before the test. As a guest every run starts with a new browser context,
  so the cart is empty anyway.
