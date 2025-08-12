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
        <div className="fixed z-[10050] w-[420px] max-w-[92vw]" style={{ right: 16 - pos.x, bottom: 140 - pos.y }} onMouseMove={onMouseMove} onMouseUp={onMouseUp}>
          <div className="glass-panel p-3">
            <div className="flex items-center justify-between mb-2 cursor-move select-none" onMouseDown={onMouseDown}>
              <div className="text-white/90 font-semibold">WRDO</div>
              <div className="flex items-center gap-2">
                <button onClick={() => setOpen(false)} className="text-gray-300 hover:text-white text-xs px-2 py-1 rounded bg-white/5 border border-white/10">Minimize</button>
                <button onClick={() => setOpen(false)} className="text-gray-300 hover:text-white text-sm">Close</button>
              </div>
            </div>
            <div className="h-[520px] rounded-xl bg-black/30 border border-white/10 overflow-hidden">
              <AIChat api={api} user={user} />
            </div>
          </div>
        </div>
      )}
      <button title="WRDO (Ctrl+K)" onClick={() => setOpen(!open)} className="fixed bottom-28 right-6 z-[10050] w-14 h-14 rounded-full flex items-center justify-center btn-primary shadow-xl animate-pulse">
        <FaComments />
      </button>
    </>
  );
};

export default FloatingChat;