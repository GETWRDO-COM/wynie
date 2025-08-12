import React from 'react';

// Simplified, premium background wrapper (cleaner, less noise)
const ThemeWrapper = ({ children }) => {
  return (
    <div className="relative min-h-screen bg-[#0b0f14] text-white overflow-x-hidden">
      {/* Subtle radial glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background: 'radial-gradient(900px 600px at 30% 10%, rgba(59,130,246,0.18) 0%, rgba(139,92,246,0.12) 30%, rgba(0,0,0,0) 60%)',
          filter: 'blur(2px)'
        }}
      />

      {/* Soft edge vignette */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(1200px_800px_at_50%_0%,rgba(0,0,0,0)_0%,rgba(0,0,0,0.6)_100%)]" />

      {/* Minimal accent gradients (very low opacity) */}
      <img src="/assets/theme/gradient-1.png" alt="" aria-hidden className="hidden md:block absolute -top-24 -left-24 w-[800px] opacity-[0.12]" />
      <img src="/assets/theme/gradient-2.png" alt="" aria-hidden className="absolute bottom-[-160px] -right-24 w-[1000px] opacity-[0.1]" />

      <div className="relative z-10">{children}</div>
    </div>
  );
};

export default ThemeWrapper;