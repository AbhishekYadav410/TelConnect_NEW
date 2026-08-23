import React, { useEffect, useState } from 'react';
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet';
import { useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import { useTheme } from '../ThemeContext.jsx';

const COLORS = { high: '#F0544F', medium: '#F5A623', normal: '#2DD4BF' };

function MapBoundsUpdater({ cells, viewMode }) {
  const map = useMap();
  useEffect(() => {
    if (viewMode === 'india') {
      map.setView([22.5, 79.5], 5);
      return;
    }
    if (viewMode === 'us') {
      map.setView([38.5, -97.0], 4);
      return;
    }
    if (viewMode === 'world') {
      map.setView([25.0, 0.0], 2);
      return;
    }
    const valid = cells.filter((c) => c.lat != null && c.long != null);
    if (!valid.length) return;
    const lats = valid.map((c) => c.lat);
    const lngs = valid.map((c) => c.long);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);
    if (minLat === maxLat && minLng === maxLng) {
      map.setView([minLat, minLng], 8);
    } else {
      map.fitBounds([
        [minLat - 0.5, minLng - 0.5],
        [maxLat + 0.5, maxLng + 0.5],
      ], { padding: [40, 40], maxZoom: 8 });
    }
  }, [cells, viewMode, map]);
  return null;
}

export default function Heatmap() {
  const nav = useNavigate();
  const { theme } = useTheme();
  const [cells, setCells] = useState([]);
  const [filters, setFilters] = useState({ category: '', service_type: '', since: '' });
  const [viewMode, setViewMode] = useState('auto');
  const [search, setSearch] = useState('');

  useEffect(() => {
    let alive = true;
    const qs = Object.entries(filters).filter(([, v]) => v)
      .map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
    const load = () => api.get(`/api/admin/heatmap${qs ? '?' + qs : ''}`)
      .then((d) => alive && setCells(d)).catch(() => { });
    load();
    const id = setInterval(load, 15000);
    return () => { alive = false; clearInterval(id); };
  }, [filters]);

  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.value });
  const max = Math.max(1, ...cells.map((c) => c.count));
  const spiking = cells.filter((c) => c.severity === 'high');
  const validCells = cells.filter((c) => c.lat != null && c.long != null);
  const totalComplaints = cells.reduce((sum, c) => sum + (c.count || 0), 0);
  const totalOpen = cells.reduce((sum, c) => sum + (c.open_count || 0), 0);

  const filteredList = cells
    .filter((c) => !search || c.region.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => b.count - a.count);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 className="page-title">Network issue heatmap</h2>
          <p className="page-sub">
            Plotted {validCells.length} regions ({totalComplaints.toLocaleString()} total complaints, {totalOpen.toLocaleString()} open). Red indicates abnormal concentration vs baseline.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="small muted">View preset:</span>
          <select className="field sm" value={viewMode} onChange={(e) => setViewMode(e.target.value)}>
            <option value="auto">📍 Auto-fit Data</option>
            <option value="india">🇮🇳 India</option>
            <option value="us">🇺🇸 United States</option>
            <option value="world">🌍 Global</option>
          </select>
        </div>
      </div>

      <div className="filters" style={{ marginTop: 10 }}>
        <select className="field" value={filters.category} onChange={set('category')} aria-label="Filter by category">
          <option value="">All categories</option>
          {['network', 'billing', 'service', 'device', 'other'].map((c) => <option key={c}>{c}</option>)}
        </select>
        <select className="field" value={filters.service_type} onChange={set('service_type')} aria-label="Filter by service">
          <option value="">All services</option>
          {['broadband', 'mobile data', 'voice', 'other'].map((s) => <option key={s}>{s}</option>)}
        </select>
        <select className="field" value={filters.since} onChange={set('since')} aria-label="Filter by time range">
          <option value="">All time</option>
          <option value={new Date(Date.now() - 6 * 3600e3).toISOString()}>Last 6 hours</option>
          <option value={new Date(Date.now() - 24 * 3600e3).toISOString()}>Last 24 hours</option>
          <option value={new Date(Date.now() - 7 * 86400e3).toISOString()}>Last 7 days</option>
        </select>
        <span className="small muted" style={{ alignSelf: 'center' }}>
          <span className="badge red">high</span> <span className="badge amber">medium</span> <span className="badge teal">normal</span>
        </span>
      </div>

      {spiking.length > 0 && (
        <div className="card dossier" style={{ marginBottom: 14, borderLeftColor: 'var(--alert)' }}>
          <span className="badge red">spike detected</span>
          <p style={{ marginTop: 8 }}>
            {spiking.slice(0, 5).map((c) => `${c.region} (${c.count} complaints)`).join(' · ')}
            {spiking.length > 5 ? ` and ${spiking.length - 5} more` : ''} — abnormal density vs baseline.{' '}
            <a style={{ color: 'var(--signal)', cursor: 'pointer', fontWeight: 600 }}
              onClick={() => nav('/admin/incidents')}>View incidents &amp; root cause →</a>
          </p>
        </div>
      )}

      <MapContainer center={[22.5, 79.5]} zoom={4} scrollWheelZoom style={{ height: '480px', borderRadius: '12px', border: '1px solid var(--line)' }}>
        <MapBoundsUpdater cells={validCells} viewMode={viewMode} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url={theme === 'light'
            ? "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"} />
        {validCells.map((c) => (
          <CircleMarker key={c.region} center={[c.lat, c.long]}
            radius={Math.max(6, Math.min(32, 6 + 26 * (c.count / max)))}
            pathOptions={{ color: COLORS[c.severity] || COLORS.normal, fillColor: COLORS[c.severity] || COLORS.normal, fillOpacity: 0.45, weight: 2 }}>
            <Popup>
              <div style={{ minWidth: '140px' }}>
                <b style={{ fontSize: '13px' }}>{c.region}</b><br />
                <div style={{ margin: '4px 0', fontSize: '12px' }}>
                  <b>{c.count}</b> complaints · <span style={{ color: 'var(--alert)' }}>{c.open_count} open</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
                  Severity: <span className={`badge ${c.severity === 'high' ? 'red' : c.severity === 'medium' ? 'amber' : 'teal'}`}>{c.severity}</span>
                </div>
                <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px', fontFamily: 'var(--mono)' }}>
                  {c.lat?.toFixed(3)}°, {c.long?.toFixed(3)}°
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="card" style={{ marginTop: 16, overflowX: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
          <h3 style={{ margin: 0 }}>Regions by volume ({filteredList.length})</h3>
          <input
            className="field sm"
            style={{ width: '220px' }}
            placeholder="Search region..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            aria-label="Search regions"
          />
        </div>
        <table className="data">
          <thead><tr><th>Region</th><th>Coordinates</th><th>Complaints</th><th>Open</th><th>Severity</th></tr></thead>
          <tbody>
            {filteredList.map((c) => (
              <tr key={c.region}>
                <td><b>{c.region}</b></td>
                <td className="mono muted small">
                  {c.lat != null && c.long != null ? `${c.lat.toFixed(2)}°, ${c.long.toFixed(2)}°` : '—'}
                </td>
                <td className="mono">{c.count}</td>
                <td className="mono">{c.open_count}</td>
                <td><span className={`badge ${c.severity === 'high' ? 'red' : c.severity === 'medium' ? 'amber' : 'teal'}`}>{c.severity}</span></td>
              </tr>
            ))}
            {!filteredList.length && (
              <tr><td colSpan={5} className="small muted" style={{ textAlign: 'center', padding: '16px' }}>No matching regions found.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
