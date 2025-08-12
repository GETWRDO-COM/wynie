import React, { useEffect, useState } from "react"
import { Bell, X } from "lucide-react"
import { Button } from "./ui/button"
import useNotificationsWS from "../hooks/useNotificationsWS"
import axios from "axios"

const BASE = (process.env.REACT_APP_BACKEND_URL || import.meta?.env?.REACT_APP_BACKEND_URL || "")

export default function NotificationsBell(){
  const live = useNotificationsWS()
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState([])

  useEffect(()=>{
    (async()=>{
      try { const { data } = await axios.get(`${BASE}/api/notifications?limit=25`); setItems(data) } catch {}
    })()
  },[])

  useEffect(()=>{ if (live && live.length) setItems(prev => [...live, ...prev].slice(0, 50)) }, [live])

  const unread = items.length

  return (
    <div className="relative">
      <Button size="sm" variant="secondary" onClick={()=> setOpen(!open)}>
        <Bell className="w-4 h-4 mr-1"/> {unread}
      </Button>
      {open && (
        <div className="absolute right-0 mt-2 w-96 max-h-80 overflow-auto border rounded bg-card shadow">
          <div className="flex items-center justify-between px-3 py-2 border-b">
            <div className="text-sm font-medium">Notifications</div>
            <button onClick={()=> setOpen(false)}><X className="w-4 h-4"/></button>
          </div>
          <div className="divide-y text-sm">
            {items.length===0 && <div className="px-3 py-4 text-muted-foreground">No notifications yet.</div>}
            {items.map(n => (
              <div key={n.id} className="px-3 py-2">
                <div className="font-medium">{n.symbol}</div>
                <div className="text-muted-foreground text-xs">{n.message}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}