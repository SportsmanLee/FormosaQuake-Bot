"""Simple jittered exponential backoff helper."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass


@dataclass
class Backoff:
    base_seconds: float
    max_seconds: float
    factor: float = 2.0

    def next_sleep(self, failures: int) -> float:
        """Return sleep seconds with jitter based on failure count (>=1)."""

        if failures <= 0:
            return 0.0
        raw = self.base_seconds * (self.factor ** (failures - 1))
        capped = min(raw, self.max_seconds)
        jitter = random.uniform(0, capped * 0.1)
        return capped + jitter


async def sleep_with_backoff(backoff: Backoff, failures: int) -> None:
    await asyncio.sleep(backoff.next_sleep(failures))


__all__ = ["Backoff", "sleep_with_backoff"]