import React, { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { listWatchlists, createWatchlist, updateWatchlist, deleteWatchlist } from "../services/api"

const COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#22c55e","#f97316"]

export default function WatchlistsPanel({ onUseSymbols }){
  const [lists, setLists] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [newName, setNewName] = useState("")

  const active = useMemo(()=> lists.find(l=> l.id===activeId) || lists[0], [lists, activeId])

  async function load(){ try { const r = await listWatchlists(); setLists(r||[]) } catch {} }
  useEffect(()=>{ load() }, [])

  async function addList(){
    const name = newName.trim() || "My List"
    const body = { name, sections: [{ id: crypto.randomUUID(), name: "Core", color: COLORS[0], symbols: ["AAPL","MSFT","NVDA"] }] }
    try { const r = await createWatchlist(body.name, body.sections[0].symbols); // backward-compat
      // immediately upgrade to sections model
      await updateWatchlist(r.id, { sections: body.sections })
      setNewName("")
      await load()
      setActiveId(r.id)
    } catch {}
  }

  async function addSection(){
    if (!active) return
    const name = prompt("Section name?") || "Section"
    const color = COLORS[Math.floor(Math.random()*COLORS.length)]
    const sections = [...(active.sections||[]), { id: crypto.randomUUID(), name, color, symbols: [] }]
    await updateWatchlist(active.id, { sections }); await load()
  }

  async function addSymbol(sec){
    const val = prompt("Add symbol (e.g., TSLA)")
    if (!val) return
    const s = val.toUpperCase().trim()
    const sections = (active.sections||[]).map(x=> x.id===sec.id ? ({...x, symbols: [...(x.symbols||[]), s]}) : x)
    await updateWatchlist(active.id, { sections }); await load()
  }

  async function moveSymbol(sym, fromId, toId){
    const sections = (active.sections||[]).map(x=> {
      if (x.id===fromId){ return { ...x, symbols: (x.symbols||[]).filter(z=> z!==sym) } }
      if (x.id===toId){ return { ...x, symbols: [...(x.symbols||[]), sym] } }
      return x
    })
    await updateWatchlist(active.id, { sections }); await load()
  }

  async function setColor(secId, color){
    const sections = (active.sections||[]).map(x=> x.id===secId? ({...x, color}) : x)
    await updateWatchlist(active.id, { sections }); await load()
  }

  function useSection(sec){ onUseSymbols && onUseSymbols([...(sec.symbols||[])]) }

  return (
    <Card>
      <CardHeader className="py-2"><CardTitle className="text-base">Watchlists</CardTitle></CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <Input placeholder="New list name" value={newName} onChange={(e)=> setNewName(e.target.value)} />
          <Button size="sm" onClick={addList}>Add</Button>
        </div>
        <div className="flex gap-2 overflow-x-auto">
          {lists.map(l=> (
            <Button key={l.id} size="sm" variant={active?.id===l.id? 'default':'secondary'} onClick={()=> setActiveId(l.id)}>{l.name}</Button>
          ))}
        </div>
        {active && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Sections</div>
              <Button size="sm" variant="secondary" onClick={addSection}>+ Section</Button>
            </div>
            <div className="space-y-2">
              {(active.sections||[]).map(sec => (
                <div key={sec.id} className="border rounded p-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: sec.color||'#64748b' }} />
                      <div className="font-medium">{sec.name}</div>
                      <div className="text-xs text-muted-foreground">{(sec.symbols||[]).length} symbols</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Select value={sec.color||''} onValueChange={(v)=> setColor(sec.id, v)}>
                        <SelectTrigger className="w-24"><SelectValue placeholder="Color"/></SelectTrigger>
                        <SelectContent>
                          {COLORS.map(c=> <SelectItem key={c} value={c}><div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{background:c}}></span><span>{c}</span></div></SelectItem>)}
                        </SelectContent>
                      </Select>
                      <Button size="sm" variant="secondary" onClick={()=> useSection(sec)}>Use</Button>
                      <Button size="sm" onClick={()=> addSymbol(sec)}>+ Symbol</Button>
                    </div>
                  </div>
                  {(sec.symbols||[]).length>0 && (
                    <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                      {sec.symbols.map(s => (
                        <div key={s} className="flex items-center justify-between border rounded px-2 py-1">
                          <span>{s}</span>
                          <Select onValueChange={(to)=> moveSymbol(s, sec.id, to)}>
                            <SelectTrigger className="w-28"><SelectValue placeholder="Move"/></SelectTrigger>
                            <SelectContent>
                              {(active.sections||[]).filter(x=> x.id!==sec.id).map(x=> (
                                <SelectItem key={x.id} value={x.id}>→ {x.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {(active.sections||[]).length===0 && (
                <div className="text-xs text-muted-foreground">No sections yet. Click "+ Section" to add.</div>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}