import React, { useEffect, useState } from 'react';

const PolygonKeySettings = () => {
  const [value, setValue] = useState('');
  const [configured, setConfigured] = useState(false);
  const [saving, setSaving] = useState(false);
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';

  const load = async () => {
    try {
      const resp = await fetch(`${BACKEND_URL}/api/integrations/polygon/status`, { headers: { Authorization: `Bearer ${localStorage.getItem('authToken') || ''}` } });
      const js = await resp.json();
      setConfigured(!!js.configured);
    } catch {}
  };

  const save = async () => {
    if (!value) return;
    setSaving(true);
    try {
      await fetch(`${BACKEND_URL}/api/integrations/polygon/key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('authToken') || ''}` },
        body: JSON.stringify({ api_key: value })
      });
      setValue('');
      await load();
      alert('Polygon key saved');
    } catch (e) {
      alert('Failed to save key');
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="glass-panel p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-white/90 font-semibold">Polygon.io Integration</div>
        <div className={`text-xs ${configured ? 'text-green-400' : 'text-red-300'}`}>{configured ? 'Configured' : 'Not configured'}</div>
      </div>
      <div className="flex gap-2">
        <input type="password" placeholder="Paste Polygon API Key" value={value} onChange={(e) => setValue(e.target.value)} className="form-input flex-1" />
        <button disabled={!value || saving} onClick={save} className="btn btn-primary">Save</button>
      </div>
      <div className="text-xs text-gray-400 mt-2">Stored securely on backend. Env variable POLYGON_API_KEY is used as fallback.</div>
    </div>
  );
};

export default PolygonKeySettings;
