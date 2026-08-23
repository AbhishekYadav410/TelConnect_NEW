import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Line, LineChart,
  Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { api } from '../api.js';
import { useTheme } from '../ThemeContext.jsx';

const CAT_COLORS = { network: '#F0544F', billing: '#F5A623', service: '#8B7CF6', device: '#2DD4BF', other: '#8A97AC' };

export default function Overview() {
  const { theme } = useTheme();
  const isLight = theme === 'light';
  const tooltipStyle = {
    background: isLight ? '#FFFFFF' : '#1C2638',
    border: isLight ? '1px solid #E8DFD6' : '1px solid #263248',
    borderRadius: 8,
    fontSize: 12,
    color: isLight ? '#191E24' : '#E8EDF6',
    boxShadow: isLight ? '0 4px 12px rgba(0,0,0,0.08)' : '0 4px 12px rgba(0,0,0,0.4)',
  };
  const gridStroke = isLight ? '#E8DFD6' : '#263248';
  const tickFill = isLight ? '#6B7280' : '#8A97AC';
  const axisTextFill = isLight ? '#191E24' : '#E8EDF6';

  const [data, setData] = useState(null);
  const [risk, setRisk] = useState([]);
  const [err, setErr] = useState('');

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        const [s, r] = await Promise.all([
          api.get('/api/admin/analytics/summary'), api.get('/api/admin/analytics/risk')]);
        if (alive) { setData(s); setRisk(r.slice(0, 8)); setErr(''); }
      } catch (ex) { if (alive) setErr(ex.message); }
    };
    load();
    const id = setInterval(load, 15000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  if (err) return <div className="empty">Could not load analytics: {err}</div>;
  if (!data) return <div className="empty">Loading dashboard…</div>;
  const { resolution } = data;
  if (!resolution.total) {
    return (
      <div className="empty">
        No complaint data yet. <Link to="/admin/upload" style={{ color: 'var(--signal)' }}>
          Upload your company's complaint dataset</Link> to activate the pipeline.
      </div>
    );
  }

  return (
    <>
      <h2 className="page-title">Operations overview</h2>
      <p className="page-sub">Live across {resolution.total.toLocaleString()} complaints — refreshes automatically.</p>

      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        <div className="card"><div className="stat-num">{resolution.total.toLocaleString()}</div><div className="stat-label">Total complaints</div></div>
        <div className="card"><div className="stat-num" style={{ color: 'var(--alert)' }}>{resolution.open}</div><div className="stat-label">Open (new + reopened)</div></div>
        <div className="card"><div className="stat-num" style={{ color: 'var(--amber)' }}>{resolution.in_progress}</div><div className="stat-label">In progress</div></div>
        <div className="card"><div className="stat-num" style={{ color: 'var(--signal)' }}>{Math.round(resolution.resolution_rate * 100)}%</div><div className="stat-label">Closed &amp; confirmed</div></div>
      </div>
      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        <div className="card"><div className="stat-num" style={{ color: resolution.sla_breaches ? 'var(--alert)' : 'var(--signal)' }}>{resolution.sla_breaches}</div><div className="stat-label">SLA breaches</div></div>
        <div className="card"><div className="stat-num" style={{ color: 'var(--alert)' }}>{resolution.escalated}</div><div className="stat-label">Escalated</div></div>
        <div className="card"><div className="stat-num" style={{ color: 'var(--violet)' }}>{resolution.pending_confirmation}</div><div className="stat-label">Awaiting customer confirm</div></div>
        <div className="card">
          <div className="stat-num" style={{ color: 'var(--amber)' }}>{resolution.avg_rating ?? '—'}</div>
          <div className="stat-label">Avg feedback ({resolution.feedback_count || 0} ratings)</div>
          <div className="factor-list" style={{ marginTop: 8 }}>
            {(resolution.priority_distribution || []).map((p) => (
              <span key={p.priority_label} className={`badge ${p.priority_label === 'P1' ? 'red' : p.priority_label === 'P2' ? 'amber' : 'grey'}`}>
                {p.priority_label}: {p.count}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <div className="card">
          <h3>Complaint volume over time</h3>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={data.volume}>
              <CartesianGrid stroke={gridStroke} strokeDasharray="3 3" />
              <XAxis dataKey="day" tick={{ fill: tickFill, fontSize: 11 }} />
              <YAxis tick={{ fill: tickFill, fontSize: 11 }} width={36} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area dataKey="count" stroke={isLight ? '#0D9488' : '#2DD4BF'} fill={isLight ? 'rgba(13,148,136,.15)' : 'rgba(45,212,191,.15)'} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Category breakdown</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={data.categories} dataKey="count" nameKey="category"
                innerRadius={55} outerRadius={85} paddingAngle={2}
                label={({ category, count }) => `${category} (${count})`}
                labelLine={false} fontSize={11}>
                {data.categories.map((c) => (
                  <Cell key={c.category} fill={CAT_COLORS[c.category] || (isLight ? '#6B7280' : '#8A97AC')} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid cols-2" style={{ marginBottom: 16 }}>
        <div className="card">
          <h3>Sentiment trend (avg polarity by day)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data.sentiment_trend}>
              <CartesianGrid stroke={gridStroke} strokeDasharray="3 3" />
              <XAxis dataKey="day" tick={{ fill: tickFill, fontSize: 11 }} />
              <YAxis domain={[-1, 1]} tick={{ fill: tickFill, fontSize: 11 }} width={36} />
              <Tooltip contentStyle={tooltipStyle} />
              <Line dataKey="avg_sentiment" stroke={isLight ? '#7C3AED' : '#8B7CF6'} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Recurring issue themes</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.recurring_themes} layout="vertical" margin={{ left: 40 }}>
              <XAxis type="number" tick={{ fill: tickFill, fontSize: 11 }} />
              <YAxis type="category" dataKey="theme" width={110} tick={{ fill: axisTextFill, fontSize: 11 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" fill={isLight ? '#D97706' : '#F5A623'} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3>Highest escalation risk — open complaints</h3>
        <table className="data">
          <thead><tr><th>Priority</th><th>Ticket</th><th>Summary</th><th>Region</th><th>Risk</th></tr></thead>
          <tbody>
            {risk.map((r) => {
              const p = r.priority_score >= 0.75 ? 4 : r.priority_score >= 0.55 ? 3 : r.priority_score >= 0.35 ? 2 : 1;
              return (
                <tr key={r.complaint_id}>
                  <td><span className={`sigbars p${p}`} title={`priority ${r.priority_score}`}><i /><i /><i /><i /></span></td>
                  <td className="mono">{r.complaint_id}</td>
                  <td>{r.ticket_summary}
                    <div className="factor-list">
                      {(r.priority_factors || []).slice(0, 3).map((f, i) => (
                        <span key={i} className="badge grey">{f.factor}</span>
                      ))}
                    </div>
                  </td>
                  <td className="small">{r.region}</td>
                  <td><span className={`badge ${r.escalation_risk >= 0.6 ? 'red' : 'amber'}`}>{Math.round(r.escalation_risk * 100)}%</span></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
