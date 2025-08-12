import React, { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { Input } from "../components/ui/input"
import { Button } from "../components/ui/button"
import { getSettings, saveSettings } from "../services/api"

export default function Settings(){
  const [polygon, setPolygon] = useState("")
  const [finnhub, setFinnhub] = useState("")
  const [status, setStatus] = useState(null)

  useEffect(()=>{
    (async()=>{
      try{ const s = await getSettings(); setStatus(s) } catch {}
    })()
  },[])

  const onSave = async ()=>{
    await saveSettings({ polygon: polygon || undefined, finnhub: finnhub || undefined })
    setPolygon(""); setFinnhub("")
    const s = await getSettings(); setStatus(s)
  }

  return (
    <Card>
      <CardHeader className="py-2"><CardTitle className="text-base">Settings</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="text-sm text-muted-foreground">Keys stored server-side. Booleans below indicate if a key is set.</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-sm">Polygon API Key (set: {String(status?.polygon)})</label>
            <Input placeholder="••••••" value={polygon} onChange={(e)=> setPolygon(e.target.value)} />
          </div>
          <div>
            <label className="text-sm">Finnhub API Key (set: {String(status?.finnhub)})</label>
            <Input placeholder="••••••" value={finnhub} onChange={(e)=> setFinnhub(e.target.value)} />
          </div>
        </div>
        <Button onClick={onSave}>Save</Button>
      </CardContent>
    </Card>
  )
}