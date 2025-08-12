import { useEffect, useRef, useState } from "react"

function buildWsUrl() {
  const base = (process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL || "").replace(/\/$/, "")
  const wsBase = base.startsWith("https") ? base.replace("https", "wss") : base.replace("http", "ws")
  return `${wsBase}/api/ws/notifications`
}

export default function useNotificationsWS() {
  const [notifs, setNotifs] = useState([])
  const wsRef = useRef(null)

  useEffect(() => {
    const url = buildWsUrl()
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data)
        if (msg.type === 'notification' && msg.data) {
          setNotifs(prev => [msg.data, ...prev].slice(0, 100))
        }
      } catch {}
    }
    ws.onerror = () => {}
    ws.onclose = () => {}
    return () => { try { ws.close() } catch {} }
  }, [])

  return notifs
}