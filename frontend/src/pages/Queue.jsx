import React, { useEffect, useState } from 'react';
import { api, BASE_URL, token } from '../api.js';

const empty = { category: '', region: '', service_type: '', status: '', channel: '' };
const STATUSES = ['new', 'in_progress', 'waiting_for_customer', 'escalated',
  'resolved_pending_confirmation', 'reopened', 'closed'];
const STATUS_BADGE = { closed: 'teal', new: 'red', reopened: 'red', escalated: 'red',
  in_progress: 'amber', waiting_for_customer: 'amber', resolved_pending_confirmation: 'violet' };

function slaChip(r) {
  if (!r.sla_deadline || r.status === 'closed') return null;
  const breached = new Date(r.sla_deadline) < new Date();
  return (
    <span className={`sla-chip${breached ? ' breach' : ''}`}>
      {breached ? '⏰ SLA breached' : `SLA ${new Date(r.sla_deadline).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}`}
    </span>
  );
}

function ManagePanel({ row, teams, onDone }) {
  const [history, setHistory] = useState([]);
  const [assign, setAssign] = useState(row.assigned_to || '');
  const [status, setStatus] = useState(row.status);
  const [note, setNote] = useState('');
  const [resText, setResText] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    api.get(`/api/admin/complaints/${row.complaint_id}/history`).then(setHistory).catch(() => {});
  }, [row.complaint_id]);

  const act = async (fn, okMsg) => {
    setBusy(true); setMsg('');
    try { await fn(); setMsg(okMsg); onDone(); } catch (ex) { setMsg(ex.message); }
    setBusy(false);
  };

  return (
    <div className="ticket-manage">
      <div>
        <h3 style={{ marginBottom: 8 }}>Manage ticket</h3>
        <div style={{ display: 'grid', gap: 10 }}>
          <label className="small muted" htmlFor={`assign-${row.complaint_id}`}>Assign to team</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <select id={`assign-${row.complaint_id}`} className="field" value={assign}
              onChange={(e) => setAssign(e.target.value)}>
              <option value="">— unassigned —</option>
              {teams.map((t) => <option key={t}>{t}</option>)}
            </select>
            <button className="btn sm" disabled={busy || !assign}
              onClick={() => act(() => api.patch(`/api/admin/complaints/${row.complaint_id}`,
                { assigned_to: assign }), 'Assigned.')}>
              Assign
            </button>
          </div>
          <label className="small muted" htmlFor={`status-${row.complaint_id}`}>Update status</label>
          <div style={{ display: 'flex', gap: 8 }}>
            <select id={`status-${row.complaint_id}`} className="field" value={status}
              onChange={(e) => setStatus(e.target.value)}>
              {STATUSES.map((s) => <option key={s}>{s}</option>)}
            </select>
            <button className="btn sm" disabled={busy || status === row.status}
              onClick={() => act(() => api.patch(`/api/admin/complaints/${row.complaint_id}`,
                { status, note }), 'Status updated — customer notified.')}>
              Update
            </button>
          </div>
          <input className="field" placeholder="Note for the customer (optional)"
            value={note} onChange={(e) => setNote(e.target.value)} />
          <label className="small muted" htmlFor={`res-${row.complaint_id}`}>Propose resolution
            (customer must confirm before it closes)</label>
          <textarea id={`res-${row.complaint_id}`} className="field" rows={2} value={resText}
            onChange={(e) => setResText(e.target.value)}
            placeholder="e.g. Node rebooted at the exchange; service restored." />
          <button className="btn sm" disabled={busy || !resText.trim()}
            onClick={() => act(() => api.post(`/api/admin/complaints/${row.complaint_id}/propose-resolution`,
              { text: resText.trim() }), 'Resolution proposed — awaiting customer confirmation.')}>
            Propose resolution
          </button>
          {msg && <div className="small" style={{ color: 'var(--signal)' }}>{msg}</div>}
        </div>
      </div>
      <div>
        <h3 style={{ marginBottom: 8 }}>Status history</h3>
        <div className="timeline">
          {history.map((h) => (
            <div className="tl-item" key={h.history_id}>
              <b>{h.to_status.replace(/_/g, ' ')}</b>
              <span className="muted"> — {h.actor}</span>
              <div className="muted mono" style={{ fontSize: 10 }}>
                {new Date(h.created_at).toLocaleString()}{h.reason ? ` · ${h.reason}` : ''}
              </div>
            </div>
          ))}
          {!history.length && <div className="small muted">Ingested record — no transitions yet.</div>}
        </div>
      </div>
    </div>
  );
}

