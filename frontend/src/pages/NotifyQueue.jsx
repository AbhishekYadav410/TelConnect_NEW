import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api.js';

export default function NotifyQueue() {
  const nav = useNavigate();
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);

  const load = () => api.get('/api/admin/notifications/queue').then(setItems).catch(() => {});
  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  const decide = async (n, status) => {
    setBusy(true);
    try {
      await api.post(`/api/admin/notifications/${n.notification_id}/approval`, { status });
      await load();
    } catch {}
    setBusy(false);
  };

  const decideAll = async (status) => {
    setBusy(true);
    try {
      for (const n of pending) {
        await api.post(`/api/admin/notifications/${n.notification_id}/approval`, { status });
      }
      await load();
    } catch {}
    setBusy(false);
  };

  const pending = items.filter((n) => n.approval_status === 'pending');
  const decided = items.filter((n) => n.approval_status !== 'pending');

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 className="page-title">Proactive notification queue</h2>
          <p className="page-sub">
            Drafted incident broadcast messages to affected customers. Nothing sends without your explicit approval (human-in-the-loop).
          </p>
        </div>
        {pending.length > 1 && (
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn sm" disabled={busy} onClick={() => decideAll('approved')}>
              Approve All ({pending.length})
            </button>
            <button className="btn danger sm" disabled={busy} onClick={() => decideAll('rejected')}>
              Reject All
            </button>
          </div>
        )}
      </div>

      <div className="card dossier" style={{ margin: '12px 0 16px', borderLeftColor: 'var(--signal)' }}>
        <p className="small" style={{ margin: 0 }}>
          💡 <b>Looking for customer tickets or human escalation requests?</b> Customer complaints are managed in the{' '}
          <a style={{ color: 'var(--signal)', cursor: 'pointer', fontWeight: 600 }} onClick={() => nav('/admin/queue')}>
            Complaint Queue →
          </a>{' '}
          and urgent escalation alerts land in the{' '}
          <a style={{ color: 'var(--signal)', cursor: 'pointer', fontWeight: 600 }} onClick={() => nav('/admin/alerts')}>
            Alert Inbox →
          </a>.
        </p>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>Awaiting your approval ({pending.length})</h3>
          {pending.length > 0 && <span className="badge amber">Action Required</span>}
        </div>
        {!pending.length && (
          <div className="empty">
            Nothing pending. Drafts appear automatically once an incident has a confirmed root cause, and require your approval before sending.
          </div>
        )}
        {pending.map((n) => (
          <div className="alert-row" key={n.notification_id} style={{ padding: '14px', border: '1px solid var(--line)', borderRadius: 10, marginBottom: 10, background: 'var(--panel)' }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                <span className="badge violet">{n.incident_id}</span>
                <b>{n.customer_name}</b>
                <span className="small muted">· {n.incident_region}</span>
                <span className="badge amber small" style={{ fontSize: 10 }}>Pending Consent</span>
              </div>
              <p className="small" style={{ background: 'var(--panel-2)', padding: '10px 12px', borderRadius: 8, borderLeft: '3px solid var(--signal)', margin: '6px 0' }}>
                “{n.draft_text}”
              </p>
              <div className="small muted mono" style={{ fontSize: 11, marginTop: 4 }}>
                Matched via: {n.match_reason} · Created: {new Date(n.created_at).toLocaleString()}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, flexShrink: 0, justifyContent: 'center' }}>
              <button className="btn sm" disabled={busy} onClick={() => decide(n, 'approved')}>
                Approve &amp; Send
              </button>
              <button className="btn danger sm" disabled={busy} onClick={() => decide(n, 'rejected')}>
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3>Decided Broadcasts ({decided.length})</h3>
        {!decided.length && <div className="empty">No decided incident notifications yet.</div>}
        {decided.map((n) => (
          <div className="alert-row" key={n.notification_id} style={{ alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <span className={`badge ${n.approval_status === 'approved' ? 'teal' : 'red'}`}>
                {n.approval_status === 'approved' ? 'Approved & Sent' : 'Rejected'}
              </span>
              <span className="small" style={{ marginLeft: 8, fontWeight: 600 }}>{n.customer_name}</span>
              <span className="small muted"> ({n.incident_region}) — “{n.draft_text.slice(0, 100)}…”</span>
            </div>
            <span className="small muted mono" style={{ fontSize: 11 }}>
              {n.sent_at ? `Sent ${new Date(n.sent_at).toLocaleTimeString()}` : `Decided ${new Date(n.created_at).toLocaleTimeString()}`}
            </span>
          </div>
        ))}
      </div>
    </>
  );
}
