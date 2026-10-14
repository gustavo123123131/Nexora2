"""Localhost-bound management API and bundled desktop-style interface."""
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
import json

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import storage_dir
from .database import Database
from .runner import Runner
from .security import SecretStore, load_token
from .profile_routes import router as profiles
from .proxy_routes import router as proxies
from .system_routes import router as system
from .api_extensions import router as actions

WEB = Path(__file__).resolve().parent.parent / "web"


def create_app(root=None, runner=None, secrets=None):
    root = Path(root or storage_dir()).resolve()
    db = Database(root)
    vault = secrets or SecretStore()
    engine = runner or Runner(root, vault)
    token = load_token(root)

    @asynccontextmanager
    async def lifespan(app):
        yield
        await engine.shutdown()

    app = FastAPI(title="Nexora2 Local API", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.db, app.state.vault = db, vault
    app.state.runner, app.state.token = engine, token
    app.state.events = []

    @app.middleware("http")
    async def protect(request: Request, call_next):
        if request.url.hostname not in ("localhost", "127.0.0.1", "::1"):
            return JSONResponse({"detail": "Localhost only"}, status_code=403)
        origin = request.headers.get("origin")
        if origin and urlsplit(origin).hostname not in ("localhost", "127.0.0.1", "::1"):
            return JSONResponse({"detail": "Origin denied"}, status_code=403)
        if request.url.path.startswith("/api/") and request.headers.get("x-app-token") != token:
            return JSONResponse({"detail": "Invalid local token"}, status_code=403)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        errors = [{"loc": list(e["loc"]), "type": e["type"], "msg": e["msg"]}
                  for e in exc.errors()]
        return JSONResponse({"detail": errors}, status_code=422)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        html = (WEB / "index.html").read_text(encoding="utf-8")
        return html.replace("__NEXORA_TOKEN__", json.dumps(token))

    app.mount("/static", StaticFiles(directory=WEB), name="static")
    for subrouter in (profiles, proxies, system, actions):
        app.include_router(subrouter, prefix="/api")
    return app


app = create_app()
