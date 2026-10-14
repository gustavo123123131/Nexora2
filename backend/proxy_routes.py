"""Proxy records; secrets exist only in the OS credential vault."""
from uuid import uuid4
from fastapi import APIRouter, Request, HTTPException
from .schemas import Proxy
from .proxy_helpers import validate_host

router = APIRouter()


def public(row):
    return {k: v for k, v in row.items() if k != "password_key"} | {
        "has_password": bool(row.get("password_key"))}


def create_proxy(app, item):
    data = item.model_dump()
    validate_host(data["host"])
    uid = str(uuid4())
    if data["password"]:
        try:
            app.state.vault.put(uid, data["password"])
        except Exception:
            raise HTTPException(503, "System credential vault unavailable") from None
    row = {"id": uid, **{k: v for k, v in data.items() if k != "password"},
           "password_key": uid if data["password"] else None,
           "status": "unchecked", "exit_ip": None, "last_checked": None, "error": None}
    app.state.db.save("proxies", row)
    return public(row)


@router.get("/proxies")
async def all_proxies(request: Request):
    return [public(p) for p in request.app.state.db.all("proxies")]


@router.post("/proxies", status_code=201)
async def add_proxy(request: Request, item: Proxy):
    try:
        return create_proxy(request.app, item)
    except ValueError:
        raise HTTPException(422, "Invalid proxy host") from None


@router.patch("/proxies/{uid}")
async def edit_proxy(request: Request, uid: str, payload: dict):
    app = request.app
    current = app.state.db.one("proxies", uid)
    if not current:
        raise HTTPException(404, "Proxy not found")
    for p in app.state.db.all("profiles"):
        if p.get("proxy_id") == uid and app.state.runner.status(p["id"])["status"] != "stopped":
            raise HTTPException(409, "Stop dependent browsers before editing proxy")
    if set(payload) - set(Proxy.model_fields):
        raise HTTPException(422, "Unknown proxy field")
    try:
        update = Proxy.model_validate({**{k: current[k] for k in Proxy.model_fields if k != "password"}, **payload}).model_dump()
        validate_host(update["host"])
    except Exception:
        raise HTTPException(422, "Invalid proxy fields") from None
    if "password" in payload:
        try:
            if update["password"]:
                app.state.vault.put(uid, update["password"])
            elif current.get("password_key"):
                app.state.vault.delete(uid)
        except Exception:
            raise HTTPException(503, "System credential vault unavailable") from None
    row = {**current, **{k: v for k, v in update.items() if k != "password"}}
    if "password" in payload:
        row["password_key"] = uid if update["password"] else None
    row.update(status="unchecked", exit_ip=None, last_checked=None, error=None)
    return public(app.state.db.save("proxies", row))
