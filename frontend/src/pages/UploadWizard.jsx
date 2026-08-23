import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, BASE_URL } from '../api.js';

const FIELDS = ['text', 'category', 'channel', 'timestamp', 'region', 'lat', 'long',
  'service_type', 'network_type', 'device', 'status', 'resolution', 'external_id'];

export default function UploadWizard() {
  const nav = useNavigate();
  const [step, setStep] = useState(1);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [result, setResult] = useState(null);

  const doPreview = async () => {
    if (!file) return;
    setBusy(true); setErr('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      const p = await api.postForm('/api/admin/upload/preview', fd);
      setPreview(p);
      setMapping(p.suggested_mapping);
      setStep(2);
    } catch (ex) { setErr(ex.message); }
    setBusy(false);
  };

  const doIngest = async () => {
    setBusy(true); setErr('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('mapping', JSON.stringify(mapping));
      const r = await api.postForm('/api/admin/upload/ingest', fd);
      setResult(r);
      setStep(3);
    } catch (ex) { setErr(ex.message); }
    setBusy(false);
  };

  return (
    <>
      <h2 className="page-title">Dataset upload &amp; schema mapping</h2>
      <p className="page-sub">Onboard any telecom company's complaint export — map its columns once, the pipeline does the rest.</p>
      <div className="steps">
        <span className={step >= 1 ? 'on' : ''}>1 · choose file</span>
        <span className={step >= 2 ? 'on' : ''}>2 · confirm mapping</span>
        <span className={step >= 3 ? 'on' : ''}>3 · pipeline result</span>
      </div>

      {step === 1 && (
        <div className="card" style={{ maxWidth: 560 }}>
          <h3>Complaint CSV</h3>
          <input className="field" type="file" accept=".csv" aria-label="Complaint CSV file"
            onChange={(e) => setFile(e.target.files[0])} />
          <p className="small muted" style={{ margin: '12px 0' }}>
            No file handy? <a style={{ color: 'var(--signal)' }} href={`${BASE_URL}/api/demo/sample-csv`}>
            Download the demo dataset</a> (1,300 realistic complaints with a live network spike), then upload it here.
          </p>
          {err && <div className="small" style={{ color: 'var(--alert)', marginBottom: 10 }}>{err}</div>}
          <button className="btn" onClick={doPreview} disabled={!file || busy}>
            {busy ? 'Reading…' : 'Preview & map columns'}
          </button>
        </div>
      )}

      {step === 2 && preview && (
        <div className="grid cols-2">
          <div className="card">
            <h3>Column mapping (auto-suggested — adjust if wrong)</h3>
            {FIELDS.map((f) => (
              <div className="map-row" key={f}>
                <label className="mono" htmlFor={`map-${f}`}>{f}{f === 'text' && ' *'}</label>
                <select id={`map-${f}`} className="field" value={mapping[f] || ''}
                  onChange={(e) => setMapping({ ...mapping, [f]: e.target.value || null })}>
                  <option value="">— not present —</option>
                  {preview.headers.map((h) => <option key={h} value={h}>{h}</option>)}
                </select>
              </div>
            ))}
            {err && <div className="small" style={{ color: 'var(--alert)', margin: '10px 0' }}>{err}</div>}
            <div style={{ display: 'flex', gap: 10, marginTop: 14 }}>
              <button className="btn ghost" onClick={() => setStep(1)}>Back</button>
              <button className="btn" onClick={doIngest} disabled={busy || !mapping.text}>
                {busy ? 'Running ETL + ML pipeline…' : 'Confirm mapping & ingest'}
              </button>
            </div>
          </div>
          <div className="card" style={{ overflowX: 'auto' }}>
            <h3>Sample rows</h3>
            <table className="data">
              <thead><tr>{preview.headers.slice(0, 6).map((h) => <th key={h}>{h}</th>)}</tr></thead>
              <tbody>
                {preview.sample.map((row, i) => (
                  <tr key={i}>{preview.headers.slice(0, 6).map((h) => (
                    <td key={h} className="small">{String(row[h] ?? '').slice(0, 48)}</td>))}</tr>
                ))}
              </tbody>
            </table>
            <p className="small muted" style={{ marginTop: 10 }}>
              Name/contact columns are never imported — PII is redacted during ETL before storage or any LLM call.
            </p>
          </div>
        </div>
      )}

      {step === 3 && result && (
        <div className="card" style={{ maxWidth: 560 }}>
          <h3>Pipeline activated</h3>
          <ul className="evidence">
            <li>{result.etl.inserted.toLocaleString()} complaints ingested</li>
            <li>{result.etl.deduplicated} duplicates collapsed (same ticket, multiple channels)</li>
            <li>{result.scored.toLocaleString()} complaints classified, scored &amp; summarised</li>
            <li>{(result.pipeline.opened || []).length} incident(s) opened by the spike detector</li>
            <li>{result.pipeline.notifications_drafted || 0} proactive customer notification(s) drafted</li>
          </ul>
          <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
            <button className="btn" onClick={() => nav('/admin')}>Open dashboard</button>
            <button className="btn ghost" onClick={() => nav('/admin/heatmap')}>View heatmap</button>
          </div>
        </div>
      )}
    </>
  );
}
