import React, { useMemo } from "react"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"

const OPS = [">=","<=",">","<","between","in"]

function CondRow({ idx, fields, cond, onChange, onRemove }){
  const field = fields.find(f=> f.id===cond.field) || fields[0]
  const type = field?.type || 'number'
  return (
    <div className="grid grid-cols-12 gap-2 items-center">
      <div className="col-span-4">
        <Select value={cond.field} onValueChange={(v)=> onChange(idx, { ...cond, field: v })}>
          <SelectTrigger><SelectValue placeholder="Field" /></SelectTrigger>
          <SelectContent className="max-h-60">
            {fields.map(f=> <SelectItem key={f.id} value={f.id}>{f.label}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div className="col-span-2">
        <Select value={cond.op} onValueChange={(v)=> onChange(idx, { ...cond, op: v })}>
          <SelectTrigger><SelectValue placeholder="Op" /></SelectTrigger>
          <SelectContent>
            {OPS.map(o=> <SelectItem key={o} value={o}>{o}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>
      <div className="col-span-5">
        {cond.op === 'between' ? (
          <div className="flex gap-2">
            <Input placeholder="Min" value={cond.value?.[0] ?? ''} onChange={(e)=> onChange(idx, { ...cond, value: [e.target.value, cond.value?.[1] ?? ''] })} />
            <Input placeholder="Max" value={cond.value?.[1] ?? ''} onChange={(e)=> onChange(idx, { ...cond, value: [cond.value?.[0] ?? '', e.target.value] })} />
          </div>
        ) : (
          <Input placeholder="Value" value={cond.value ?? ''} onChange={(e)=> onChange(idx, { ...cond, value: e.target.value })} />
        )}
      </div>
      <div className="col-span-1">
        <Button size="sm" variant="destructive" onClick={()=> onRemove(idx)}>X</Button>
      </div>
    </div>
  )
}

export default function QueryBuilder({ registry, query, setQuery }){
  const fields = useMemo(()=> (registry?.categories||[]).flatMap(c=> c.fields||c.columns || []), [registry])
  const add = ()=> setQuery(prev => ({...prev, filters: [...(prev.filters||[]), { field: (fields[0]?.id||'last'), op: ">=", value: 5 }]}))
  const onChange = (i, c)=> setQuery(prev => ({...prev, filters: prev.filters.map((x, idx)=> idx===i? c : x)}))
  const onRemove = (i)=> setQuery(prev => ({...prev, filters: prev.filters.filter((_, idx)=> idx!==i)}))

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">Build conditions (AND). Use presets for complex queries.</div>
        <Button size="sm" onClick={add}>+ Condition</Button>
      </div>
      <div className="space-y-2">
        {(query.filters||[]).map((cond, i)=> (
          <CondRow key={i} idx={i} fields={fields} cond={cond} onChange={onChange} onRemove={onRemove} />
        ))}
        {(!query.filters || query.filters.length===0) && (
          <div className="text-xs text-muted-foreground">No conditions. Click "+ Condition" to add.</div>
        )}
      </div>
    </div>
  )
}