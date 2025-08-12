from __future__ import annotations
from typing import List, Dict, Any

# Basic indicator implementations operating on daily bars list with keys t,o,h,l,c,v

def _values(bars: List[Dict[str, float]], key: str) -> List[float]:
  return [float(b.get(key)) for b in bars]


def sma(series: List[float], n: int) -> List[float]:
  out: List[float] = []
  s = 0.0
  q: List[float] = []
  for x in series:
    q.append(x)
    s += x
    if len(q) > n:
      s -= q.pop(0)
    out.append(s / n if len(q) == n else None)
  return out


def ema(series: List[float], n: int) -> List[float]:
  out: List[float] = []
  k = 2 / (n + 1)
  e = None
  for x in series:
    if e is None:
      e = x
    else:
      e = x * k + e * (1 - k)
    out.append(e)
  return [None if i < n - 1 else out[i] for i in range(len(out))]


def rsi(series: List[float], n: int = 14) -> List[float]:
  out: List[float] = [None] * len(series)
  gains = 0.0
  losses = 0.0
  for i in range(1, n + 1):
    ch = series[i] - series[i - 1]
    gains += max(0.0, ch)
    losses += max(0.0, -ch)
  avg_g = gains / n
  avg_l = losses / n
  for i in range(n + 1, len(series)):
    ch = series[i] - series[i - 1]
    gain = max(0.0, ch)
    loss = max(0.0, -ch)
    avg_g = (avg_g * (n - 1) + gain) / n
    avg_l = (avg_l * (n - 1) + loss) / n
    rs = 100.0 if avg_l == 0 else avg_g / avg_l
    out[i] = 100 - 100 / (1 + rs)
  return out


def true_range(h: List[float], l: List[float], c: List[float]) -> List[float]:
  out = [None]
  for i in range(1, len(c)):
    tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
    out.append(tr)
  return out


def atr(bars: List[Dict[str, float]], n: int = 14) -> List[float]:
  h = _values(bars, "h")
  l = _values(bars, "l")
  c = _values(bars, "c")
  tr = true_range(h, l, c)
  # Wilder's smoothing
  out: List[float] = [None] * len(c)
  s = sum([x for x in tr[1 : n + 1]])
  prev = s / n if n + 1 <= len(tr) else None
  if prev is None:
    return out
  out[n] = prev
  for i in range(n + 1, len(tr)):
    prev = (prev * (n - 1) + tr[i]) / n
    out[i] = prev
  return out


def bollinger(series: List[float], n: int = 20, k: float = 2.0):
  import math
  out_mid = sma(series, n)
  out_b = [None] * len(series)
  out_t = [None] * len(series)
  out_bw = [None] * len(series)
  for i in range(len(series)):
    if i < n - 1:
      continue
    window = series[i - n + 1 : i + 1]
    mean = sum(window) / n
    var = sum((x - mean) ** 2 for x in window) / n
    sd = math.sqrt(var)
    out_b[i] = mean - k * sd
    out_t[i] = mean + k * sd
    out_bw[i] = (out_t[i] - out_b[i]) / mean if mean else None
  return out_mid, out_b, out_t, out_bw


def compute_all_daily(bars: List[Dict[str, float]]) -> Dict[str, Any]:
  # compute a selection of indicators; return latest values
  if not bars:
    return {}
  closes = _values(bars, "c")
  highs = _values(bars, "h")
  lows = _values(bars, "l")
  vols = _values(bars, "v")
  res: Dict[str, Any] = {}

  def last_valid(arr):
    for x in reversed(arr):
      if x is not None:
        return x
    return None

  res["sma20"] = last_valid(sma(closes, 20))
  res["sma50"] = last_valid(sma(closes, 50))
  res["sma200"] = last_valid(sma(closes, 200))
  res["ema8"] = last_valid(ema(closes, 8))
  res["ema21"] = last_valid(ema(closes, 21))
  res["ema50"] = last_valid(ema(closes, 50))
  res["rsi14"] = last_valid(rsi(closes, 14))
  atr14 = atr(bars, 14)
  res["atr14"] = last_valid(atr14)
  # Bollinger
  mid, lb, ub, bw = bollinger(closes, 20, 2.0)
  res["bb_mid"] = last_valid(mid)
  res["bb_lb"] = last_valid(lb)
  res["bb_ub"] = last_valid(ub)
  res["bb_bw"] = last_valid(bw)
  # 52w high/low
  hi52 = max(highs[-252:]) if len(highs) >= 2 else None
  lo52 = min(lows[-252:]) if len(lows) >= 2 else None
  last = closes[-1]
  if hi52 is not None and lo52 is not None:
    res["pct_to_hi52"] = (hi52 - last) / hi52 * 100.0 if hi52 else None
    res["pct_above_lo52"] = (last - lo52) / lo52 * 100.0 if lo52 else None
    res["hi52"] = hi52
    res["lo52"] = lo52
  # Avg Volume and relative/run-rate
  if len(vols) >= 20:
    avg20 = sum(vols[-20:]) / 20.0
    res["avgVol20d"] = avg20
    res["runRate20d"] = vols[-1] / avg20 if avg20 else None
    res["relVol"] = vols[-1] / avg20 if avg20 else None
  # gap % (today open vs prev close) if we had opens; fallback using h/l and prev close not available in bars; skip.
  # ADR20: average daily range of last 20 sessions
  if len(highs) >= 20:
    ranges = [highs[i]-lows[i] for i in range(max(0, len(highs)-20), len(highs))]
    adr20 = sum(ranges)/len(ranges) if ranges else None
    res["adr20"] = adr20
  return res