import asyncio
import time

class GlobalRateLimiter:
    def __initуд
    def __init__(self, delay=1.5):
        self.delay = delay
        self.last_call = 0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = time.monotonic()
            diff = now - self.last_call
            if diff < self.delay:
                await asyncio.sleep(self.delay - diff)
            self.last_call = time.monotonic()
