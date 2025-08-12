import React, { useEffect } from "react"
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom"
import Dashboard from "./pages/Dashboard"
import Settings from "./pages/Settings"
import "./index.css"

function Shell({children}){
  return (
    <div className="h-screen flex flex-col">
      <nav className="h-12 border-b flex items-center justify-between px-4 bg-card">
        <div className="font-semibold">Market Workstation</div>
        <div className="flex gap-4 text-sm">
          <Link to="/">Dashboard</Link>
          <Link to="/settings">Settings</Link>
        </div>
      </nav>
      <div className="flex-1 overflow-hidden">{children}</div>
    </div>
  )
}

function App() {
  useEffect(()=>{
    // Force dark theme to match Deepvue screenshots
    try { document.documentElement.classList.add('dark') } catch {}
  },[])
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Shell><Dashboard /></Shell>} />
        <Route path="/settings" element={<Shell><Settings /></Shell>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App