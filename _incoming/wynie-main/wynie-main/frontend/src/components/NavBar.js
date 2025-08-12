import React, { useState } from 'react';
import { FaCog, FaSignOutAlt, FaBars } from 'react-icons/fa';

const TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'swing-grid', label: 'Analysis Grid', mega: true },
  { id: 'ai-analysis', label: 'AI Assistant', mega: true },
  { id: 'spreadsheet', label: 'Spreadsheet' },
  { id: 'ai-chat', label: 'AI Chat' },
];

const MegaMenu = ({ open, kind }) => {
  if (!open) return null;
  const groups = kind === 'swing-grid' ? [
    { title: 'Scanners', items: ['Top Movers', 'Breakouts', 'High RS'] },
    { title: 'Filters', items: ['Low ATR', 'RWB Pattern', 'Bullish 20SMA'] },
    { title: 'Leaders', items: ['1D Winners', '1W Momentum', '1M Strength'] },
  ] : [
    { title: 'Chat', items: ['New Session', 'Latest Model', 'Saved Sessions'] },
    { title: 'Playbooks', items: ['Mean Reversion', 'Breakout', 'Swing'] },
    { title: 'Actions', items: ['Backtest', 'Simulate', 'Explain Strategy'] },
  ];
  return (
    <div className="absolute left-1/2 -translate-x-1/2 mt-3 w-[760px] rounded-2xl border border-white/10 bg-[#0b0f14]/95 backdrop-blur-xl shadow-2xl p-6 z-50">
      <div className="grid grid-cols-3 gap-6">
        {groups.map((g) => (
          <div key={g.title}>
            <div className="text-white/90 font-semibold mb-2">{g.title}</div>
            <ul className="space-y-1 text-sm">
              {g.items.map((it) => (
                <li key={it} className="text-gray-300 hover:text-white cursor-pointer">{it}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

const NavBar = ({ activeTab, setActiveTab, user, onSettings, onLogout }) => {
  const [open, setOpen] = useState(false);
  const [mega, setMega] = useState(null);

  return (
    <header className="sticky top-0 z-50">
      <div className="bg-[#070a11]/98">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 relative">
          <div className="h-14 flex items-center justify-between gap-4">
            {/* Brand only */}
            <div className="text-white font-semibold tracking-wide">HUNT by WRDO</div>

            {/* Desktop nav - transparent (no frosted behind) */}
            <nav className="hidden md:block relative">
              <div className="flex items-center gap-2">
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    onMouseEnter={() => setMega(t.mega ? t.id : null)}
                    onMouseLeave={() => setMega(null)}
                    onClick={() => { setMega(null); setActiveTab(t.id); }}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${activeTab === t.id ? 'text-white bg-white/10 border border-white/10' : 'text-gray-300 hover:text-white hover:bg-white/5'}`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
              <MegaMenu open={!!mega} kind={mega} />
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <button onClick={onSettings} className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" title="Settings"><FaCog className="text-[15px]" /></button>
              <button onClick={onLogout} className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" title="Logout"><FaSignOutAlt className="text-[15px]" /></button>
              <button onClick={() => setOpen(!open)} className="md:hidden text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" aria-label="Toggle menu"><FaBars /></button>
            </div>
          </div>
          {/* Fine line under categories */}
          <div className="h-px bg-gradient-to-r from-white/5 via-white/15 to-white/5" />

          {/* Mobile nav */}
          {open && (
            <div className="md:hidden pb-3">
              <div className="flex flex-wrap items-center gap-1">
                {TABS.map((t) => (
                  <button key={t.id} onClick={() => { setActiveTab(t.id); setOpen(false); }} className={`px-3 py-1.5 rounded-lg text-sm ${activeTab === t.id ? 'text-white bg-white/10 border border-white/10' : 'text-gray-300 hover:text-white hover:bg-white/5'}`}>{t.label}</button>
                ))}
              </div>
              <div className="mt-3 text-xs text-gray-400">Signed in as {user?.email}</div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default NavBar;