"""Bulk import with explicit formats and no leaked raw input lines."""
from fastapi import APIRouter, Request, HTTPException
from .proxy_helpers import parse_line
from .proxy_routes import create_proxy
from .schemas import ProxyImport

router = APIRouter()


@router.post("/proxies/import")
async def import_proxies(request: Request, batch: ProxyImport):
    lines = [line for line in batch.lines.splitlines() if line.strip()]
    if len(lines) > 1000:
        raise HTTPException(422, "Maximum 1000 proxies per import")
    parsed = []
    for number, line in enumerate(lines, 1):
        try:
            parsed.append(parse_line(line))
        except Exception:
            raise HTTPException(422, f"Invalid proxy format on line {number}") from None
    return {"imported": [create_proxy(request.app, item) for item in parsed]}
