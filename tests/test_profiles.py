"""CRUD, data persistence, isolation and local API security."""
from pathlib import Path
from backend.database import Database
from .conftest import create_profile


def test_profiles_crud_and_persistence(env):
    client, app, runner, _ = env
    first = create_profile(client,"Primeiro",tags=["cliente"])
    second = create_profile(client,"Segundo")
    assert len(client.get("/api/profiles").json()) == 2
    changed = client.patch(f'/api/profiles/{first["id"]}',json={"name":"Editado"})
    assert changed.status_code == 200
    assert changed.json()["name"] == "Editado"
    duplicate = client.post(f'/api/profiles/{first["id"]}/duplicate')
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] != first["id"]
    assert duplicate.json()["proxy_id"] is None
    assert len(Database(app.state.db.root).all("profiles")) == 3
    assert client.delete(f'/api/profiles/{first["id"]}').status_code == 200
    assert client.get("/api/profiles").json()[0]["id"] == duplicate.json()["id"]
    assert any(p["id"] == second["id"] for p in Database(app.state.db.root).all("profiles"))


def test_isolated_profile_directories_and_limit(env):
    client, _, runner, _ = env
    one = create_profile(client,"One")
    two = create_profile(client,"Two")
    settings = client.put("/api/settings",json={"max_active":1,"warn_duplicate_proxy":True})
    assert settings.status_code == 200
    assert client.post(f'/api/profiles/{one["id"]}/start').status_code == 200
    assert client.post(f'/api/profiles/{two["id"]}/start').status_code == 409
    path1 = runner.root / one["id"] / "browser" / "cookie.txt"
    path1.write_text("one")
    assert client.post(f'/api/profiles/{one["id"]}/stop').status_code == 200
    assert client.post(f'/api/profiles/{two["id"]}/start').status_code == 200
    path2 = runner.root / two["id"] / "browser" / "cookie.txt"
    path2.write_text("two")
    assert client.delete(f'/api/profiles/{one["id"]}').status_code == 200
    assert path2.read_text() == "two"
    assert not path1.exists()


def test_authentication_and_ui(env):
    client, app, _, _ = env
    response = client.get("/api/profiles", headers={"x-app-token":"bad"})
    assert response.status_code == 403
    response = client.get("/api/profiles", headers={"host":"malicious.example"})
    assert response.status_code == 403
    response = client.post("/api/profiles",json={"name":"A","device":"INVALID"})
    assert response.status_code == 422
    page = client.get("/")
    assert page.status_code == 200 and "NEXORA" in page.text
    assert "__NEXORA_TOKEN__" not in page.text
    assert client.get("/static/app.js").status_code == 200
