import React, { useEffect, useState } from 'react';
import { api } from '../api.js';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [busy, setBusy] = useState('');

  const load = () => api.get('/api/admin/incidents').then(setIncidents).catch(() => {});
  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  const act = async (fn, key) => {
    setBusy(key);
    try { await fn(); await load(); } catch (ex) { alert(ex.message); }
    setBusy('');
  };

  return (
    <>
      <h2 className="page-title">Incidents &amp; root-cause investigation</h2>
      <p className="page-sub">Every AI hypothesis is shown with its computed evidence and confidence — never a bare claim.</p>
      {!incidents.length && <div className="empty">No incidents detected. The spike detector opens one automatically when a region breaches its rolling baseline.</div>}
      <div className="grid" style={{ gridTemplateColumns: '1fr' }}>
        {incidents.map((inc) => (
          <div className="card dossier" key={inc.incident_id}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <span className="mono" style={{ fontWeight: 600 }}>{inc.incident_id}</span>
              <span className={`badge ${inc.status === 'resolved' ? 'teal' : inc.status === 'open' ? 'red' : 'amber'}`}>{inc.status}</span>
              <span className="badge grey">{inc.admin_ack_status}</span>
              <span className="grow" style={{ flex: 1 }} />
              <span className="small muted">opened {new Date(inc.opened_at).toLocaleString()}</span>
            </div>
            <p className="small muted" style={{ margin: '8px 0 12px' }}>
              {inc.region} · {inc.service_type || 'multiple services'} · {inc.complaint_count} complaints
              · density {inc.spike_pct > 500 ? `${Math.round(inc.spike_pct / 100 + 1)}x` : `+${Math.round(inc.spike_pct)}%`} vs baseline
            </p>

            {inc.root_cause ? (
              <>
                <div className="badge violet" style={{ marginBottom: 6 }}>root cause analysis</div>
                <div className="cause">{inc.root_cause}</div>
                <div className="small muted" style={{ marginTop: 6 }}>Confidence {Math.round(inc.confidence)}%</div>
                <div className="confbar"><i style={{ width: `${inc.confidence}%` }} /></div>
                <ul className="evidence">
                  {(inc.evidence || []).map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              </>
            ) : (
              <button className="btn sm" disabled={busy === inc.incident_id}
                onClick={() => act(() => api.post(`/api/admin/incidents/${inc.incident_id}/investigate`), inc.incident_id)}>
                {busy === inc.incident_id ? 'Investigating…' : 'Run root-cause investigation'}
              </button>
            )}

            <div style={{ display: 'flex', gap: 8, marginTop: 14, flexWrap: 'wrap' }}>
              {inc.admin_ack_status === 'unacknowledged' && (
                <button className="btn ghost sm" onClick={() => act(() =>
                  api.post(`/api/admin/incidents/${inc.incident_id}/ack`, { ack_status: 'acknowledged' }), inc.incident_id + 'a')}>
                  Acknowledge
                </button>
              )}
              {inc.admin_ack_status === 'acknowledged' && (
                <button className="btn ghost sm" onClick={() => act(() =>
                  api.post(`/api/admin/incidents/${inc.incident_id}/ack`, { ack_status: 'assigned' }), inc.incident_id + 'b')}>
                  Assign to field team
                </button>
              )}
              <button className="btn ghost sm" onClick={() => act(() =>
                api.post(`/api/admin/incidents/${inc.incident_id}/draft-notifications`), inc.incident_id + 'c')}>
                Draft customer notifications
              </button>
              {inc.status !== 'resolved' && (
                <button className="btn danger sm" onClick={() => act(() =>
                  api.post(`/api/admin/incidents/${inc.incident_id}/resolve`), inc.incident_id + 'd')}>
                  Mark resolved
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
