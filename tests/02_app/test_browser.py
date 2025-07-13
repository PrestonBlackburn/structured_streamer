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
    # page.wait_for_selector("#sse-list-container")
    page.wait_for_selector("#list-card", timeout=20000)
    # can do this better later
    time.sleep(3)
    list_items = page.locator("li")
    count_li = list_items.count()
    assert count_li > 1
    page.close()


def test_simple_form_stream(page: Page, fastapi_env: dict, wait_for_fastapi):
    page.goto(f"localhost:{fastapi_env['port']}")
    page.locator("#test-stream-form-btn").click(timeout=1000)
    page.wait_for_selector("#form-card", timeout=20000)
    time.sleep(3)
    form_items = page.locator("label")
    count_form_item = form_items.count()
    assert count_form_item > 1
    page.close()
