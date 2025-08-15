import time
import logging
import requests
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)
BASE = "https://finnhub.io/api/v1"

class TTLCache:
    def __init__(self):
        self.data: Dict[str, Tuple[float, Any]] = {}
    def get(self, key):
        item = self.data.get(key)
        if not item:
            return None
        exp, val = item
        if exp < time.time():
            self.data.pop(key, None)
            return None
        return val
    def set(self, key, val, ttl: float):
        self.data[key] = (time.time() + ttl, val)

_cache = TTLCache()

class FinnhubClient:
    def __init__(self, token: str | None):
        self.token = token or ""

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None, ttl: float | None = None) -> Any:
        if not self.token:
            return {}
        params = params or {}
        params["token"] = self.token
        url = f"{BASE}{path}"
        key = f"GET:{url}:{sorted(params.items())}"
        if ttl:
            cached = _cache.get(key)
            if cached is not None:
                return cached
        delay = 0.5
        for _ in range(4):
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 429:
                time.sleep(delay); delay *= 2; continue
            r.raise_for_status()
            j = r.json()
            if ttl: _cache.set(key, j, ttl)
            return j
        r.raise_for_status()

    def company_profile(self, symbol: str) -> Dict[str, Any]:
        try:
            return self._get("/stock/profile2", {"symbol": symbol}, ttl=3600) or {}
        except Exception as e:
            logger.warning("finnhub profile failed: %s", e)
            return {}

    def metrics(self, symbol: str) -> Dict[str, Any]:
        try:
            j = self._get("/stock/metric", {"symbol": symbol, "metric": "all"}, ttl=1800)
            return j.get("metric", {}) if isinstance(j, dict) else {}
        except Exception as e:
            logger.warning("finnhub metrics failed: %s", e)
            return {}

    def quote(self, symbol: str) -> Dict[str, Any]:
        try:
            return self._get("/quote", {"symbol": symbol}, ttl=2) or {}
        except Exception:
            return {}