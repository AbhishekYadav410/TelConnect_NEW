import React, { useEffect, useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { api, clearSession, user } from '../api.js';

const NAV = [
  ['/admin', 'Overview', true],
  ['/admin/assistant', '🤖 AI Assistant', false],
  ['/admin/upload', 'Dataset upload', false],
  ['/admin/queue', 'Complaint queue', false],
  ['/admin/heatmap', 'Network heatmap', false],
  ['/admin/incidents', 'Incidents & root cause', false],
  ['/admin/alerts', 'Alert inbox', false],
  ['/admin/notifications', 'Notify queue', false],
  ['/admin/audit', 'Audit log', false],
];

export default function AdminLayout() {
  const nav = useNavigate();
  const [health, setHealth] = useState({});
  const [alertCount, setAlertCount] = useState(0);
  const [tick, setTick] = useState(new Date());
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const [h, alerts] = await Promise.all([api.get('/api/health'), api.get('/api/admin/alerts')]);
        if (!alive) return;
        setHealth(h);
        setAlertCount(alerts.filter((a) => !a.read).length);
        setTick(new Date());
      } catch { /* backend briefly away — keep last state */ }
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  return (
    <div className="shell">
      {/* Mobile Top Header */}
      <header className="mobile-admin-header">
        <button
          className="btn ghost sm mobile-menu-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? '✕' : '☰'}
        </button>
        <div className="brand-name">TelConnect <span className="brand-sub-badge">Admin</span></div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8 }}>
          {alertCount > 0 && <span className="badge red">{alertCount}</span>}
          <span className="live-dot" aria-hidden="true" />
        </div>
      </header>

      {/* Mobile Nav Overlay Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-nav-backdrop" onClick={() => setMobileMenuOpen(false)}>
          <div className="mobile-nav-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="brand" style={{ padding: '16px 12px 12px' }}>
              <div className="brand-name">TelConnect</div>
              <div className="brand-sub">Admin console</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, padding: '0 8px' }}>
              {NAV.map(([to, label, end]) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) => `nav${isActive ? ' active' : ''}`}
                >
                  {label}
                  {label === 'Alert inbox' && alertCount > 0 && <span className="badge red">{alertCount}</span>}
                </NavLink>
              ))}
            </div>
            <div className="spacer" />
            <div style={{ padding: '16px 12px', borderTop: '1px solid var(--line)', marginTop: 'auto' }}>
              <div className="small muted" style={{ marginBottom: 8 }}>{user()?.name}</div>
              <button
                className="btn ghost sm"
                style={{ width: '100%' }}
                onClick={() => { clearSession(); nav('/'); }}
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Desktop Rail Navigation */}
      <nav className="rail">
        <div className="brand">
          <div className="brand-name">TelConnect</div>
          <div className="brand-sub">Admin console</div>
        </div>
        {NAV.map(([to, label, end]) => (
          <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav${isActive ? ' active' : ''}`}>
            {label}
            {label === 'Alert inbox' && alertCount > 0 && <span className="badge red">{alertCount}</span>}
          </NavLink>
        ))}
        <div className="spacer" />
        <div className="small muted" style={{ padding: '0 10px 8px' }}>{user()?.name}</div>
        <button className="btn ghost sm" style={{ margin: '0 10px' }}
          onClick={() => { clearSession(); nav('/'); }}>Sign out</button>
      </nav>
      <main className="main">
        <div className="statusbar">
          <span className="live-dot" aria-hidden="true" /> LIVE
          <span>refreshed {tick.toLocaleTimeString()}</span>
          <span className="grow" />
          <span>LLM: {health.groq_live ? 'Groq connected' : 'offline fallback'}</span>
          <span>dataset: {health.ingest_done ? 'active' : 'awaiting upload'}</span>
        </div>
        <Outlet />
      </main>
    </div>
  );
}
