import { useEffect, useRef, useState } from "react"

function buildWsUrl(symbolsCsv) {
  const base = (process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL || "").replace(/\/$/, "")
  const wsBase = base.startsWith("https") ? base.replace("https", "wss") : base.replace("http", "ws")
  return `${wsBase}/api/ws/quotes?symbols=${encodeURIComponent(symbolsCsv)}`
}

export default function useQuotesWS(symbols) {
  const [quotes, setQuotes] = useState({})
  const wsRef = useRef(null)
  const csv = (symbols || []).filter(Boolean).join(',')

  useEffect(() => {
    if (!csv) return
    const url = buildWsUrl(csv)
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.type === 'quotes' && Array.isArray(msg.data)) {
          const next = {}
          msg.data.forEach(q => { if (q?.symbol) next[q.symbol] = q })
          setQuotes(next)
        }
      } catch {}
    }
    ws.onerror = () => {}
    ws.onclose = () => {}
    return () => { try { ws.close() } catch {} }
  }, [csv])

  return quotes
}