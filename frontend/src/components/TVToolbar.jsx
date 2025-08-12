import React from "react"
import { MousePointer2, Pencil, Ruler, Brush, Text, Eraser, Settings, LineChart, Move3D, Crosshair } from "lucide-react"

const ToolBtn = ({ icon: Icon, active, onClick, title }) => (
  <button
    title={title}
    onClick={onClick}
    className={`w-8 h-8 mb-2 flex items-center justify-center rounded ${active? 'bg-secondary text-secondary-foreground':'hover:bg-muted/60'} transition-colors`}
  >
    <Icon className="w-4 h-4" />
  </button>
)

export default function TVToolbar({ tool, setTool }){
  return (
    <div className="flex flex-col items-center p-2 border-r bg-card/60">
      <ToolBtn icon={MousePointer2} title="Select" active={tool==='select'} onClick={()=> setTool('select')} />
      <ToolBtn icon={Crosshair} title="Crosshair" active={tool==='cross'} onClick={()=> setTool('cross')} />
      <ToolBtn icon={Pencil} title="Trend Line" active={tool==='line'} onClick={()=> setTool('line')} />
      <ToolBtn icon={Ruler} title="Ray" active={tool==='ray'} onClick={()=> setTool('ray')} />
      <ToolBtn icon={Brush} title="Brush" active={tool==='brush'} onClick={()=> setTool('brush')} />
      <ToolBtn icon={Text} title="Text" active={tool==='text'} onClick={()=> setTool('text')} />
      <div className="h-2" />
      <ToolBtn icon={Eraser} title="Clear" active={false} onClick={()=> setTool('clear')} />
      <div className="h-2" />
      <ToolBtn icon={Settings} title="Chart Settings" active={false} onClick={()=> {}} />
    </div>
  )
}