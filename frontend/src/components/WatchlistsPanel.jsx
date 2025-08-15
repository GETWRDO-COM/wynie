import React, { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { listWatchlists, createWatchlist, updateWatchlist, deleteWatchlist } from "../services/api"
import { LS } from "../mock/mock"
import { GripVertical, X } from "lucide-react"

const COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#22c55e","#f97316"]

function rid(){ return (globalThis.crypto?.randomUUID?.() || `id_${Date.now()}_${Math.random().toString(36).slice(2)}`) }

export default function WatchlistsPanel({ onUseSymbols }){
  const [lists, setLists] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [newName, setNewName] = useState("")
  const [template, setTemplate] = useState("multi") // 'core' | 'multi'

  // DnD state
  const [dragData, setDragData] = useState(null) // {sym, fromId, fromIndex}

  // Combo builder state
  const [selectedSecs, setSelectedSecs] = useState(()=> LS.get('combo_selectedSecs', []))
  const [comboName, setComboName] = useState("")
  const [savedCombos, setSavedCombos] = useState(()=> LS.get('combos', {})) // { name: [secKey,...] }

  const active = useMemo(()=> lists.find(l=> l.id===activeId) || lists[0], [lists, activeId])

  const allSections = useMemo(()=> {
    const arr = []
    for (const l of lists){
      for (const s of (l.sections||[])){
        arr.push({ key: `${l.id}:${s.id}`, listId: l.id, listName: l.name, id: s.id, name: s.name, color: s.color, symbols: s.symbols||[] })
      }
    }
    return arr
  }, [lists])

  async function load(){ try { const r = await listWatchlists(); setLists(r||[]) } catch {} }
  useEffect(()=>{ load() }, [])

  async function addList(){
    const name = newName.trim() || "My List"
    let sections
    if (template === 'multi') {
      sections = [
        { id: rid(), name: "Core", color: "#3b82f6", symbols: ["AAPL","MSFT","NVDA"] },
        { id: rid(), name: "Momentum", color: "#10b981", symbols: ["TSLA","AMD","META"] },
        { id: rid(), name: "Earnings", color: "#f59e0b", symbols: ["AMZN","GOOGL","NFLX"] },
      ]
    } else {
      sections = [{ id: rid(), name: "Core", color: "#3b82f6", symbols: ["AAPL","MSFT","NVDA"] }]
    }
    try {
      const r = await createWatchlist(name, [], sections)
      setNewName("")
      await load()
      setActiveId(r.id)
    } catch {}
  }

  async function addSection(){
    if (!active) return
    const name = prompt("Section name?") || "Section"
    const color = COLORS[Math.floor(Math.random()*COLORS.length)]
    const sections = [...(active.sections||[]), { id: rid(), name, color, symbols: [] }]
    await updateWatchlist(active.id, { sections }); await load()
  }

  async function addSymbol(sec){
    const val = prompt("Add symbol (e.g., TSLA)")
    if (!val) return
    const s = val.toUpperCase().trim()
    const sections = (active.sections||[]).map(x=> x.id===sec.id ? ({...x, symbols: [...(x.symbols||[]), s]}) : x)
    await updateWatchlist(active.id, { sections }); await load()
  }

  async function moveSymbol(sym, fromId, toId, toIndex=null){
    const sections = (active.sections||[]).map(x=> ({...x, symbols: [...(x.symbols||[])]}))
    const from = sections.find(x=> x.id===fromId)
    const to = sections.find(x=> x.id===toId)
    if (!to) return
    // remove from source
    if (from){
      const idx = from.symbols.indexOf(sym)
      if (idx >= 0) from.symbols.splice(idx, 1)
    }
    // insert into target at index or end
    if (toIndex==null || toIndex<0 || toIndex>to.symbols.length) to.symbols.push(sym)
    else to.symbols.splice(toIndex, 0, sym)
    await updateWatchlist(active.id, { sections }); await load()
  }

  async function removeSymbol(sym, secId){
    if (!active) return
    // optimistic remove without blocking confirm for automation reliability
    const sections = (active.sections||[]).map(x=> x.id===secId ? ({...x, symbols: (x.symbols||[]).filter(z=> z!==sym)}) : x)
    // optimistic local update for instant feedback
    setLists(prev => prev.map(l => l.id===active.id ? ({...l, sections}) : l))
    try { await updateWatchlist(active.id, { sections }) } catch {}
    await load()
  }

  async function setColor(secId, color){
    const sections = (active.sections||[]).map(x=> x.id===secId? ({...x, color}) : x)
    await updateWatchlist(active.id, { sections }); await load()
  }

  function useSection(sec){ onUseSymbols && onUseSymbols([...(sec.symbols||[])]) }

  function onDragStartSym(e, sym, secId, index){
    setDragData({ sym, fromId: secId, fromIndex: index })
    e.dataTransfer.effectAllowed = 'move'
  }
  function onDragOverSymbol(e){ e.preventDefault(); e.dataTransfer.dropEffect = 'move' }
  function onDropIntoSection(e, toSecId, toIndex=null){
    e.preventDefault()
    if (!dragData) return
    moveSymbol(dragData.sym, dragData.fromId, toSecId, toIndex)
    setDragData(null)
  }

  // Combo builder helpers
  function toggleSec(key){
    setSelectedSecs(prev => {
      const set = new Set(prev)
      if (set.has(key)) set.delete(key); else set.add(key)
      const arr = Array.from(set)
      LS.set('combo_selectedSecs', arr)
      return arr
    })
  }
  function useCombo(){
    const chosen = allSections.filter(s=> selectedSecs.includes(`${s.listId}:${s.id}`))
    const merged = []
    for (const s of chosen){ for (const sym of (s.symbols||[])) if (!merged.includes(sym)) merged.push(sym) }
    onUseSymbols && onUseSymbols(merged)
  }
  function saveCombo(){
    const name = comboName.trim() || `Combo ${Object.keys(savedCombos).length+1}`
    const next = { ...savedCombos, [name]: [...selectedSecs] }
    setSavedCombos(next); LS.set('combos', next); setComboName("")
  }
  function loadCombo(name){ const secs = savedCombos[name] || []; setSelectedSecs(secs); LS.set('combo_selectedSecs', secs) }
  function deleteCombo(name){ const next = { ...savedCombos }; delete next[name]; setSavedCombos(next); LS.set('combos', next) }

  return (
    <Card>
      <CardHeader className="py-2"><CardTitle className="text-base">Watchlists</CardTitle></CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <Input placeholder="New list name" value={newName} onChange={(e)=> setNewName(e.target.value)} />
          <Select value={template} onValueChange={setTemplate}>
            <SelectTrigger className="w-44"><SelectValue placeholder="Start with"/></SelectTrigger>
            <SelectContent>
              <SelectItem value="core">Core only</SelectItem>
              <SelectItem value="multi">Core + Momentum + Earnings</SelectItem>
            </SelectContent>
          </Select>
          <Button size="sm" onClick={addList}>Add</Button>
        </div>

        <div className="flex gap-2 overflow-x-auto">
          {lists.map(l=> (
            <Button key={l.id} size="sm" variant={active?.id===l.id? 'default':'secondary'} onClick={()=> setActiveId(l.id)}>{l.name}</Button>
          ))}
        </div>

        {active && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">Sections</div>
              <Button size="sm" variant="secondary" onClick={addSection}>+ Section</Button>
            </div>
            <div className="space-y-2">
              {(active.sections||[]).map(sec => (
                <div key={sec.id} className="border rounded p-2" onDragOver={onDragOverSymbol} onDrop={(e)=> onDropIntoSection(e, sec.id, null)}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ background: sec.color||'#64748b' }} />
                      <div className="font-medium">{sec.name}</div>
                      <div className="text-xs text-muted-foreground">{(sec.symbols||[]).length} symbols</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Select value={sec.color||''} onValueChange={(v)=> setColor(sec.id, v)}>
                        <SelectTrigger className="w-28"><SelectValue placeholder="Color"/></SelectTrigger>
                        <SelectContent>
                          {COLORS.map(c=> <SelectItem key={c} value={c}><div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full" style={{background:c}}></span><span>{c}</span></div></SelectItem>)}
                        </SelectContent>
                      </Select>
                      <input type="color" value={sec.color||'#64748b'} onChange={(e)=> setColor(sec.id, e.target.value)} title="Custom color" className="w-8 h-8 p-0 border rounded" />
                      <Button size="sm" variant="secondary" onClick={()=> useSection(sec)}>Use</Button>
                      <Button size="sm" onClick={()=> addSymbol(sec)}>+ Symbol</Button>
                    </div>
                  </div>
                  {(sec.symbols||[]).length>0 && (
                    <div className="mt-2 grid grid-cols-3 gap-2 text-xs">
                      {sec.symbols.map((s, idx) => (
                        <div key={s+idx} className="flex items-center justify-between border rounded px-2 py-1"
                             draggable
                             onDragStart={(e)=> { onDragStartSym(e, s, sec.id, idx); try { const el = e.currentTarget.cloneNode(true); el.style.position='absolute'; el.style.left='-9999px'; document.body.appendChild(el); e.dataTransfer.setDragImage(el, 10, 10); setTimeout(()=> document.body.removeChild(el), 0) } catch {} }}
                             onDragOver={onDragOverSymbol}
                             onDrop={(e)=> onDropIntoSection(e, sec.id, idx)}>
                          <span className="flex items-center gap-1">
                            <GripVertical className="w-3 h-3 text-muted-foreground" />
                            {s}
                          </span>
                          <div className="flex items-center gap-2">
                            <Select onValueChange={(to)=> moveSymbol(s, sec.id, to)}>
                              <SelectTrigger className="w-32"><SelectValue placeholder="Move"/></SelectTrigger>
                              <SelectContent>
                                {(active.sections||[]).filter(x=> x.id!==sec.id).map(x=> (
                                  <SelectItem key={x.id} value={x.id}>→ {x.name}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600" title="Remove" onClick={()=> removeSymbol(s, sec.id)}>
                              <X className="w-4 h-4" />
                            </Button>
                          </div>
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

        {/* Combo Builder */}
        <div className="border rounded p-2">
          <div className="flex items-center justify-between mb-2">
            <div className="font-medium text-sm">Combo Builder</div>
            <div className="flex items-center gap-2">
              <Input placeholder="Combo name" value={comboName} onChange={(e)=> setComboName(e.target.value)} className="h-8" />
              <Button size="sm" variant="secondary" onClick={saveCombo}>Save</Button>
              <Select onValueChange={(name)=> name && loadCombo(name)}>
                <SelectTrigger className="w-40"><SelectValue placeholder="Load combo"/></SelectTrigger>
                <SelectContent>
                  {Object.keys(savedCombos).length===0 && <div className="px-2 py-1 text-xs text-muted-foreground">No saved combos</div>}
                  {Object.keys(savedCombos).map(n=> (
                    <SelectItem key={n} value={n}>{n}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {Object.keys(savedCombos).length>0 && (
                <Select onValueChange={(name)=> name && deleteCombo(name)}>
                  <SelectTrigger className="w-28"><SelectValue placeholder="Delete"/></SelectTrigger>
                  <SelectContent>
                    {Object.keys(savedCombos).map(n=> (
                      <SelectItem key={n} value={n}>{n}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
              <Button size="sm" onClick={useCombo}>Use Combo</Button>
            </div>
          </div>
          <div className="max-h-40 overflow-auto grid grid-cols-1 gap-1 text-xs">
            {allSections.map(sec => {
              const key = `${sec.listId}:${sec.id}`
              const checked = selectedSecs.includes(key)
              return (
                <label key={key} className="flex items-center gap-2">
                  <input type="checkbox" checked={checked} onChange={()=> toggleSec(key)} />
                  <span className="inline-flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{background: sec.color||'#64748b'}}></span>
                    <span className="font-medium">{sec.name}</span>
                    <span className="text-muted-foreground">({sec.listName})</span>
                    <span className="text-muted-foreground">• {sec.symbols.length} symbols</span>
                  </span>
                </label>
              )
            })}
            {allSections.length===0 && <div className="text-muted-foreground">No sections available</div>}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}