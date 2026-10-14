"""Lifecycle operations: independently close one browser at a time."""
import asyncio


class Lifecycle:
    def status(self, uid):
        return {"status": self.states.get(uid, "stopped"), "error": self.errors.get(uid)}

    async def _closed(self, uid, context):
        async with self.lock:
            if self.running.get(uid) is context:
                self.running.pop(uid, None)
                self.states[uid] = "stopped"

    async def stop(self, uid):
        async with self.lock:
            context = self.running.pop(uid, None)
            self.states[uid] = "stopped"
            if context:
                await context.close()
            return self.status(uid)

    async def shutdown(self):
        for uid in list(self.running):
            await self.stop(uid)
        if self.driver:
            await self.driver.stop()
            self.driver = None

    def watch(self, uid, context):
        context.on("close", lambda: asyncio.create_task(self._closed(uid, context)))
