"""Fakes isolate API tests from desktop browser binaries."""
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.main import create_app


class FakeVault:
    def __init__(self):
        self.data = {}

    def put(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)


class FakeRunner:
    def __init__(self, root):
        self.root = Path(root) / "profiles"
        self.running = set()
        self.errors = {}

    async def devices(self):
        return [{"name":"Pixel 7","browser":"chromium","viewport":{"width":412,"height":915}},
                {"name":"iPhone 13","browser":"webkit","viewport":{"width":390,"height":844}}]

    def status(self, uid):
        return {"status":"running" if uid in self.running else "stopped",
                "error":self.errors.get(uid)}

    async def start(self, profile, proxy, limit):
        if profile["id"] in self.running:
            raise ValueError("Already running")
        if len(self.running) >= limit:
            raise ValueError("Simultaneous profile limit reached")
        folder = self.root / profile["id"] / "browser"
        folder.mkdir(parents=True, exist_ok=True)
        self.running.add(profile["id"])
        return self.status(profile["id"])

    async def stop(self, uid):
        self.running.discard(uid)
        return self.status(uid)

    async def shutdown(self):
        self.running.clear()


@pytest.fixture
def env(tmp_path):
    runner = FakeRunner(tmp_path)
    vault = FakeVault()
    app = create_app(root=tmp_path, runner=runner, secrets=vault)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        client.headers.update({"x-app-token":app.state.token})
        yield client, app, runner, vault


def create_profile(client, name="Teste", **changes):
    data = {"name":name,"device":"Pixel 7",**changes}
    result = client.post("/api/profiles",json=data)
    assert result.status_code == 201, result.text
    return result.json()
