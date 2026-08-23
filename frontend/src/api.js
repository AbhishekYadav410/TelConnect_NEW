const BASE = 'http://localhost:8000';

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
  const res = await fetch(BASE + path, { ...opts, headers });
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
