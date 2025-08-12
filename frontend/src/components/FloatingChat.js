import React, { useState } from 'react';
import { FaComments } from 'react-icons/fa';
import AIChat from './AIChat';

const FloatingChat = ({ api, user }) => {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open && (
        <div className="fixed bottom-20 right-4 z-[70] w-[380px] max-w-[90vw]">
          <div className="glass-panel p-3">
            <div className="flex items-center justify-between mb-2">
              <div className="text-white/90 font-semibold">AI Assistant</div>
              <button onClick={() => setOpen(false)} className="text-gray-300 hover:text-white text-sm">Close</button>
            </div>
            <div className="h-[420px] overflow-hidden rounded-xl bg-black/30 border border-white/10">
              <AIChat api={api} user={user} />
            </div>
          </div>
        </div>
      )}
      <button onClick={() => setOpen(!open)} className="fixed bottom-6 right-6 z-[70] w-12 h-12 rounded-full flex items-center justify-center btn-primary shadow-lg">
        <FaComments />
      </button>
    </>
  );
};

export default FloatingChat;