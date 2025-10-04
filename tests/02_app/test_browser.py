from playwright.sync_api import Page, expect
import pytest
import time

@pytest.fixture
def get_page(page: Page, fastapi_env: dict, wait_for_fastapi):
    page.goto(f"localhost:{fastapi_env['port']}")
    page.wait_for_load_state("domcontentloaded")
    yield True
    # cleanup
    page.close()

def test_page_load(page: Page, get_page):
    # verify that the page has loaded
    expect(page).to_have_title("HTMX Streaming Test")


def test_simple_list_stream(page: Page, get_page):
    button = page.locator("#test-stream-list-btn")
    expect(button).to_be_visible(timeout=5000)
    expect(button).to_be_enabled()

    # It waits for the real data stream connection.
    with page.expect_response("**/test_list/**", timeout=15000) as response_info:
        button.click(timeout=2000)

    response = response_info.value
    assert response.ok

    # The rest of the test
    expect(page.locator("#list-card").first).to_be_visible(timeout=5000)
    expect(page.locator("li")).to_have_count(3, timeout=5000)


def test_simple_form_stream(page: Page, get_page):
    page.locator("#test-stream-form-btn").click(timeout=2000)
    expect(page.locator("#form-card").first).to_be_visible(timeout=10000)
    expect(page.locator("label")).to_have_count(3, timeout=10000)


def test_simple_table_stream(page: Page, get_page):
    page.locator("#test-stream-table-btn").click(timeout=2000)
    expect(page.locator("#table-card").first).to_be_visible(timeout=10000)
    expect(page.locator("tr")).to_have_count(3, timeout=10000)