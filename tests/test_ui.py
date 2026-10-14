"""Real dashboard smoke test on localhost."""
import socket
import threading
import time
import pytest
import uvicorn
from playwright.async_api import async_playwright
from backend.main import create_app


@pytest.mark.asyncio
async def test_browser_ui_profile_crud(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        port = sock.getsockname()[1]
    app = create_app(root=tmp_path)
    server = uvicorn.Server(uvicorn.Config(app,host="127.0.0.1",port=port,
                                          access_log=False,log_level="warning"))
    thread = threading.Thread(target=server.run,daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(.05)
    assert server.started
    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(f"http://127.0.0.1:{port}/")
                await page.locator('[data-act="new-profile"]').click(timeout=15000)
                await page.locator('input[name="name"]').fill("E2E Mobile")
                await page.locator('select[name="device"]').select_option("Pixel 7")
                await page.locator('#modalForm button[type="submit"]').click()
                await page.locator('tbody tr').filter(has_text="E2E Mobile").wait_for()
                await page.locator('[data-page="profiles"]').click()
                await page.locator('[data-act="edit"]').first.click()
                await page.locator('input[name="name"]').fill("E2E Editado")
                await page.locator('#modalForm button[type="submit"]').click()
                await page.locator('tbody tr').filter(has_text="E2E Editado").wait_for()
            finally:
                await browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=10)
