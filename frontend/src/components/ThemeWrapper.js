import React from 'react';

// Global theme wrapper that renders epic background layers and provides a glassy container style
// Uses public assets copied from the UI kit (see /public/assets/theme)
const ThemeWrapper = ({ children }) => {
  return (
    <div className="relative min-h-screen bg-[#0a0c12] text-white overflow-x-hidden">
      {/* Background gradients */}
      <img
        src="/assets/theme/gradient-1.png"
        alt="bg-1"
        aria-hidden
        className="pointer-events-none select-none hidden md:block absolute -top-16 -left-24 w-[900px] opacity-30 blur-[2px]"
      />
      <img
        src="/assets/theme/gradient-2.png"
        alt="bg-2"
        aria-hidden
        className="pointer-events-none select-none absolute bottom-[-120px] -right-24 w-[1100px] opacity-25 blur-[1px]"
      />
      <img
        src="/assets/theme/gradient-3.png"
        alt="bg-3"
        aria-hidden
        className="pointer-events-none select-none hidden lg:block absolute top-1/3 -right-32 w-[800px] opacity-20"
      />

      {/* Star overlay */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.12]"
        style={{
          backgroundImage: "url('/assets/theme/star.svg')",
          backgroundRepeat: 'repeat',
          backgroundSize: '180px 180px',
          mixBlendMode: 'screen',
        }}
      />

      {/* Subtle vignette */}
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(1200px_800px_at_50%_0%,rgba(0,0,0,0)_0%,rgba(0,0,0,0.65)_100%)]" />

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
};

export default ThemeWrapper;