import React from "react"
import { Button } from "./ui/button"

export default function PresetsBar({ onApply }){
  return (
    <div className="flex flex-wrap gap-2">
      <Button size="sm" variant="secondary" onClick={()=> onApply('newHighs')}>New Highs</Button>
      <Button size="sm" variant="secondary" onClick={()=> onApply('redList')}>Red List</Button>
      <Button size="sm" variant="secondary" onClick={()=> onApply('leaders')}>Leaders</Button>
      <Button size="sm" variant="secondary" onClick={()=> onApply('vcp')}>VCP</Button>
      <Button size="sm" variant="secondary" onClick={()=> onApply('breakouts')}>Breakouts</Button>
      <Button size="sm" variant="secondary" onClick={()=> onApply('pullbacks')}>Pullbacks</Button>
      <Button size="sm" variant="secondary" onClick={()=> onApply('earnings')}>Earnings</Button>
    </div>
  )
}