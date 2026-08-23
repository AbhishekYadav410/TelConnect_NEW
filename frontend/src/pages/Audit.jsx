import React, { useEffect, useState } from 'react';
import { api } from '../api.js';

const ACTION_BADGE = {
  'ticket.update': 'violet', 'ticket.propose_resolution': 'teal',
  'dataset.ingest': 'amber', 'incident.ack': 'grey',
  'incident.resolve': 'teal', 'notification.approval': 'red',
};

export default function Audit() {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    const load = () => api.get('/api/admin/audit?limit=150').then(setRows).catch(() => {});
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      <h2 className="page-title">Audit log</h2>
      <p className="page-sub">Every privileged action — who changed what, when, and on which record. Immutable.</p>
      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="data">
          <thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Target</th><th>Detail</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.audit_id}>
                <td className="mono small">{new Date(r.created_at).toLocaleString()}</td>
                <td className="small">{r.actor_role}<div className="mono muted" style={{ fontSize: 10 }}>{r.actor_id}</div></td>
                <td><span className={`badge ${ACTION_BADGE[r.action] || 'grey'}`}>{r.action}</span></td>
                <td className="mono small">{r.target}</td>
                <td className="small muted">{r.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length && <div className="empty">No audited actions yet.</div>}
      </div>
    </>
  );
}
