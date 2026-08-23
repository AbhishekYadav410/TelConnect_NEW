import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api.js';

export default function Alerts() {
  const nav = useNavigate();
  const [alerts, setAlerts] = useState([]);

  const load = () => api.get('/api/admin/alerts').then(setAlerts).catch(() => {});
  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  const markRead = async (a) => {
    await api.post(`/api/admin/alerts/${a.notification_id}/read`);
    load();
  };

  const markAllRead = async () => {
    const unread = alerts.filter((a) => !a.read);
    for (const a of unread) {
      await api.post(`/api/admin/alerts/${a.notification_id}/read`);
    }
    load();
  };

  const unreadCount = alerts.filter((a) => !a.read).length;

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 className="page-title">Alert inbox</h2>
          <p className="page-sub">Real-time alerts for network spikes, high-priority complaints, and customer human-escalation requests.</p>
        </div>
        {unreadCount > 1 && (
          <button className="btn ghost sm" onClick={markAllRead}>
            Mark all read ({unreadCount})
          </button>
        )}
      </div>

      <div className="card">
        {!alerts.length && <div className="empty">No alerts yet. System alerts and customer escalation requests will appear here in real time.</div>}
        {alerts.map((a) => {
          const isEscalation = a.match_reason?.includes('escalation') || a.match_reason?.includes('high_priority');
          return (
            <div className={`alert-row${a.read ? '' : ' unread'}`} key={a.notification_id}>
              <span className="alert-flag" aria-hidden="true" style={{ color: isEscalation ? 'var(--alert)' : 'var(--amber)' }}>
                {isEscalation ? '⚡' : '⚠'}
              </span>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: a.read ? 400 : 600 }}>{a.draft_text}</div>
                <div className="small muted mono" style={{ marginTop: 4 }}>
                  {new Date(a.created_at).toLocaleString()} · {a.match_reason}
                  {a.incident_status && <> · incident: {a.incident_status} / {a.admin_ack_status}</>}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                {isEscalation ? (
                  <button className="btn sm" onClick={() => nav('/admin/queue')}>Manage Ticket →</button>
                ) : (
                  <button className="btn ghost sm" onClick={() => nav('/admin/incidents')}>View root cause</button>
                )}
                {!a.read && <button className="btn ghost sm" onClick={() => markRead(a)}>Mark read</button>}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
