import React, { useState } from 'react';
import { FaComments } from 'react-icons/fa';
import AIChat from './AIChat';

import useHotkeys from '../hooks/useHotkeys';

const FloatingChat = ({ api, user }) => {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [drag, setDrag] = useState(null);

  useHotkeys([
    { combo: 'ctrl+k', handler: () => setOpen((v) => !v) },
    { combo: 'ctrl+/', handler: () => setOpen(true) },
  ]);

  const onMouseDown = (e) => { setDrag({ startX: e.clientX, startY: e.clientY, baseX: pos.x, baseY: pos.y }); };
  const onMouseMove = (e) => { if (!drag) return; const dx = e.clientX - drag.startX; const dy = e.clientY - drag.startY; setPos({ x: drag.baseX + dx, y: drag.baseY + dy }); };
  const onMouseUp = () => setDrag(null);

  return (
    <>
      {open && (
        <div className="fixed z-[10050] w-[380px] max-w-[90vw]" style={{ right: 16 - pos.x, bottom: 120 - pos.y }} onMouseMove={onMouseMove} onMouseUp={onMouseUp}>
          <div className="glass-panel p-3">
            <div className="flex items-center justify-between mb-2 cursor-move select-none" onMouseDown={onMouseDown}>
              <div className="text-white/90 font-semibold">AI Assistant</div>
              <button onClick={() => setOpen(false)} className="text-gray-300 hover:text-white text-sm">Close</button>
            </div>
            <div className="h-[420px] overflow-hidden rounded-xl bg-black/30 border border-white/10">
              <AIChat api={api} user={user} />
            </div>
          </div>
        </div>
      )}
      <button title="AI (Ctrl+K)" onClick={() => setOpen(!open)} className="fixed bottom-24 right-6 z-[10050] w-12 h-12 rounded-full flex items-center justify-center btn-primary shadow-lg">
        <FaComments />
      </button>
    </>
  );
};

export default FloatingChat;