import logging
import threading
import time
from dataclasses import dataclass
from enum import IntEnum

import httpx

from config import CACHE_TTL_SECONDS, JEEDOM_STATUS_URL

logger = logging.getLogger(__name__)


class RoofState(IntEnum):
    """État du toit Jeedom : 0 = ouvert, 1 = fermé."""

    OPEN = 0
    CLOSED = 1


@dataclass
class CachedRoofStatus:
    state: RoofState | None
    error: str | None
    fetched_at: float


class RoofStatusClient:
    """Client Jeedom avec cache TTL pour l'état du toit."""

    def __init__(self, url: str = JEEDOM_STATUS_URL, cache_ttl: float = CACHE_TTL_SECONDS):
        self._url = url
        self._cache_ttl = cache_ttl
        self._lock = threading.Lock()
        self._cache: CachedRoofStatus | None = None

    def get_status(self) -> CachedRoofStatus:
        with self._lock:
            now = time.monotonic()
            if self._cache is not None and (now - self._cache.fetched_at) < self._cache_ttl:
                return self._cache

        status = self._fetch()
        with self._lock:
            self._cache = status
        return status

    def _fetch(self) -> CachedRoofStatus:
        now = time.monotonic()
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self._url)
                response.raise_for_status()
                raw = response.text.strip()
            state = RoofState(int(raw))
            logger.debug("État toit Jeedom : %s (%s)", state.name, raw)
            return CachedRoofStatus(state=state, error=None, fetched_at=now)
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Impossible de lire l'état du toit : %s", exc)
            return CachedRoofStatus(state=None, error=str(exc), fetched_at=now)

    def is_open(self) -> bool | None:
        status = self.get_status()
        if status.state is None:
            return None
        return status.state == RoofState.OPEN

    def shutter_state(self) -> int:
        """Retourne ShutterState Alpaca (0=Open, 1=Closed, 4=Error)."""
        status = self.get_status()
        if status.state is None:
            return 4
        return int(status.state)
