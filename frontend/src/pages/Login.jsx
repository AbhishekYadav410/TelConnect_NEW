import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, setSession } from '../api.js';

const REGIONS = ['Raj Nagar, Ghaziabad', 'Indirapuram, Ghaziabad', 'Connaught Place, Delhi',
  'Dwarka, Delhi', 'Gurgaon Sector 29', 'Noida Sector 62', 'Andheri, Mumbai', 'Bandra, Mumbai',
  'Koramangala, Bangalore', 'Whitefield, Bangalore', 'T Nagar, Chennai', 'Salt Lake, Kolkata',
  'Others'];

export default function Login() {
  const nav = useNavigate();
  const [role, setRole] = useState('admin');
  const [mode, setMode] = useState('login'); // login | signup (customer only)
  const [form, setForm] = useState({
    email: '', password: '', name: '', customRegion: '',
    region: REGIONS[0], service_type: 'broadband',
  });
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const pickRole = (r) => {
    setRole(r); setMode('login'); setErr('');
    setForm((prev) => ({
      ...prev,
      email: '',
      password: '',
      name: '',
      customRegion: '',
    }));
  };

  const fillDemo = (demoEmail, demoPassword, demoRole) => {
    setRole(demoRole);
    setMode('login');
    setErr('');
    setForm((prev) => ({
      ...prev,
      email: demoEmail,
      password: demoPassword,
    }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr(''); setBusy(true);
    try {
      const regionValue = form.region === 'Others'
        ? (form.customRegion?.trim() || 'Others')
        : form.region;
      const res = mode === 'signup'
        ? await api.post('/api/auth/signup', {
          name: form.name, email: form.email, password: form.password,
          region: regionValue, service_type: form.service_type
        })
        : await api.post('/api/auth/login', { email: form.email, password: form.password });
      if (!res) {
        setBusy(false);
        return;
      }
      if (role === 'admin' && res.user?.role !== 'admin') {
        setErr('This account is not an admin account. Please switch to Customer tab.');
        setBusy(false);
        return;
      }
      setSession(res.token, res.user);
      nav(res.user.role === 'admin' ? '/admin' : '/chat');
    } catch (ex) {
      setErr(ex.message || 'Authentication failed. Please try again.');
    }
    setBusy(false);
  };

  const isUnregistered = err.toLowerCase().includes('not registered') || err.toLowerCase().includes('sign up');

  return (
    <div className="login-wrap">
      <div className="card login-card">
        <div className="wordmark">
          <div className="sigbars p4" aria-hidden="true" style={{ height: 20, marginBottom: 10 }}>
            <i /><i /><i /><i />
          </div>
          <h1>TelConnect</h1>
          <div className="brand-sub">Telecom operations &amp; resolution assistant</div>
        </div>
        <div className="role-tabs" role="tablist">
          <button type="button" className={role === 'admin' ? 'on' : ''} onClick={() => pickRole('admin')}>Company admin</button>
          <button type="button" className={role === 'customer' ? 'on' : ''} onClick={() => pickRole('customer')}>Customer</button>
        </div>
        <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
          {mode === 'signup' && (
            <input className="field" placeholder="Full name" value={form.name} onChange={set('name')} required />
          )}
          <input className="field" type="email" placeholder="Email" value={form.email} onChange={set('email')} required />
          <input className="field" type="password" placeholder="Password" value={form.password} onChange={set('password')} required />
          {mode === 'signup' && (
            <>
              <select className="field" value={form.region} onChange={set('region')}>
                {REGIONS.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
              {form.region === 'Others' && (
                <input
                  className="field"
                  placeholder="Specify your area / city (optional)"
                  value={form.customRegion || ''}
                  onChange={set('customRegion')}
                />
              )}
              <select className="field" value={form.service_type} onChange={set('service_type')}>
                <option>broadband</option><option>mobile data</option>
                <option>voice</option><option>other</option>
              </select>
            </>
          )}
          {err && (
            <div style={{
              background: 'rgba(240,84,79,.12)',
              border: '1px solid var(--alert)',
              borderRadius: 8,
              padding: '10px 12px',
              color: 'var(--alert)',
              fontSize: 13,
              display: 'flex',
              flexDirection: 'column',
              gap: 6
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 16 }}>⚠</span>
                <span>{err}</span>
              </div>
              {role === 'customer' && mode === 'login' && isUnregistered && (
                <button
                  type="button"
                  className="btn ghost sm"
                  style={{ alignSelf: 'flex-start', marginTop: 4, borderColor: 'var(--alert)', color: 'var(--text)' }}
                  onClick={() => { setMode('signup'); setErr(''); }}
                >
                  Sign up now →
                </button>
              )}
            </div>
          )}
          <button className="btn" disabled={busy}>
            {mode === 'signup' ? 'Create account' : 'Sign in'}
          </button>
        </form>
        {role === 'customer' && (
          <button className="btn ghost" style={{ width: '100%', marginTop: 10 }}
            onClick={() => { setMode(mode === 'signup' ? 'login' : 'signup'); setErr(''); }}>
            {mode === 'signup' ? 'Back to sign in' : 'New customer? Create an account'}
          </button>
        )}
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <p className="small muted" style={{ marginBottom: 6 }}>
            Demo accounts (click to autofill):
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
            <button
              type="button"
              className="btn ghost sm"
              style={{ fontSize: 11, padding: '3px 8px' }}
              onClick={() => fillDemo('admin@telecom.com', 'admin123', 'admin')}
            >
              Admin
            </button>
            <button
              type="button"
              className="btn ghost sm"
              style={{ fontSize: 11, padding: '3px 8px' }}
              onClick={() => fillDemo('rohan@example.com', 'customer123', 'customer')}
            >
              Customer (Rohan)
            </button>
          </div>
        </div>
        <p className="small" style={{ marginTop: 12, textAlign: 'center' }}>
          <a href="/" style={{ color: 'var(--muted)' }}>← Back to overview</a>
        </p>
      </div>
    </div>
  );
}
