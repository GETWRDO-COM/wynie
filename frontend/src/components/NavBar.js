import React, { useState } from 'react';
import { FaCog, FaSignOutAlt, FaBars } from 'react-icons/fa';

// Icon-only mapping so we can render small icons next to labels if desired
const TABS = [
  { id: 'dashboard', label: 'Dashboard', emoji: '🏠' },
  { id: 'swing-grid', label: 'Analysis Grid', emoji: '📊' },
  { id: 'ai-analysis', label: 'AI Assistant', emoji: '🧠' },
  { id: 'spreadsheet', label: 'Spreadsheet', emoji: '📋' },
  { id: 'ai-chat', label: 'AI Chat', emoji: '💬' },
];

const NavBar = ({ activeTab, setActiveTab, user, onSettings, onLogout }) => {
  const [open, setOpen] = useState(false);

  return (
    <header className="nav-shell px-4 sm:px-6">
      <div className="max-w-7xl mx-auto">
        <div className="h-16 flex items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <img src="/assets/theme/logo.svg" alt="logo" className="w-7 h-7" />
            <div className="hidden sm:block">
              <div className="text-[15px] leading-none text-gray-300">HUNT BY WRDO</div>
              <div className="text-xs text-gray-500">Premium Trading Workspace</div>
            </div>
          </div>

          {/* Desktop nav */}
          <nav className="hidden md:block">
            <div className="nav-tabs flex items-center gap-1">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={`nav-tab ${activeTab === t.id ? 'active' : 'inactive'}`}
                >
                  <span className="mr-1">{t.emoji}</span>
                  {t.label}
                </button>
              ))}
            </div>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-2">
            <button
              onClick={onSettings}
              className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5"
              title="Settings"
            >
              <FaCog className="text-lg" />
            </button>
            <button
              onClick={onLogout}
              className="text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5"
              title="Logout"
            >
              <FaSignOutAlt className="text-lg" />
            </button>
            <button
              onClick={() => setOpen(!open)}
              className="md:hidden text-gray-300 hover:text-white p-2 rounded-lg hover:bg-white/5"
              aria-label="Toggle menu"
            >
              <FaBars />
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        {open && (
          <div className="md:hidden pb-3">
            <div className="nav-tabs flex flex-wrap items-center gap-1">
              {TABS.map((t) => (
                <button
                  key={t.id}
                  onClick={() => { setActiveTab(t.id); setOpen(false); }}
                  className={`nav-tab ${activeTab === t.id ? 'active' : 'inactive'} w-[calc(50%-4px)]`}
                >
                  <span className="mr-1">{t.emoji}</span>
                  {t.label}
                </button>
              ))}
            </div>
            <div className="mt-3 text-xs text-gray-400">Signed in as {user?.email}</div>
          </div>
        )}
      </div>
    </header>
  );
};

export default NavBar;