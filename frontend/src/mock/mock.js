/*
  Mock data and helpers for Deepvue-style workstation.
  - Universe generator with consistent random values
  - OHLC generator per symbol
  - RS/AS computations (percentile ranks over windows)
  - LocalStorage helpers for presets, drawings, layouts
*/

// Simple deterministic RNG so mock data stays stable across reloads
function mulberry32(seed) {
  return function () {
    let t = (seed += 0x6d2b79f5)
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

const SECTORS = [
  "Technology",
  "Health Care",
  "Financials",
  "Consumer Discretionary",
  "Industrials",
  "Energy",
  "Materials",
  "Utilities",
  "Real Estate",
  "Communication Services",
]

const INDUSTRIES = [
  "Software",
  "Semiconductors",
  "Banks",
  "Retail",
  "Aerospace",
  "Oil & Gas",
  "Metals & Mining",
  "Electric Utilities",
  "REITs",
  "Media",
]

const SYMBOLS = [
  "AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AMD","NFLX","AVGO",
  "INTC","ORCL","CRM","ADBE","CSCO","COIN","PLTR","SNOW","UBER","SHOP",
  "SQ","PYPL","MU","QCOM","TXN","AMAT","LRCX","ASML","TSM","MRNA",
  "PFE","JNJ","UNH","LLY","XOM","CVX","OXY","BA","GE","CAT",
  "GS","JPM","MS","BAC","C","SPY","QQQ","IWM","ARKK","HOOD"
]

// Cache for generated candles per symbol
const ohlcCache = new Map()

function genOhlc(symbol, days = 180, seed = 1) {
  const key = symbol + "_" + days
  if (ohlcCache.has(key)) return ohlcCache.get(key)
  const rnd = mulberry32(seed + symbol.length)
  let px = 50 + rnd() * 250
  const out = []
  let ts = Date.now() - days * 24 * 60 * 60 * 1000
  for (let i = 0; i &lt; days; i++) {
    const drift = (rnd() - 0.5) * 2 // -1..1
    const vol = 0.01 + rnd() * 0.03
    const change = px * (drift * vol)
    const open = px
    px = Math.max(1, px + change)
    const close = px
    const high = Math.max(open, close) * (1 + rnd() * 0.01)
    const low = Math.min(open, close) * (1 - rnd() * 0.01)
    const volume = Math.floor(1_000_000 + rnd() * 5_000_000)
    out.push({
      time: Math.floor(ts / 1000),
      open: +open.toFixed(2),
      high: +high.toFixed(2),
      low: +low.toFixed(2),
      close: +close.toFixed(2),
      volume,
    })
    ts += 24 * 60 * 60 * 1000
  }
  ohlcCache.set(key, out)
  return out
}

// Compute SMA
function sma(arr, n, accessor = (d) => d) {
  const res = []
  let sum = 0
  for (let i = 0; i &lt; arr.length; i++) {
    sum += accessor(arr[i])
    if (i &gt;= n) sum -= accessor(arr[i - n])
    res.push(i &gt;= n - 1 ? sum / n : null)
  }
  return res
}

// RSI(14) basic implementation
function rsi(values, n = 14) {
  let gains = 0, losses = 0
  const res = Array(values.length).fill(null)
  for (let i = 1; i &lt;= n; i++) {
    const ch = values[i] - values[i - 1]
    if (ch &gt; 0) gains += ch; else losses -= ch
  }
  let avgGain = gains / n
  let avgLoss = losses / n
  for (let i = n + 1; i &lt; values.length; i++) {
    const ch = values[i] - values[i - 1]
    const gain = Math.max(0, ch)
    const loss = Math.max(0, -ch)
    avgGain = (avgGain * (n - 1) + gain) / n
    avgLoss = (avgLoss * (n - 1) + loss) / n
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
    res[i] = 100 - 100 / (1 + rs)
  }
  return res
}

// Universe generator
function getMockUniverse() {
  const rnd = mulberry32(42)
  const out = []
  for (let i = 0; i &lt; SYMBOLS.length; i++) {
    const s = SYMBOLS[i]
    const candles = genOhlc(s, 240, 100 + i)
    const closes = candles.map((c) =&gt; c.close)
    const last = closes.at(-1)
    const chg = ((last - closes.at(-2)) / closes.at(-2)) * 100
    const vToday = candles.at(-1).volume
    const avg20 = Math.round(candles.slice(-20).reduce((a, c) =&gt; a + c.volume, 0) / 20)
    const hi52 = Math.max(...candles.slice(-252).map((c) =&gt; c.high))
    const lo52 = Math.min(...candles.slice(-252).map((c) =&gt; c.low))
    const sector = SECTORS[Math.floor(rnd() * SECTORS.length)]
    const industry = INDUSTRIES[Math.floor(rnd() * INDUSTRIES.length)]

    const sma20 = sma(closes, 20)
    const sma50 = sma(closes, 50)
    const sma200 = sma(closes, 200)
    const rsi14 = rsi(closes, 14)

    const marketCap = Math.round((5 + rnd() * 500) * 1e8)

    out.push({
      symbol: s,
      description: `${s} Inc.`,
      sector,
      industry,
      marketCap,
      last: +last.toFixed(2),
      changePct: +chg.toFixed(2),
      volume: vToday,
      avgVol20d: avg20,
      runRate20d: +(vToday / Math.max(1, avg20)).toFixed(2),
      high52w: +hi52.toFixed(2),
      low52w: +lo52.toFixed(2),
      nextEarnings: new Date(Date.now() + (7 + Math.floor(rnd() * 60)) * 86400000).toISOString(),
      latestEarnings: new Date(Date.now() - (10 + Math.floor(rnd() * 60)) * 86400000).toISOString(),
      sma20: +sma20.at(-1)?.toFixed(2),
      sma50: +sma50.at(-1)?.toFixed(2),
      sma200: +sma200.at(-1)?.toFixed(2),
      rsi14: +rsi14.at(-1)?.toFixed(2) || 50,
      atr: +(last * (0.01 + rnd() * 0.03)).toFixed(2),
      prePct: +(rnd() * 2 - 1).toFixed(2),
      postPct: +(rnd() * 2 - 1).toFixed(2),
      relVol: +((vToday / Math.max(1, avg20))).toFixed(2),
      gapPct: +((candles.at(-1).open - closes.at(-2)) / closes.at(-2) * 100).toFixed(2),
      notes: "",
    })
  }
  return out
}

// Percentile rank helper
function percentile(values, v) {
  const sorted = [...values].sort((a,b) =&gt; a-b)
  const idx = sorted.findIndex((x) =&gt; x &gt; v)
  const rank = idx === -1 ? sorted.length : idx
  return Math.round((rank / sorted.length) * 100)
}

function computeRS(universe, windowDays = 63) { // ~3M trading days
  const returns = universe.map((row) =&gt; {
    const candles = genOhlc(row.symbol, 240, 100 + SYMBOLS.indexOf(row.symbol))
    const closes = candles.map((c) =&gt; c.close)
    const end = closes.at(-1)
    const start = closes.at(-(windowDays + 1)) || closes[0]
    return (end - start) / start
  })
  return universe.map((row, i) =&gt; percentile(returns, returns[i]))
}

function computeAS(universe, shortDays = 21, longDays = 63) {
  const accel = universe.map((row) =&gt; {
    const candles = genOhlc(row.symbol, 240, 100 + SYMBOLS.indexOf(row.symbol))
    const closes = candles.map((c) =&gt; c.close)
    const end = closes.at(-1)
    const s = closes.at(-(shortDays + 1)) || closes[0]
    const l = closes.at(-(longDays + 1)) || closes[0]
    const rocS = (end - s) / s
    const rocL = (end - l) / l
    return rocS - rocL
  })
  return universe.map((row, i) =&gt; percentile(accel, accel[i]))
}

// Local storage helpers
const LS = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v ? JSON.parse(v) : fallback } catch { return fallback }
  },
  set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)) } catch {}
  },
}

function getCandles(symbol, days = 180) { return genOhlc(symbol, days, 100 + SYMBOLS.indexOf(symbol)) }

export {
  getMockUniverse,
  getCandles,
  computeRS,
  computeAS,
  LS,
  SYMBOLS,
}