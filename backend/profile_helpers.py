"""Profile validation and data mapping."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from uuid import uuid4
from fastapi import HTTPException
from pydantic import ValidationError
from .schemas import Profile


def stamp():
    return datetime.now(timezone.utc).isoformat()


async def valid_profile(app, payload):
    if set(payload) - set(Profile.model_fields):
        raise HTTPException(422, "Unknown profile field")
    try:
        model = Profile.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(422, exc.errors(include_url=False)) from None
    data = model.model_dump()
    if (data["viewport_width"] is None) != (data["viewport_height"] is None):
        raise HTTPException(422, "Viewport width and height must be supplied together")
    try:
        ZoneInfo(data["timezone"])
    except ZoneInfoNotFoundError:
        raise HTTPException(422, "Invalid IANA timezone") from None
    names = {item["name"] for item in await app.state.runner.devices()}
    if data["device"] not in names:
        raise HTTPException(422, "Device not available in installed Playwright")
    if data["proxy_id"] and not app.state.db.one("proxies", data["proxy_id"]):
        raise HTTPException(422, "Proxy not found")
    return data


def new_profile(data):
    moment = stamp()
    return {"id": str(uuid4()), **data, "created_at": moment, "updated_at": moment}


def with_status(app, profile):
    return {**profile, **app.state.runner.status(profile["id"])}


def require(db, uid):
    profile = db.one("profiles", uid)
    if profile is None:
        raise HTTPException(404, "Profile not found")
    return profile


def proxy_warning(db, profile):
    if not profile.get("proxy_id") or not db.settings()["warn_duplicate_proxy"]:
        return None
    in_use = [p for p in db.all("profiles") if p["id"] != profile["id"]
              and p.get("proxy_id") == profile["proxy_id"]]
    return "Proxy already assigned to another profile" if in_use else None
