"""Proxy formatting, secure vault, import errors, and disassociation."""
from .conftest import create_profile
from backend.proxy_helpers import parse_line, proxy_uri


def test_parser():
    a = parse_line("proxy.example:8080:user:password")
    assert a.scheme == "http" and a.username == "user"
    b = parse_line("socks5://alice:pass@127.0.0.1:1080")
    assert b.scheme == "socks5" and b.port == 1080
    assert "alice:pass@" in proxy_uri(b.model_dump(), b.password)


def test_proxy_vault_crud(env):
    client, app, _, vault = env
    response = client.post("/api/proxies",json={
        "name":"A","scheme":"http","host":"127.0.0.1","port":8080,
        "username":"alice","password":"super-secret"
    })
    assert response.status_code == 201, response.text
    record = response.json()
    assert "password" not in record and "super-secret" not in str(record)
    assert "super-secret" not in str(app.state.db.one("proxies",record["id"]))
    assert vault.get(record["id"]) == "super-secret"
    assert client.patch(f'/api/proxies/{record["id"]}',json={"name":"Novo"}).status_code == 200
    profile = create_profile(client,proxy_id=record["id"])
    assert client.delete(f'/api/proxies/{record["id"]}').status_code == 200
    updated = next(p for p in client.get("/api/profiles").json() if p["id"] == profile["id"])
    assert updated["proxy_id"] is None
    assert vault.get(record["id"]) is None


def test_import_and_failure(env):
    client, _, _, _ = env
    invalid = client.post("/api/proxies/import",json={"lines":"proxy:8080:u:pwd\nbadline"})
    assert invalid.status_code == 422 and "pwd" not in invalid.text
    response = client.post("/api/proxies/import",json={"lines":"127.0.0.1:1\nlocalhost:2"})
    assert response.status_code == 200
    assert len(response.json()["imported"]) == 2
    pid = response.json()["imported"][0]["id"]
    checked = client.post(f"/api/proxies/{pid}/check")
    assert checked.status_code == 200
    assert checked.json()["status"] == "error"
    assert "super-secret" not in checked.text
