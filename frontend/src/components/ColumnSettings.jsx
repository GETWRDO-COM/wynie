import React, { useMemo, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Input } from "./ui/input"
import { Checkbox } from "./ui/checkbox"
import { Button } from "./ui/button"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion"
import { COLUMN_REGISTRY } from "./DataTable"

export default function ColumnSettings({ open, onOpenChange, visibleColumns, setVisibleColumns, presets, savePreset, loadPreset, resetRecommended }) {
  const [search, setSearch] = useState("")
  const grouped = useMemo(()=>{
    const groups = {}
    for (const c of COLUMN_REGISTRY) {
      if (search && !c.label.toLowerCase().includes(search.toLowerCase())) continue
      groups[c.category] ||= []
      groups[c.category].push(c)
    }
    return groups
  }, [search])

  const toggle = (id) => {
    setVisibleColumns(prev => prev.includes(id) ? prev.filter(x=> x!==id) : [...prev, id])
  }

  const move = (id, dir) => {
    setVisibleColumns(prev => {
      const i = prev.indexOf(id); if (i===-1) return prev
      const j = Math.max(0, Math.min(prev.length-1, i + dir))
      const arr = [...prev]; const [it] = arr.splice(i,1); arr.splice(j,0,it)
      return arr
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Column Settings</DialogTitle>
        </DialogHeader>
        <div className="flex gap-3 mb-3">
          <Input placeholder="Search columns" value={search} onChange={(e)=> setSearch(e.target.value)} />
          <Button variant="secondary" onClick={resetRecommended}>Reset</Button>
          <div className="ml-auto flex gap-2">
            <Input placeholder="Preset name" id="presetName" className="w-40" />
            <Button onClick={()=> savePreset(document.getElementById('presetName').value)}>Save Preset</Button>
            <select className="border rounded px-2" onChange={(e)=> loadPreset(e.target.value)}>
              <option value="">Load preset...</option>
              {Object.keys(presets||{}).map(k=> <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-h-[60vh] overflow-auto pr-2">
          <div>
            <h4 className="font-medium mb-2">Categories</h4>
            <Accordion type="multiple" defaultValue={["General","Price & Volume"]}>
              {Object.entries(grouped).map(([cat, cols])=> (
                <AccordionItem key={cat} value={cat}>
                  <AccordionTrigger>{cat}</AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2">
                      {cols.map(c=> (
                        <label key={c.id} className="flex items-center gap-2">
                          <Checkbox checked={visibleColumns.includes(c.id)} onCheckedChange={()=> toggle(c.id)} />
                          <span>{c.label}</span>
                        </label>
                      ))}
                    </div>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </div>
          <div>
            <h4 className="font-medium mb-2">Visible Order</h4>
            <div className="border rounded p-2 space-y-2 max-h-[50vh] overflow-auto">
              {visibleColumns.map(id=> {
                const c = COLUMN_REGISTRY.find(x=> x.id===id)
                if (!c) return null
                return (
                  <div key={id} className="flex items-center justify-between bg-muted/50 px-2 py-1 rounded">
                    <span>{c.label}</span>
                    <div className="space-x-1">
                      <Button size="sm" variant="secondary" onClick={()=> move(id, -1)}>Up</Button>
                      <Button size="sm" variant="secondary" onClick={()=> move(id, +1)}>Down</Button>
                      <Button size="sm" variant="destructive" onClick={()=> toggle(id)}>Hide</Button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}