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


def macd(series: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
  ema_fast = ema(series, fast)
  ema_slow = ema(series, slow)
  line = [None if (a is None or b is None) else (a - b) for a, b in zip(ema_fast, ema_slow)]
  # For signal, filter out None progressively
  seq = []
  for v in line:
    seq.append(0.0 if v is None else v)
  sig = ema(seq, signal)
  hist = [None if (l is None or s is None) else (l - s) for l, s in zip(line, sig)]
  return line, sig, hist


def stochastic_kd(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3):
  k_vals: List[float] = [None] * len(closes)
  for i in range(len(closes)):
    if i < k_period - 1:
      continue
    hh = max(highs[i - k_period + 1 : i + 1])
    ll = min(lows[i - k_period + 1 : i + 1])
    denom = hh - ll
    k = ((closes[i] - ll) / denom * 100.0) if denom else None
    k_vals[i] = k
  # D is SMA of K
  d_vals = sma([0.0 if v is None else v for v in k_vals], d_period)
  return k_vals, d_vals


def compute_all_daily(bars: List[Dict[str, float]]) -> Dict[str, Any]:
  # compute a selection of indicators; return latest values
  if not bars:
    return {}
  closes = _values(bars, "c")
  highs = _values(bars, "h")
  lows = _values(bars, "l")
  opens = _values(bars, "o")
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
  # MACD
  macd_line, macd_sig, macd_hist = macd(closes)
  res["macd_line"] = last_valid(macd_line)
  res["macd_signal"] = last_valid(macd_sig)
  res["macd_hist"] = last_valid(macd_hist)
  # Stochastic
  k_vals, d_vals = stochastic_kd(highs, lows, closes, 14, 3)
  res["stoch_k"] = last_valid(k_vals)
  res["stoch_d"] = last_valid(d_vals)
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
  # ADR20: average daily range of last 20 sessions
  if len(highs) >= 20:
    ranges = [highs[i]-lows[i] for i in range(max(0, len(highs)-20), len(highs))]
    adr20 = sum(ranges)/len(ranges) if ranges else None
    res["adr20"] = adr20
  # Gap % today vs previous close
  if len(closes) >= 2 and len(opens) >= 1:
    prev_close = closes[-2]
    today_open = opens[-1]
    res["gapPct"] = ((today_open - prev_close) / prev_close * 100.0) if prev_close else None
  return res