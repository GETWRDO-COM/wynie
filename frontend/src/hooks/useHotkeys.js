import { useEffect } from 'react';

export default function useHotkeys(bindings = []) {
  useEffect(() => {
    const onKey = (e) => {
      const key = [];
      if (e.ctrlKey || e.metaKey) key.push('ctrl');
      if (e.shiftKey) key.push('shift');
      if (e.altKey) key.push('alt');
      key.push(e.key.toLowerCase());
      const combo = key.join('+');
      const found = bindings.find(b => b.combo === combo);
      if (found) {
        e.preventDefault();
        try { found.handler(); } catch {}
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [bindings]);
}
