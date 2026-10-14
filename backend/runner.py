"""Playwright execution, using a separate persistent directory per profile."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from .browser_launch import launch
from .devices import catalog
from .runner_lifecycle import Lifecycle


class Runner(Lifecycle):
    def __init__(self, root, secrets):
        self.root = Path(root).resolve() / "profiles"
        self.root.mkdir(parents=True, exist_ok=True)
        self.secrets = secrets
        self.driver = None
        self.running = {}
        self.states = {}
        self.errors = {}
        self.lock = asyncio.Lock()
        self.driver_lock = asyncio.Lock()

    async def ensure(self):
        async with self.driver_lock:
            if self.driver is None:
                self.driver = await async_playwright().start()
            return self.driver

    async def devices(self):
        return catalog(await self.ensure())

    async def start(self, profile, proxy, limit):
        uid = profile["id"]
        async with self.lock:
            if uid in self.running or self.states.get(uid) == "starting":
                raise ValueError("Profile already running")
            if len(self.running) >= limit:
                raise ValueError("Simultaneous profile limit reached")
            self.states[uid] = "starting"
            self.errors.pop(uid, None)
            try:
                driver = await self.ensure()
                if profile["device"] not in {d["name"] for d in catalog(driver)}:
                    raise ValueError("Unsupported device preset")
                ctx = await launch(driver, profile, proxy, self.secrets, self.root / uid / "browser")
                self.running[uid] = ctx
                self.states[uid] = "running"
                self.watch(uid, ctx)
                return self.status(uid)
            except Exception as exc:
                self.states[uid] = "stopped"
                self.errors[uid] = f"Launch failed ({type(exc).__name__})"
                raise RuntimeError(self.errors[uid]) from None
