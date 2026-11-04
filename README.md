# eBay E2E Automation — Playwright + Python

End-to-end scenario on eBay: **search products → filter by price → add to cart → verify the cart total**.
Built with Page Object Model, OOP and data-driven input.

The static code review task is in [ReadMeAIBugs.md](ReadMeAIBugs.md).

---

## How to run

### Prerequisites
- Python **3.10+**
- (for the HTML report) [Allure CLI](https://allurereport.org/docs/install/) — `brew install allure` (needs Java)

### Setup
```bash
git clone https://github.com/mmzobin/ebay-e2e-automation.git
cd ebay-e2e-automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Run
```bash
pytest                                   # default profile: visible browser
TEST_PROFILE=headless pytest             # headless profile
pytest -k shoes                          # one scenario
pytest --slowmo 500                      # slow motion, to watch the steps
PWDEBUG=1 pytest -k shoes                # step-by-step in Playwright Inspector
```

### Reports
```bash
allure serve reports/allure-results      # open the Allure report
allure generate reports/allure-results -o reports/allure-report --clean --single-file   # one HTML file
playwright show-trace reports/traces/<test-name>.zip   # step-by-step trace of a run
```
Every run also writes a JUnit XML report to `reports/junit.xml`.

---

## Configuration (profiles, ENV)

| Source | Example | Priority |
|---|---|---|
| Environment variables | `HEADLESS=true MAX_PAGES=3 pytest` | highest |
| `.env` file (copy from `.env.example`) | `TEST_PROFILE=headless` | |
| YAML profile `config/profiles/<TEST_PROFILE>.yaml` | `default`, `headless` | lowest |

Supported overrides: `TEST_PROFILE`, `BASE_URL`, `HEADLESS`, `MAX_PAGES`, `EBAY_USER`, `EBAY_PASSWORD`.

**Test data** lives in [`data/search_scenarios.yaml`](data/search_scenarios.yaml); each entry becomes a separate test case:
```yaml
- id: shoes_under_220
  query: shoes
  max_price: 220
  limit: 5
```

---

## Architecture

```
config/
  settings.py              # loads YAML profile + .env + ENV into one Settings object
  profiles/                # default.yaml, headless.yaml
data/
  search_scenarios.yaml    # data-driven test input
src/
  pages/                   # Page Objects: locators + atomic page actions only
    base_page.py           #   open(), bot-protection detection
    home_page.py           #   search box
    search_results_page.py #   XPath item parsing, price filter, paging
    item_page.py           #   random variant selection, Add to cart
    cart_page.py           #   subtotal
    login_page.py
  services/                # business flows = the 4 functions of the assignment
    auth_service.py        #   login()
    search_service.py      #   search_items_by_name_under_price()
    cart_service.py        #   add_items_to_cart(), assert_cart_total_not_exceeds()
  models/                  # dataclasses: SearchScenario, SearchResultItem
  utils/                   # price_parser, data_loader, logger, Allure helpers
tests/e2e/
  test_shopping_flow.py    # the full scenario, parametrized from YAML
conftest.py                # browser config from profile, tracing, failure screenshots
```

**Layers:** test → services → pages. Tests contain no locators; pages contain no business
logic; services combine page actions into the assignment's functions. Each class has one
responsibility (SRP).

### The four functions

| Function | Behaviour |
|---|---|
| `AuthService.login()` | Logs in if `EBAY_USER`/`EBAY_PASSWORD` are set, otherwise continues as guest. If eBay shows a captcha, falls back to guest (captcha is out of scope). |
| `search_items_by_name_under_price(query, max_price, limit=5)` | Searches, applies the page's price filter (falls back to the `_udhi` URL parameter if the filter is missing), extracts items with **XPath**, keeps those with price ≤ `max_price`, follows **Next** until `limit` items are found or pages run out. Returns 0..`limit` URLs. |
| `add_items_to_cart(urls)` | Opens each item in a new tab, picks a **random available** value in every variant dropdown (size, color…), clicks *Add to cart*, attaches a screenshot, closes the tab and returns to the search tab. |
| `assert_cart_total_not_exceeds(budget_per_item, items_count)` | Opens the cart, reads the **Subtotal**, asserts `subtotal ≤ budget_per_item × items_count`, attaches a screenshot of the cart. |

### Robustness / locators
- **Two search layouts** supported: current `li.s-card` and legacy `li.s-item`.
- The **"Shop on eBay" promo card** has a fake `/itm/` link — excluded (real results carry `@data-item-pos`).
- **Price parsing** handles `$12.99`, `ILS 1,234.56`, `US $…`; a **range** (`ILS 10.00 to ILS 25.00`) is
  rendered as separate spans and is evaluated by its **upper bound** — a variant is chosen randomly
  later, so the conservative value keeps the cart within budget. Strikethrough "was" prices are ignored.
- **Variants** are custom listboxes (not `<select>`): out-of-stock options (`aria-disabled="true"`) are
  skipped; the hidden backing `<select>` is ignored; a real `<select>` is supported as a fallback.
- **No hard sleeps** — Playwright auto-waiting and `expect()` assertions.
- **Bot protection detection**: if eBay returns its block page / captcha, the test is marked
  **skipped** with the reason and a screenshot, instead of failing on a locator timeout.

### Reporting
- **Allure**: steps for each function, screenshot per added item, cart screenshot,
  full Playwright trace of each test, screenshot on failure.
- **Logs**: every action is logged to the console (`log_cli`).
- **JUnit XML**: `reports/junit.xml`.

---

## Limitations and assumptions

- **eBay bot protection (Akamai).** During development (Nov 2026) eBay returned its *"Error Page"*
  to every Playwright-controlled browser (Chromium, Chrome, Firefox — headless and headed), while a
  regular browser on the same network worked. Bypassing bot protection is out of scope (the
  assignment says captcha does not need to be handled), so the framework detects the block page and
  skips the test with a clear reason. Locators were verified against real eBay pages (search results,
  item with variants, cart) saved from a regular browser.
- **Login**: guest mode by default — eBay allows adding to cart without an account, and automated
  login is normally stopped by a captcha. Credentials are read only from ENV / `.env` (never committed).
  Login page locators are eBay's standard ones but could not be verified live.
- **Currency**: eBay shows prices in the currency of your region (ILS from Israel, USD from the US).
  `max_price` and the cart subtotal are compared in the currency the site displays; both the search
  results and the cart use the same currency.
- **Quantity** is always 1 (variants like size/color are random). A random quantity would make
  `subtotal ≤ budget_per_item × items_count` meaningless.
- **Paging** stops after `max_pages` (default 5, configurable via `MAX_PAGES`) as a safety limit.
- **Subtotal** (items only, without shipping) is used as the cart total.
- **Cart state**: the test does not clear the cart beforehand; in guest mode every run starts with a
  fresh browser context, so the cart is empty.