export default function Queue() {
  const [filters, setFilters] = useState({ ...empty, search: '', sort_by: 'newest' });
  const [page, setPage] = useState(0);
  const [limit, setLimit] = useState(50);
  const [data, setData] = useState({ total: 0, rows: [] });
  const [expanded, setExpanded] = useState(null);
  const [regions, setRegions] = useState([]);
  const [teams, setTeams] = useState([]);
  const [refresh, setRefresh] = useState(0);

  const qs = () => {
    const p = { ...filters, offset: page * limit, limit };
    return Object.entries(p).filter(([, v]) => v !== '' && v !== null && v !== undefined)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
  };

  useEffect(() => {
    api.get('/api/admin/heatmap').then((cells) => setRegions(cells.map((c) => c.region))).catch(() => {});
    api.get('/api/admin/teams').then(setTeams).catch(() => {});
  }, []);

  useEffect(() => {
    let alive = true;
    api.get(`/api/admin/queue?${qs()}`)
      .then((d) => alive && setData(d)).catch(() => {});
    const id = setInterval(() => {
      api.get(`/api/admin/queue?${qs()}`).then((d) => alive && setData(d)).catch(() => {});
    }, 10000);
    return () => { alive = false; clearInterval(id); };
  }, [filters, page, limit, refresh]);

  const set = (k) => (e) => {
    setFilters({ ...filters, [k]: e.target.value });
    setPage(0);
  };

  const setQuickStatus = (st) => {
    setFilters({ ...filters, status: st });
    setPage(0);
  };

  const exportCsv = async () => {
    const res = await fetch(`${BASE_URL}/api/admin/export.csv${qs() ? '?' + qs() : ''}`,
      { headers: { Authorization: `Bearer ${token()}` } });
    const blob = await res.blob();
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'complaints.csv';
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const totalPages = Math.max(1, Math.ceil((data.total || 0) / limit));

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 className="page-title">Complaint queue &amp; ticket management</h2>
          <p className="page-sub">
            {data.total.toLocaleString()} complaints match. Live updates every 10s. Click any ticket row to manage assignment and status.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn ghost sm" onClick={() => setRefresh((r) => r + 1)}>🔄 Refresh</button>
          <button className="btn sm" onClick={exportCsv}>Export CSV</button>
        </div>
      </div>

      {/* Quick Status Chips */}
      <div style={{ display: 'flex', gap: 6, margin: '8px 0 12px', flexWrap: 'wrap', alignItems: 'center' }}>
        <span className="small muted">Status:</span>
        {[
          ['', 'All Tickets'],
          ['new', 'New (In Queue)'],
          ['escalated', '⚡ Escalated'],
          ['in_progress', 'In Progress'],
          ['resolved_pending_confirmation', 'Pending Confirmation'],
          ['closed', 'Closed'],
        ].map(([val, label]) => (
          <button
            key={val}
            className={`btn sm ${filters.status === val ? '' : 'ghost'}`}
            style={{ fontSize: 11, padding: '4px 10px', height: 'auto' }}
            onClick={() => setQuickStatus(val)}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="filters">
        <input
          className="field"
          style={{ minWidth: 200 }}
          placeholder="Search ticket ID, text, region..."
          value={filters.search}
          onChange={set('search')}
          aria-label="Search complaints"
        />
        <select className="field" value={filters.sort_by} onChange={set('sort_by')} aria-label="Sort order">
          <option value="newest">⏱ Newest first</option>
          <option value="priority">🔥 Highest priority</option>
          <option value="risk">⚡ Highest escalation risk</option>
          <option value="oldest">📅 Oldest first</option>
        </select>
        <select className="field" value={filters.category} onChange={set('category')} aria-label="Filter by category">
          <option value="">All categories</option>
          {['network', 'billing', 'service', 'device', 'other'].map((c) => <option key={c}>{c}</option>)}
        </select>
        <select className="field" value={filters.region} onChange={set('region')} aria-label="Filter by region">
          <option value="">All regions</option>
          {regions.map((r) => <option key={r}>{r}</option>)}
        </select>
        <select className="field" value={filters.service_type} onChange={set('service_type')} aria-label="Filter by service">
          <option value="">All services</option>
          {['broadband', 'mobile data', 'voice', 'other'].map((s) => <option key={s}>{s}</option>)}
        </select>
        <select className="field" value={filters.channel} onChange={set('channel')} aria-label="Filter by channel">
          <option value="">All channels</option>
          {['chat', 'call', 'app', 'email', 'social'].map((c) => <option key={c}>{c}</option>)}
        </select>
        <button className="btn ghost sm" onClick={() => { setFilters({ ...empty, search: '', sort_by: 'newest' }); setPage(0); }}>
          Reset
        </button>
      </div>

      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="data">
          <thead>
            <tr>
              <th>Pri</th>
              <th>Ticket ID / Summary</th>
              <th>Category</th>
              <th>Region</th>
              <th>Channel</th>
              <th>Status</th>
              <th>Assigned</th>
              <th>SLA</th>
            </tr>
          </thead>
          <tbody>
            {data.rows.map((r) => {
              const p = { P1: 4, P2: 3, P3: 2, P4: 1 }[r.priority_label] || 1;
              const open = expanded === r.complaint_id;
              return (
                <React.Fragment key={r.complaint_id}>
                  <tr onClick={() => setExpanded(open ? null : r.complaint_id)} style={{ cursor: 'pointer' }}>
                    <td>
                      <span className={`sigbars p${p}`} title={r.priority_label}><i /><i /><i /><i /></span>
                      <span className="mono muted" style={{ fontSize: 10, marginLeft: 5 }}>{r.priority_label}</span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                        <span className="mono bold" style={{ color: 'var(--signal)', fontSize: 11 }}>{r.complaint_id}</span>
                        <span>{r.ticket_summary || r.text?.slice(0, 90)}</span>
                      </div>
                      <div className="small muted mono" style={{ fontSize: 10, marginTop: 2 }}>
                        {new Date(r.timestamp).toLocaleString()}
                      </div>
                    </td>
                    <td><span className="badge violet">{r.category}</span></td>
                    <td className="small">{r.region}</td>
                    <td><span className="badge grey small" style={{ fontSize: 10 }}>{r.channel || 'chat'}</span></td>
                    <td><span className={`badge ${STATUS_BADGE[r.status] || 'grey'}`}>{r.status.replace(/_/g, ' ')}</span></td>
                    <td className="small">{r.assigned_to || '—'}</td>
                    <td>{slaChip(r)}</td>
                  </tr>
                  {open && (
                    <tr>
                      <td colSpan={8} style={{ background: 'var(--panel-2)' }}>
                        <div className="small" style={{ padding: '6px 2px' }}>
                          <div className="mono muted">
                            {r.complaint_id} · {r.timestamp} · channel: {r.channel || 'chat'} · sentiment: {r.sentiment_label} · risk: {Math.round((r.escalation_risk || 0) * 100)}% · incident: {r.incident_id || '—'}
                          </div>
                          <p style={{ margin: '8px 0', fontSize: 13, background: 'var(--panel)', padding: '8px 12px', borderRadius: 6, border: '1px solid var(--line)' }}>
                            {r.text}
                          </p>
                          <div className="factor-list" style={{ marginBottom: 10 }}>
                            {(r.priority_factors || []).map((f, i) => (
                              <span key={i} className="badge grey">{f.factor} +{f.weight}</span>
                            ))}
                          </div>
                          <ManagePanel row={r} teams={teams} onDone={() => setRefresh((x) => x + 1)} />
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
        {!data.rows.length && <div className="empty">No complaints match these filters.</div>}

        {/* Pagination Footer */}
        {data.total > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 6px 4px', borderTop: '1px solid var(--line)', marginTop: 10, flexWrap: 'wrap', gap: 10 }}>
            <div className="small muted">
              Showing {Math.min(data.total, page * limit + 1)}–{Math.min(data.total, (page + 1) * limit)} of {data.total.toLocaleString()} complaints
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <button className="btn ghost sm" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>
                ← Previous
              </button>
              <span className="small mono">Page {page + 1} of {totalPages}</span>
              <button className="btn ghost sm" disabled={page >= totalPages - 1} onClick={() => setPage((p) => p + 1)}>
                Next →
              </button>
              <select className="field sm" value={limit} onChange={(e) => { setLimit(Number(e.target.value)); setPage(0); }} style={{ width: 85 }}>
                <option value="25">25 / page</option>
                <option value="50">50 / page</option>
                <option value="100">100 / page</option>
              </select>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
