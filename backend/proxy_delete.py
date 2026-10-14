"""Delete one proxy without affecting unrelated profiles."""
from fastapi import APIRouter, Request, HTTPException
from .profile_helpers import stamp

router = APIRouter()


@router.delete("/proxies/{uid}")
async def delete_proxy(request: Request, uid: str):
    app = request.app
    row = app.state.db.one("proxies", uid)
    if row is None:
        raise HTTPException(404, "Proxy not found")
    attached = [p for p in app.state.db.all("profiles") if p.get("proxy_id") == uid]
    if any(app.state.runner.status(p["id"])["status"] != "stopped" for p in attached):
        raise HTTPException(409, "Stop attached browsers before removing proxy")
    if row.get("password_key"):
        try:
            app.state.vault.delete(uid)
        except Exception:
            raise HTTPException(503, "System credential vault unavailable") from None
    for profile in attached:
        profile.update(proxy_id=None, updated_at=stamp())
        app.state.db.save("profiles", profile)
    app.state.db.remove("proxies", uid)
    return {"deleted": True, "disassociated_profiles": len(attached)}
