from playwright.sync_api import Page, expect
import pytest
import time


def test_page_load(page: Page, fastapi_env: dict, wait_for_fastapi):
    # verify that the page has loaded
    page.goto(f"localhost:{fastapi_env['port']}")
    expect(page).to_have_title("HTMX Streaming Test")
    page.close()


def test_simple_list_stream(page: Page, fastapi_env: dict, wait_for_fastapi):
    page.goto(f"localhost:{fastapi_env['port']}")
    page.locator("#test-stream-list-btn").click(timeout=1000)
    # the server response (htmx)
    expect(page.locator("#list-card").first).to_be_visible(timeout=5000)
    expect(page.locator("li")).to_have_count(3, timeout=10000)
    page.close()


def test_simple_form_stream(page: Page, fastapi_env: dict, wait_for_fastapi):
    page.goto(f"localhost:{fastapi_env['port']}")
    page.locator("#test-stream-form-btn").click(timeout=1000)
    expect(page.locator("#form-card").first).to_be_visible(timeout=5000)
    expect(page.locator("label")).to_have_count(3, timeout=10000)
    page.close()
