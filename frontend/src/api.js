// Dynamic API base URL: reads VITE_API_URL for production deployment on Vercel
// Falls back to http://localhost:8000 in development
const rawBase = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
const BASE = rawBase.replace(/\/+$/, '');

export function token() { return localStorage.getItem('tci_token'); }
export function user() {
  const raw = localStorage.getItem('tci_user');
  return raw ? JSON.parse(raw) : null;
}
export function setSession(tok, usr) {
  localStorage.setItem('tci_token', tok);
  localStorage.setItem('tci_user', JSON.stringify(usr));
}
export function clearSession() {
  localStorage.removeItem('tci_token');
  localStorage.removeItem('tci_user');
}

async function request(path, opts = {}) {
  const headers = { ...(opts.headers || {}) };
  if (token()) headers.Authorization = `Bearer ${token()}`;
  if (opts.json) {
    headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(opts.json);
  }
  const url = path.startsWith('http://') || path.startsWith('https://') ? path : `${BASE}${path}`;
  const res = await fetch(url, { ...opts, headers });
  if (res.status === 401 && !path.startsWith('/api/auth/')) {
    clearSession();
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    return null;
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  const ct = res.headers.get('content-type') || '';
  return ct.includes('json') ? res.json() : res.text();
}

export const api = {
  get: (path) => request(path),
  post: (path, json) => request(path, { method: 'POST', json }),
  postForm: (path, formData) => request(path, { method: 'POST', body: formData }),
  patch: (path, json) => request(path, { method: 'PATCH', json }),
};

export const BASE_URL = BASE;
