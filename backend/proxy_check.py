"""Connectivity check against a configurable authorized IP endpoint."""
from datetime import datetime, timezone
from urllib.parse import urlsplit
import httpx
from fastapi import APIRouter, Request, HTTPException
from .config import ip_check_url
from .proxy_helpers import proxy_uri
from .proxy_routes import public

router = APIRouter()


@router.post("/proxies/{uid}/check")
async def check_proxy(request: Request, uid: str):
    app = request.app
    row = app.state.db.one("proxies", uid)
    if row is None:
        raise HTTPException(404, "Proxy not found")
    endpoint = ip_check_url()
    if urlsplit(endpoint).scheme not in ("http", "https"):
        raise HTTPException(422, "Test endpoint must be HTTP(S)")
    try:
        password = app.state.vault.get(uid) if row.get("password_key") else None
        async with httpx.AsyncClient(proxy=proxy_uri(row, password), timeout=10,
                                      trust_env=False) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
        try:
            ip = response.json()["ip"]
        except (KeyError, ValueError, TypeError):
            ip = response.text.strip()
        if not ip:
            raise ValueError("Empty response")
        row.update(status="ok", exit_ip=str(ip)[:64], error=None)
    except Exception as exc:
        row.update(status="error", exit_ip=None,
                   error=f"Connectivity failed ({type(exc).__name__})")
    row["last_checked"] = datetime.now(timezone.utc).isoformat()
    return public(app.state.db.save("proxies", row))
