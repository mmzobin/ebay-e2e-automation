Code from the task:

```python
from playwright.sync_api import sync_playwright
from selenium import webdriver
import time

def test_search_functionality():
    browser = sync_playwright().start().chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")

    time.sleep(2)

    search_box = page.locator("#search")
    search_box.fill("playwright testing")

    page.locator(".button").click()

    time.sleep(3)

    results = page.locator(".result-item")

    browser.close()
```

Reviewed by reading the code only (no running), as asked. Most important problems first.

---

## 1. The test doesn't check anything

```python
results = page.locator(".result-item")
```

A locator in Playwright is lazy. Creating it doesn't go to the DOM and can't fail. `results` is
never used and there is no assert at all. So even if search worked, the test would pass with 0
results or with an error page. A test that can't fail is worse than no test, it just gives false
confidence.

**Fix:** add a real check. `expect` also retries until timeout:

```python
from playwright.sync_api import expect

results = page.locator(".result-item")
expect(results.first).to_be_visible()
expect(results.first).to_contain_text("playwright", ignore_case=True)
```

---

## 2. Playwright is never stopped, browser is not closed on error

```python
browser = sync_playwright().start().chromium.launch()
...
browser.close()
```

- `sync_playwright().start()` starts the Playwright driver process. The object is not saved
  anywhere, so `.stop()` can't be called and the process stays alive after every test.
- `browser.close()` is just the last line. If anything fails before it (locator not found,
  timeout), it never runs and Chromium stays open. On CI with many tests this eats memory.
- `browser.new_page()` uses a default context, so there is no place to set viewport, locale,
  tracing etc.

**Fix:** let a context manager close everything:

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    try:
        page = browser.new_context().new_page()
        ...
    finally:
        browser.close()
```

Even simpler with pytest-playwright, the `page` fixture creates and closes everything per test:

```python
def test_search_functionality(page):
    page.goto(...)
```

---

## 3. `time.sleep()` instead of waiting for something

```python
time.sleep(2)
time.sleep(3)
```

Fixed sleeps are too long and too short at the same time. On a fast machine the test just waits
5 extra seconds. On a slow CI agent 2-3 seconds may be not enough and the test fails randomly
(flaky). Also it's not clear what we are waiting for. Playwright already waits for an element to
be visible and enabled before `fill()` and `click()`, so the first sleep is not needed at all, and
the second one should be a wait for a real condition.

**Fix:** remove `import time` and wait for something specific:

```python
page.goto("https://example.com")
page.locator("#search").fill("playwright testing")   # waits for the element by itself
page.get_by_role("button", name="Search").click()
expect(page.locator(".result-item").first).to_be_visible()
```

---

## 4. Selenium import

```python
from selenium import webdriver
```

Selenium is imported but never used, looks like two different examples were mixed together.
Problems:
- if selenium is not installed, the file fails on import with `ModuleNotFoundError` and pytest
  can't even collect the test;
- extra dependency for nothing;
- confusing for the next person, which framework is used here?

**Fix:** delete the line.

---

## 5. Bad locators and wrong site

```python
page.goto("https://example.com")
page.locator("#search")
page.locator(".button")
```

- example.com is an empty placeholder page, there is no search on it. `fill()` will wait 30
  seconds and fail with `TimeoutError`. Also the url is hardcoded instead of coming from config.
- `.button` is a generic CSS class. If there is more than one such element, Playwright strict mode
  throws `strict mode violation: locator(".button") resolved to N elements`. If there is exactly one
  but it's the wrong button, the test clicks it and continues as if everything is fine.
- CSS classes change with every redesign, they are the least stable locators.

**Fix:** use locators by role / placeholder and take the url from config:

```python
page.goto(base_url)
page.get_by_role("searchbox").fill("playwright testing")
page.get_by_role("button", name="Search").click()
```

If CSS is really needed, at least make it specific: `form#search-form button[type=submit]`.

---

## 6. Smaller things

- browser settings (headless, browser type, timeouts) are hardcoded, should come from config;
- search text is hardcoded, better to use `@pytest.mark.parametrize` or a data file;
- no screenshot / trace on failure, so a red CI run can't be investigated;
- locators are inside the test, no page object, so every UI change means editing every test.

---

## Fixed version

```python
import pytest
from playwright.sync_api import Page, expect


class SearchPage:
    def __init__(self, page: Page, base_url: str):
        self.page = page
        self.base_url = base_url
        self.search_box = page.get_by_role("searchbox")
        self.search_button = page.get_by_role("button", name="Search")
        self.results = page.locator(".result-item")

    def open(self):
        self.page.goto(self.base_url)
        return self

    def search(self, text: str):
        self.search_box.fill(text)
        self.search_button.click()
        return self


@pytest.mark.parametrize("text", ["playwright testing", "pytest"])
def test_search_functionality(page: Page, base_url: str, text: str):
    search = SearchPage(page, base_url).open().search(text)

    expect(search.results.first).to_be_visible()
    expect(search.results.first).to_contain_text(text.split()[0], ignore_case=True)
```

Run:
```bash
pytest --base-url https://<site-with-search> --tracing retain-on-failure --screenshot only-on-failure
```
