import os
import time
import logging
import requests
from typing import Dict, List, Any, Tuple
from functools import lru_cache

logger = logging.getLogger(__name__)

POLY_BASE = "https://api.polygon.io"

# simple in-memory cache with TTL
class TTLCache:
    def __init__(self):
        self.data: Dict[str, Tuple[float, Any]] = {}
        self.ttl_default = 60.0

    def get(self, key: str):
        item = self.data.get(key)
        if not item:
            return None
        exp, val = item
        if exp < time.time():
            self.data.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any, ttl: float | None = None):
        self.data[key] = (time.time() + (ttl or self.ttl_default), value)

cache = TTLCache()

class PolygonClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def _get(self, path: str, params: Dict[str, Any] | None = None, cache_ttl: float | None = None) -> Any:
        if params is None:
            params = {}
        params["apiKey"] = self.api_key
        url = f"{POLY_BASE}{path}"
        cache_key = f"GET:{url}:{sorted(params.items())}"
        if cache_ttl:
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
        # retry with backoff for 429
        delay = 0.5
        for i in range(4):
            r = requests.get(url, params=params, timeout=20)
            if r.status_code == 429:
                time.sleep(delay)
                delay *= 2
                continue
            r.raise_for_status()
            j = r.json()
            if cache_ttl:
                cache.set(cache_key, j, cache_ttl)
            return j
        r.raise_for_status()

    def search_symbols(self, q: str, limit: int = 25) -> List[Dict[str, Any]]:
        data = self._get(
            "/v3/reference/tickers",
            {
                "search": q,
                "active": "true",
                "market": "stocks",
                "limit": limit,
            },
            cache_ttl=300,
        )
        results = []
        for t in data.get("results", [])[:limit]:
            results.append(
                {
                    "symbol": t.get("ticker"),
                    "name": t.get("name"),
                    "exchange": t.get("primary_exchange"),
                    "locale": t.get("locale"),
                    "currency": t.get("currency_name"),
                    "sector": (t.get("sic_description") or "")[:64],
                    "industry": (t.get("sic_description") or "")[:64],
                    "logoUrl": (t.get("branding", {}) or {}).get("logo_url"),
                }
            )
        return results

    def get_logo(self, symbol: str) -> str | None:
        try:
            d = self._get(f"/v3/reference/tickers/{symbol}", cache_ttl=3600)
            branding = d.get("results", {}).get("branding", {})
            url = branding.get("logo_url")
            if url:
                joiner = "&" if "?" in url else "?"
                return f"{url}{joiner}apiKey={self.api_key}"
            return None
        except Exception as e:
            logger.warning("logo fetch failed: %s", e)
            return None

    def get_bars(self, symbol: str, multiplier: int, timespan: str, _from: str, to: str) -> List[Dict[str, Any]]:
        params = {"adjusted": "true", "sort": "asc", "limit": 50000}
        # cache per symbol/interval/window for 5 minutes
        j = self._get(f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{_from}/{to}", params, cache_ttl=300)
        bars = []
        for it in j.get("results", []) or []:
            bars.append({
                "t": int(it["t"]) // 1000,
                "o": float(it["o"]),
                "h": float(it["h"]),
                "l": float(it["l"]),
                "c": float(it["c"]),
                "v": float(it.get("v", 0)),
            })
        return bars

    def get_quotes_snapshot(self, symbols: List[str]) -> List[Dict[str, Any]]:
        tickers = ",".join(symbols)
        try:
            j = self._get("/v2/snapshot/locale/us/markets/stocks/tickers", {"tickers": tickers}, cache_ttl=2)
            out = []
            for item in j.get("tickers", []) or []:
                t = item.get("ticker")
                last = (item.get("lastTrade") or {}).get("p") or (item.get("lastQuote") or {}).get("p")
                prev = (item.get("prevDay") or {}).get("c")
                vol = (item.get("day") or {}).get("v") or 0
                chg = None
                if last is not None and prev not in (None, 0):
                    chg = (last - prev) / prev * 100.0
                out.append({
                    "symbol": t,
                    "last": last,
                    "prevClose": prev,
                    "changePct": chg,
                    "volume": vol,
                })
            return out
        except Exception as e:
            logger.warning("snapshot failed: %s", e)
            out = []
            for s in symbols:
                try:
                    lt = self._get(f"/v2/last/trade/{s}", cache_ttl=2)
                    last = (lt.get("results") or {}).get("p")
                    prev = None
                    try:
                        prevj = self._get(f"/v2/aggs/ticker/{s}/prev", {"adjusted": "true"}, cache_ttl=60)
                        pr = (prevj.get("results") or [{}])[0]
                        prev = pr.get("c")
                    except Exception:
                        pass
                    chg = None
                    if last is not None and prev not in (None, 0):
                        chg = (last - prev) / prev * 100.0
                    out.append({"symbol": s, "last": last, "prevClose": prev, "changePct": chg, "volume": None})
                except Exception:
                    out.append({"symbol": s, "last": None, "prevClose": None, "changePct": None, "volume": None})
            return out