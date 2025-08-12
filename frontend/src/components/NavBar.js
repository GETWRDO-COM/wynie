import React, { useEffect, useState } from 'react';
import { FaCog, FaSignOutAlt, FaBars } from 'react-icons/fa';

const TABS = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'swing-grid', label: 'Analysis' },
  { id: 'ai-analysis', label: 'AI' },
  { id: 'spreadsheet', label: 'Spreadsheets' },
];

const NavBar = ({ activeTab, setActiveTab, user, onSettings, onLogout }) => {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 4);
    onScroll();
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header className="sticky top-0 z-[2000]">
      <div className={`${scrolled ? 'bg-[#070a11]/98 shadow-lg border-b border-white/10' : 'bg-[#070a11]/90'} transition-colors`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 relative">
          <div className="h-14 flex items-center justify-between gap-4">
            <div className="text-white font-semibold tracking-wide">HUNT by WRDO</div>
            <nav className="hidden md:block relative">
              <div className="flex items-center gap-2">
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    onClick={() => { setActiveTab(t.id); }}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${activeTab === t.id ? 'text-white bg-white/10 border border-white/10' : 'text-gray-300 hover:text-white hover:bg-white/5'}`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </nav>
            <div className="flex items-center gap-2">
              <button onClick={onSettings} className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" title="Settings"><FaCog className="text-[15px]" /></button>
              <button onClick={onLogout} className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" title="Logout"><FaSignOutAlt className="text-[15px]" /></button>
              <button onClick={() => setOpen(!open)} className="md:hidden text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5" aria-label="Toggle menu"><FaBars /></button>
            </div>
          </div>
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