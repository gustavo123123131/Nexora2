"""Event log persists across app restarts and contains no credentials."""
from fastapi.testclient import TestClient
from backend.main import create_app
from .conftest import FakeRunner, FakeVault, create_profile


def test_persistent_log(env):
    client, app, _, _ = env
    profile = create_profile(client)
    assert client.post(f'/api/profiles/{profile["id"]}/start').status_code == 200
    assert client.post(f'/api/profiles/{profile["id"]}/stop').status_code == 200
    root = app.state.db.root
    restarted = create_app(root=root,runner=FakeRunner(root),secrets=FakeVault())
    with TestClient(restarted,base_url="http://127.0.0.1:8765") as again:
        response = again.get("/api/logs",headers={"x-app-token":restarted.state.token})
        assert response.status_code == 200
        assert [x["action"] for x in response.json()] == ["stopped","started"]
