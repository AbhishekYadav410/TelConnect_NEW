// Dynamic API base URL: reads VITE_API_URL for production deployment on Vercel
// Falls back to http://localhost:8000 in development
const rawBase = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000' : '');
const BASE = rawBase.replace(/\/+$/, '');

// Cold-start / waking space event manager for Hugging Face Spaces sleeping tier
let activeSlowRequests = 0;
let isWakingState = false;
const wakingListeners = new Set();

function notifyWaking(status) {
  if (isWakingState !== status) {
    isWakingState = status;
    wakingListeners.forEach((cb) => {
      try { cb(status); } catch (e) { console.error(e); }
    });
  }
}

export function subscribeWaking(cb) {
  wakingListeners.add(cb);
  cb(isWakingState);
  return () => wakingListeners.delete(cb);
}

export function isWaking() {
  return isWakingState;
}

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

  // Timer to detect cold start / sleeping space (Hugging Face Spaces)
  let timer = null;
  let didTriggerSlow = false;
  timer = setTimeout(() => {
    didTriggerSlow = true;
    activeSlowRequests += 1;
    notifyWaking(true);
  }, 2000);

  try {
    const res = await fetch(url, { ...opts, headers });
    clearTimeout(timer);
    if (didTriggerSlow) {
      activeSlowRequests = Math.max(0, activeSlowRequests - 1);
      if (activeSlowRequests === 0) notifyWaking(false);
    }

    if (res.status === 401 && !path.startsWith('/api/auth/')) {
      clearSession();
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return null;
    }

    if (!res.ok) {
      // 502/503/504 typically means the container is booting up on Hugging Face Spaces
      if ([502, 503, 504].includes(res.status)) {
        throw new Error('Initializing AI services... Please wait a few moments.');
      }
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status})`);
    }

    const ct = res.headers.get('content-type') || '';
    return ct.includes('json') ? res.json() : res.text();
  } catch (err) {
    clearTimeout(timer);
    if (didTriggerSlow) {
      activeSlowRequests = Math.max(0, activeSlowRequests - 1);
      if (activeSlowRequests === 0) notifyWaking(false);
    }

    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      // Network fetch failure during space wake-up
      throw new Error('Initializing AI services... Please wait a few moments.');
    }
    throw err;
  }
}

export const api = {
  get: (path) => request(path),
  post: (path, json) => request(path, { method: 'POST', json }),
  postForm: (path, formData) => request(path, { method: 'POST', body: formData }),
  patch: (path, json) => request(path, { method: 'PATCH', json }),
};

export const BASE_URL = BASE;
