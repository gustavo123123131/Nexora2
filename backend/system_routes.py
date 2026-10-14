"""Dashboard, device presets, diagnostics and preferences."""
import os
import platform
from pathlib import Path
from fastapi import APIRouter, Request

from .schemas import Settings

router = APIRouter()


@router.get("/devices")
async def devices(request: Request):
    return await request.app.state.runner.devices()


@router.get("/dashboard")
async def dashboard(request: Request):
    app = request.app
    profiles = app.state.db.all("profiles")
    proxies = app.state.db.all("proxies")
    return {"total": len(profiles),
            "active": sum(app.state.runner.status(p["id"])["status"] == "running" for p in profiles),
            "proxies": len(proxies),
            "proxies_ok": sum(p["status"] == "ok" for p in proxies)}


@router.get("/settings")
async def get_settings(request: Request):
    settings = dict(request.app.state.db.settings())
    settings.pop("id", None)
    return settings


@router.put("/settings")
async def update_settings(request: Request, payload: Settings):
    app = request.app
    return app.state.db.save("settings", {"id": "settings", **payload.model_dump()})


@router.get("/diagnostics")
async def diagnostics(request: Request):
    runner = request.app.state.runner
    driver = await runner.ensure()
    return {"platform": platform.platform(), "cpu_threads": os.cpu_count(),
            "chromium_installed": Path(driver.chromium.executable_path).exists(),
            "webkit_installed": Path(driver.webkit.executable_path).exists(),
            "storage": str(request.app.state.db.root),
            "running": len(runner.running),
            "note": "Emulação Playwright; não representa aparelho físico nem Safari do iOS."}


@router.get("/logs")
async def logs(request: Request):
    from .events import recent
    return recent(request.app)
