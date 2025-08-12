import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const useAccounts = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API}/admin/accounts`);
        setAccounts(res.data || []);
      } catch (e) {
        console.error("Failed to load accounts", e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);
  return { accounts, loading };
};

const TopBar = () => (
  <div className="topbar">
    <div className="brand">
      <img src="https://avatars.githubusercontent.com/in/1201222?s=48" alt="logo" />
      <div>HUNT Trade Journal</div>
    </div>
    <nav className="nav">
      {[
        ["/", "Dashboard"],
        ["/trades", "Trade Log"],
        ["/calendar", "Calendar"],
        ["/risk", "Risk"],
        ["/journal", "Journal"],
        ["/admin", "Admin"],
      ].map(([to, label]) => (
        <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "active" : "")}>{label}</NavLink>
      ))}
    </nav>
  </div>
);

const AccountSelector = ({ accounts, value, onChange }) => (
  <select className="select" value={value} onChange={(e) => onChange(e.target.value)}>
    {accounts.map((a) => (
      <option key={a.id} value={a.id}>{a.name} ({a.external_account_id})</option>
    ))}
  </select>
);

const Dashboard = () => {
  const { accounts, loading } = useAccounts();
  const [accountId, setAccountId] = useState("");
  const [daily, setDaily] = useState(null);

  useEffect(() => {
    if (!loading && accounts.length && !accountId) setAccountId(accounts[0].id);
  }, [loading, accounts, accountId]);

  useEffect(() => {
    const loadDaily = async () => {
      if (!accountId) return;
      try {
        const res = await axios.get(`${API}/journal/daily`, { params: { accountId } });
        setDaily(res.data);
      } catch (e) {
        console.error("failed to fetch daily", e);
      }
    };
    loadDaily();
  }, [accountId]);

  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 16 }}>
        {loading ? (
          <div>Loading accounts…</div>
        ) : (
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <div style={{ fontSize: 18, fontWeight: 600 }}>Account</div>
            <AccountSelector accounts={accounts} value={accountId} onChange={setAccountId} />
          </div>
        )}
      </div>
      <div className="kpis">
        {[
          { label: "Net P&L", value: daily?.summary?.total_pnl ?? 0 },
          { label: "R", value: daily?.summary?.avg_r ?? 0 },
          { label: "Win-rate", value: (daily?.summary?.win_rate ?? 0) * 100 },
          { label: "Expectancy", value: daily?.summary?.expectancy ?? 0 },
          { label: "Max DD", value: 0 },
        ].map((k) => (
          <div key={k.label} className="kpi">
            <div className="label">{k.label}</div>
            <div className="value">{Number(k.value).toFixed(2)}</div>
          </div>
        ))}
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>What changed today?</div>
        <div style={{ color: "#9ca3af" }}>New positions, closed trades, dividends will appear here after EOD ingest.</div>
      </div>
    </div>
  );
};

const Trades = () => {
  const { accounts, loading } = useAccounts();
  const [accountId, setAccountId] = useState("");
  const [rows, setRows] = useState([]);
  useEffect(() => {
    if (!loading && accounts.length && !accountId) setAccountId(accounts[0].id);
  }, [loading, accounts, accountId]);
  useEffect(() => {
    const load = async () => {
      if (!accountId) return;
      const res = await axios.get(`${API}/journal/trades`, { params: { accountId } });
      setRows(res.data.items || []);
    };
    load();
  }, [accountId]);
  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 12 }}>
        <AccountSelector accounts={accounts} value={accountId} onChange={setAccountId} />
      </div>
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', gap: 8, fontWeight: 700, marginBottom: 8 }}>
          <div>Symbol</div><div>R</div><div>Net P&amp;L</div><div>Fees</div><div>Entered</div>
        </div>
        {rows.map(r => (
          <div key={r.id} style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', gap: 8, padding: '8px 0', borderTop: '1px solid #1f2937' }}>
            <div>{r.symbol}</div>
            <div>{Number(r.r_multiple).toFixed(2)}</div>
            <div>{Number(r.net_pnl).toFixed(2)}</div>
            <div>{Number(r.fees_total).toFixed(2)}</div>
            <div>{r.entered_at ? new Date(r.entered_at).toLocaleString() : '-'}</div>
          </div>
        ))}
        {rows.length === 0 && <div style={{ color: '#9ca3af' }}>No trades yet. Ingest EOD to see trades.</div>}
      </div>
    </div>
  );
};

const Calendar = () => {
  const { accounts, loading } = useAccounts();
  const [accountId, setAccountId] = useState("");
  const month = useMemo(() => new Date().toISOString().slice(0,7), []);
  const [points, setPoints] = useState([]);
  useEffect(() => { if (!loading && accounts.length && !accountId) setAccountId(accounts[0].id); }, [loading, accounts, accountId]);
  useEffect(() => {
    const load = async () => {
      if (!accountId) return;
      const res = await axios.get(`${API}/calendar`, { params: { accountId, month } });
      setPoints(res.data.points || []);
    };
    load();
  }, [accountId, month]);
  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 12 }}>
        <AccountSelector accounts={accounts} value={accountId} onChange={setAccountId} />
      </div>
      <div className="card">{points.length === 0 ? 'No data for this month yet.' : `${points.length} days with data.`}</div>
    </div>
  );
};

const Risk = () => {
  const { accounts, loading } = useAccounts();
  const [accountId, setAccountId] = useState("");
  const [risk, setRisk] = useState(null);
  useEffect(() => { if (!loading && accounts.length && !accountId) setAccountId(accounts[0].id); }, [loading, accounts, accountId]);
  useEffect(() => {
    const load = async () => {
      if (!accountId) return;
      const res = await axios.get(`${API}/risk/overview`, { params: { accountId } });
      setRisk(res.data);
    };
    load();
  }, [accountId]);
  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 12 }}>
        <AccountSelector accounts={accounts} value={accountId} onChange={setAccountId} />
      </div>
      <div className="card">{risk ? `Points: ${risk.equity_curve.length}, Max DD: ${(risk.max_drawdown*100).toFixed(2)}%` : 'No risk data yet.'}</div>
    </div>
  );
};

const Journal = () => {
  const [text, setText] = useState("");
  const [saved, setSaved] = useState(null);
  const today = new Date().toISOString().slice(0,10);
  const save = async () => {
    try {
      const res = await axios.post(`${API}/journal/entry/upsert`, { date: today, text });
      setSaved(res.data);
    } catch (e) {
      console.error("save failed", e);
    }
  };
  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Daily note ({today})</div>
        <textarea value={text} onChange={(e)=>setText(e.target.value)} rows={8} style={{ width: '100%', background:'#0b0b0c', color:'#fff', border:'1px solid #374151', borderRadius: 8, padding: 8 }} placeholder="Write your notes…" />
        <div style={{ marginTop: 8 }}>
          <button onClick={save} style={{ background:'#2563eb', border:'none', padding:'8px 12px', borderRadius: 8, color:'#fff', fontWeight:700 }}>Save</button>
        </div>
        {saved && <div style={{ color:'#9ca3af', marginTop:8 }}>Saved.</div>}
      </div>
    </div>
  );
};

const Admin = () => {
  const { accounts, loading } = useAccounts();
  const [editName, setEditName] = useState("");
  const [selected, setSelected] = useState("");
  useEffect(() => {
    if (!loading && accounts.length && !selected) {
      setSelected(accounts[0].external_account_id);
      setEditName(accounts[0].name);
    }
  }, [loading, accounts, selected]);
  const save = async () => {
    try {
      await axios.patch(`${API}/admin/accounts/${selected}`, { name: editName });
      window.location.reload();
    } catch (e) {
      console.error("update failed", e);
    }
  };
  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Accounts</div>
        {loading ? 'Loading…' : (
          <div style={{ display:'flex', gap:12, alignItems:'center' }}>
            <select className="select" value={selected} onChange={(e)=>{
              const ea = e.target.value; setSelected(ea);
              const acc = accounts.find(a=>a.external_account_id===ea); setEditName(acc?.name || "");
            }}>
              {accounts.map(a=> <option key={a.external_account_id} value={a.external_account_id}>{a.name} ({a.external_account_id})</option>)}
            </select>
            <input className="select" style={{ width: 320 }} value={editName} onChange={(e)=>setEditName(e.target.value)} />
            <button onClick={save} style={{ background:'#10b981', border:'none', padding:'8px 12px', borderRadius: 8, color:'#0b0b0c', fontWeight:700 }}>Save</button>
          </div>
        )}
      </div>
      <div className="card">
        <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>DMA EOD Ingest</div>
        <div style={{ color:'#9ca3af' }}>Nightly ingest scheduled for 22:30 SAST per your preference. Manual trigger requires internal job token.</div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="app-shell">
      <BrowserRouter>
        <TopBar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trades" element={<Trades />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/risk" element={<Risk />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;