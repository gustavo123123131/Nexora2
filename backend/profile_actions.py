"""Browser actions and safe deletion of per-profile local data."""
import shutil
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException
from .profile_helpers import require, stamp

router = APIRouter()


def event(app, action, uid):
    from .events import record
    record(app, action, uid)


@router.post("/profiles/{uid}/start")
async def start_profile(request: Request, uid: str):
    app = request.app
    profile = require(app.state.db, uid)
    proxy = app.state.db.one("proxies", profile["proxy_id"]) if profile.get("proxy_id") else None
    try:
        status = await app.state.runner.start(profile, proxy, app.state.db.settings()["max_active"])
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from None
    except Exception:
        event(app, "launch_failed", uid)
        raise HTTPException(503, "Browser launch failed; check diagnostics") from None
    event(app, "started", uid)
    return status


@router.post("/profiles/{uid}/stop")
async def stop_profile(request: Request, uid: str):
    app = request.app
    require(app.state.db, uid)
    await app.state.runner.stop(uid)
    event(app, "stopped", uid)
    return app.state.runner.status(uid)


@router.delete("/profiles/{uid}")
async def delete_profile(request: Request, uid: str):
    app = request.app
    require(app.state.db, uid)
    try:
        UUID(uid)
    except ValueError:
        raise HTTPException(422, "Invalid profile identifier") from None
    await app.state.runner.stop(uid)
    directory = app.state.runner.root / uid
    if directory.exists():
        shutil.rmtree(directory)
    app.state.db.remove("profiles", uid)
    event(app, "deleted", uid)
    return {"deleted": True}
