"""Headless browser integration: real persisted storage and independent contexts."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4
import pytest
from backend.runner import Runner
from .conftest import FakeVault


class Page(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"<!doctype html><title>Isolation test</title>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.mark.asyncio
async def test_real_persistent_context_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXORA_HEADLESS","true")
    server = ThreadingHTTPServer(("127.0.0.1",0),Page)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"
    runner = Runner(tmp_path,FakeVault())
    def profile(uid):
        return {"id":uid,"device":"Pixel 7","locale":"pt-BR",
                "timezone":"America/Sao_Paulo","viewport_width":None,
                "viewport_height":None}
    first, second = profile(str(uuid4())), profile(str(uuid4()))
    try:
        await runner.start(first,None,2)
        ctx1 = runner.running[first["id"]]
        await ctx1.pages[0].goto(url)
        await ctx1.pages[0].evaluate("localStorage.setItem('key','first')")
        await runner.stop(first["id"])
        await runner.start(first,None,2)
        ctx1 = runner.running[first["id"]]
        await ctx1.pages[0].goto(url)
        assert await ctx1.pages[0].evaluate("localStorage.getItem('key')") == "first"
        await runner.start(second,None,2)
        ctx2 = runner.running[second["id"]]
        await ctx2.pages[0].goto(url)
        assert await ctx2.pages[0].evaluate("localStorage.getItem('key')") is None
        assert ctx1 is not ctx2
    finally:
        await runner.shutdown()
        server.shutdown()
        server.server_close()
