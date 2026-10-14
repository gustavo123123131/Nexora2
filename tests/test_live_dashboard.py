"""Real localhost smoke test: Chromium UI talks to the actual FastAPI database."""
import os
import socket
import threading
import time
import pytest
import uvicorn
from playwright.sync_api import sync_playwright
from nexora.api import create_app


@pytest.mark.skipif(not os.getenv("NEXORA_CHROMIUM_PATH"), reason="Browser path required")
def test_live_dashboard_profile_creation(tmp_path):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    app = create_app(tmp_path, headless=True)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port,
                                           log_level="warning", access_log=False))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(200):
        if server.started:
            break
        time.sleep(.05)
    assert server.started
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True,
                executable_path=os.environ["NEXORA_CHROMIUM_PATH"])
            try:
                page = browser.new_page()
                errors = []
                page.on("pageerror", lambda exc: errors.append(str(exc)))
                page.goto(f"http://127.0.0.1:{port}/")
                page.get_by_role("button", name="Novo perfil").click(timeout=15000)
                page.locator("#field-name").fill("Live QA 2026")
                page.get_by_role("button", name="Criar perfil").click()
                page.get_by_role("button", name="Perfis", exact=False).first.click()
                page.get_by_text("Live QA 2026").wait_for()
                assert not errors, errors
                assert len(app.state.store.list_profiles()) == 1
            finally:
                browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=15)
