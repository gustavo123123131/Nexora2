"""Additional API operations; kept separate from core CRUD."""
from fastapi import APIRouter
from .profile_actions import router as profile_actions
from .proxy_import import router as proxy_import
from .proxy_check import router as proxy_check
from .proxy_delete import router as proxy_delete

router = APIRouter()
for subrouter in (profile_actions, proxy_import, proxy_check, proxy_delete):
    router.include_router(subrouter)
