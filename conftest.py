import allure
import pytest

from config.settings import REPORTS_DIR, settings
from src.pages.base_page import BotProtectionError
from src.utils.logger import get_logger

log = get_logger("conftest")


# ---------- browser configuration from the active profile (pytest-playwright fixtures) ----------
@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "headless": settings.headless}


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {**browser_context_args, "locale": settings.locale, "viewport": {"width": 1440, "height": 900}}


@pytest.fixture(autouse=True)
def configure_page(request, context, page):
    """Timeouts + full trace of every test, attached to Allure."""
    log.info("Profile: %r", settings)
    context.set_default_timeout(settings.default_timeout_ms)  # applies to item tabs too
    context.tracing.start(screenshots=True, snapshots=True)
    yield page
    trace_path = REPORTS_DIR / "traces" / f"{request.node.name}.zip"
    context.tracing.stop(path=trace_path)
    allure.attach.file(trace_path, name="playwright_trace", extension="zip")
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        allure.attach(page.screenshot(), name="failure_screenshot", attachment_type=allure.attachment_type.PNG)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.hookimpl(wrapper=True)
def pytest_pyfunc_call(pyfuncitem):
    """Anti-bot block is an environment limitation, not a product bug -> skip with a clear reason."""
    try:
        return (yield)
    except BotProtectionError as error:
        pytest.skip(str(error))
