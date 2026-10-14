"""Profile CRUD; duplicate creates fresh browser storage, never copies cookies."""
from fastapi import APIRouter, Request, HTTPException
from .profile_helpers import valid_profile, new_profile, with_status, require, stamp, proxy_warning
from .schemas import Profile

router = APIRouter()


@router.get("/profiles")
async def list_profiles(request: Request):
    app = request.app
    return [with_status(app, item) for item in app.state.db.all("profiles")]


@router.post("/profiles", status_code=201)
async def create_profile(request: Request, payload: Profile):
    app = request.app
    data = await valid_profile(app, payload.model_dump())
    profile = app.state.db.save("profiles", new_profile(data))
    return {**with_status(app, profile), "warning": proxy_warning(app.state.db, profile)}


@router.patch("/profiles/{uid}")
async def edit_profile(request: Request, uid: str, payload: dict):
    app = request.app
    current = require(app.state.db, uid)
    if app.state.runner.status(uid)["status"] != "stopped":
        raise HTTPException(409, "Stop the browser before editing")
    fields = {key: current[key] for key in Profile.model_fields}
    data = await valid_profile(app, {**fields, **payload})
    updated = app.state.db.save("profiles", {**current, **data, "updated_at": stamp()})
    return {**with_status(app, updated), "warning": proxy_warning(app.state.db, updated)}


@router.post("/profiles/{uid}/duplicate", status_code=201)
async def duplicate_profile(request: Request, uid: str):
    app = request.app
    original = require(app.state.db, uid)
    data = {key: original[key] for key in Profile.model_fields}
    data["name"] = (original["name"][:70] + " (cópia)")
    data["proxy_id"] = None
    copy = app.state.db.save("profiles", new_profile(data))
    return with_status(app, copy)
