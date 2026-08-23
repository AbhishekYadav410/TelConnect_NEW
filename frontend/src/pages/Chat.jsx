import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, BASE_URL, clearSession, token, user } from '../api.js';

const PATH_LABELS = {
  incident_aware: 'linked to live incident',
  known_fix: 'known fix from knowledge base',
  registered: 'ticket registered',
  confirm_registration: 'verification',
  status_lookup: 'live status',
  status_none: 'ticket search',
  billing_query: 'approved billing guidance',
  resolution_confirmed: 'resolution confirmed',
  resolution_rejected: 'reopened & escalated',
  feedback_recorded: 'feedback saved',
  escalated: 'escalated to human support',
  reopened: 'ticket reopened',
  fix_worked: 'issue resolved',
  registration_cancelled: 'cancelled',
  clarification: 'clarification requested',
  greeting: 'greeting',
  chitchat: 'support assistant',
  general_query: 'telecom guidance',
  diagnostic: 'line diagnostic report',
};

const LANGUAGES = [
  { id: 'auto', label: '🌐 Auto' },
  { id: 'en', label: 'English' },
  { id: 'hi', label: 'हिन्दी (Hindi)' },
];

const CUSTOMER_ACTIONS = [
  {
    icon: '⚡',
    title: 'Speed Test',
    subtitle: 'Run line diagnostic',
    message: 'Run a speed test and line diagnostic on my connection',
  },
  {
    icon: '📡',
    title: 'Internet Down',
    subtitle: 'Report outage',
    message: 'My broadband internet is down and not working',
  },
  {
    icon: '🎫',
    title: 'My Ticket',
    subtitle: 'Track status',
    message: 'What is the status of my ticket?',
  },
  {
    icon: '💳',
    title: 'Billing',
    subtitle: 'Recharge & bills',
    message: 'I need help with my bill and recharge',
  },
];

function FormattedText({ text }) {
  if (!text) return null;
  const lines = String(text).split('\n');
  return (
    <div className="bubble-body-content">
      {lines.map((line, idx) => {
        if (!line.trim()) return <div key={idx} style={{ height: 4 }} />;
        const parts = line.split(/(\*\*.*?\*\*)/g);
        const rendered = parts.map((part, pIdx) => {
          if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
            return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
          }
          return part;
        });
        const isBullet = line.trim().startsWith('•') || line.trim().startsWith('-') || line.trim().startsWith('* ');
        return (
          <div key={idx} className={isBullet ? 'chat-bullet-line' : 'chat-text-line'}>
            {rendered}
          </div>
        );
      })}
    </div>
  );
}

const WELCOME_MESSAGE = {
  role: 'assistant',
  text: `Hello! 👋\nI'm your TelConnect AI Assistant.\n\nHow can I help you today?\n\n• Internet issues\n• Billing queries\n• Ticket status\n• Technical support`,
  meta: {
    path: 'greeting',
    source: 'welcome',
    suggestions: ['Check ticket status', 'Report internet outage', 'Run line diagnostic', 'Billing query'],
  },
};

export default function Chat() {
  const nav = useNavigate();
  const u = user();
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [busy, setBusy] = useState(false);
  const [selectedLang, setSelectedLang] = useState('auto');
  const [notices, setNotices] = useState([]);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState(null);
  const [chatSessionId, setChatSessionId] = useState(() => (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : String(Date.now())));
  const scrollRef = useRef(null);

  useEffect(() => {
    api.get('/api/chat/history').then((h) => {
      if (h && h.length > 0) {
        setMessages(h.map((m) => ({ role: m.role, text: m.text, meta: m.meta })));
      } else {
        setMessages([WELCOME_MESSAGE]);
      }
    }).catch(() => {
      setMessages([WELCOME_MESSAGE]);
    });
    const loadNotices = () => api.get('/api/my/notifications').then(setNotices).catch(() => { });
    loadNotices();
    const id = setInterval(loadNotices, 20000);
    return () => clearInterval(id);
  }, []);

  const handleNewChat = async () => {
    const hasUserMessages = messages.some((m) => m.role === 'user');
    if (hasUserMessages) {
      const confirmReset = window.confirm('Start a new conversation? This will clear the current chat history.');
      if (!confirmReset) return;
    }

    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setSpeakingIdx(null);
    setText('');
    setBusy(false);
    setChatSessionId(typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : String(Date.now()));

    try {
      await api.post('/api/chat/clear', {});
    } catch {
      // ignore clear network errors
    }

    setMessages([WELCOME_MESSAGE]);
    setTimeout(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
      }
    }, 50);
  };

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, busy]);

  const sendText = async (msg) => {
    if (!msg.trim() || busy) return;
    setText('');
    setMessages((m) => [...m, { role: 'user', text: msg }]);
    setBusy(true);
    try {
      const payload = {
        text: msg,
        preferred_language: selectedLang !== 'auto' ? selectedLang : undefined,
      };
      const res = await api.post('/api/chat', payload);
      setMessages((m) => [...m, { role: 'assistant', text: res.reply, meta: res.meta }]);
    } catch (ex) {
      setMessages((m) => [
        ...m,
        { role: 'assistant', text: `Something went wrong (${ex.message}). Please try again.` },
      ]);
    }
    setBusy(false);
  };

  const send = (e) => {
    e.preventDefault();
    sendText(text.trim());
  };

  // ---------- Text-to-Speech (TTS) ----------
  const speakMessage = (msgText, idx, lang) => {
    if (!window.speechSynthesis) return;
    if (speakingIdx === idx) {
      window.speechSynthesis.cancel();
      setSpeakingIdx(null);
      return;
    }
    window.speechSynthesis.cancel();
    const cleanText = msgText.replace(/[*_#`◈]/g, '');
    const utter = new SpeechSynthesisUtterance(cleanText);
    utter.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
    utter.rate = 1.0;
    utter.onend = () => setSpeakingIdx(null);
    utter.onerror = () => setSpeakingIdx(null);
    setSpeakingIdx(idx);
    window.speechSynthesis.speak(utter);
  };

  const last = messages[messages.length - 1];
  const expectConfirm = !busy && last?.role === 'assistant' && last?.meta?.expect === 'confirmation';
  const expectRating = !busy && last?.role === 'assistant' && last?.meta?.expect === 'rating';
  const suggestions =
    !busy &&
      last?.role === 'assistant' &&
      last?.meta?.suggestions?.length > 0 &&
      !expectConfirm &&
      !expectRating
      ? last.meta.suggestions
      : [];
  const unread = notices.length;

  const areaNotice = notices.find(
    (n) => n.incident_id && n.match_reason?.includes('region')
  );

  const firstName = u?.name?.split(' ')[0] || 'there';

  return (
    <div className="chat-wrap customer-chat-page">
      <header className="chat-head customer-chat-head">
        <div className="customer-brand">
          <div className="customer-brand-icon">
            <div className="sigbars p4" aria-hidden="true">
              <i />
              <i />
              <i />
              <i />
            </div>
          </div>

          <div className="customer-brand-copy">
            <div className="customer-title">TelConnect</div>
            <div className="customer-subtitle">AI Customer Support</div>
          </div>

          <div className="customer-profile">
            <div className="customer-name">{u?.name}</div>
            <div className="small muted">
              {u?.region} · {u?.service_type}
            </div>
          </div>
        </div>

        <div className="customer-head-actions">
          {/* Language Selector */}
          <div className="lang-pill-selector" title="Choose language for AI Assistant">
            {LANGUAGES.map((l) => (
              <button
                key={l.id}
                type="button"
                className={`lang-pill ${selectedLang === l.id ? 'active' : ''}`}
                onClick={() => setSelectedLang(l.id)}
              >
                {l.label}
              </button>
            ))}
          </div>

          <button
            className="btn ghost sm bell"
            onClick={() => setDrawerOpen(!drawerOpen)}
            aria-label={`Notifications (${unread})`}
            title="Notifications"
          >
            🔔
            {unread > 0 && <span className="dot" />}
          </button>

          <button
            className="btn ghost sm"
            onClick={() => {
              clearSession();
              nav('/');
            }}
          >
            Sign out
          </button>

          {drawerOpen && (
            <div className="notif-drawer">
              <h3 style={{ marginBottom: 6 }}>Your updates</h3>

              {!notices.length && (
                <div className="small muted">No notifications yet.</div>
              )}

              {notices.map((n) => (
                <div className="notif-item" key={n.notification_id}>
                  {n.draft_text}
                  <div className="mono muted" style={{ fontSize: 10, marginTop: 4 }}>
                    {new Date(n.created_at).toLocaleString()} · {n.match_reason}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </header>

      <main className="customer-main customer-two-column">
        <div className="customer-left-column">
          <section className="customer-left-panel">
            <section className="customer-welcome">
              <div>
                <h1>Hello, {firstName} 👋</h1>
                <p>How can we help you today?</p>
              </div>

              <div className="customer-location">📍 {u?.region || 'Your area'}</div>
            </section>

            <div className="customer-left-content">
              <section
                className={`customer-service-status ${areaNotice ? 'has-incident' : ''}`}
              >
                <div className="customer-status-icon">{areaNotice ? '🔴' : '🟢'}</div>

                <div className="customer-status-content">
                  <strong>
                    {areaNotice
                      ? 'Service issue detected in your area'
                      : 'Your service is working normally'}
                  </strong>
                  <p>
                    {areaNotice
                      ? areaNotice.draft_text
                      : 'No known outage has been detected in your area.'}
                  </p>
                </div>

                <span className={`badge ${areaNotice ? 'red' : 'teal'}`}>
                  {areaNotice ? 'Attention' : 'Operational'}
                </span>
              </section>

              <section className="customer-quick-help">
                <div className="section-heading">
                  <div>
                    <h2>Quick Actions</h2>
                    <p>Tap an action to execute diagnostic or request support.</p>
                  </div>
                </div>

                <div className="customer-actions">
                  {CUSTOMER_ACTIONS.map((action) => (
                    <button
                      key={action.title}
                      className="customer-action"
                      onClick={() => sendText(action.message)}
                      disabled={busy}
                    >
                      <span className="customer-action-icon">{action.icon}</span>
                      <span className="customer-action-title">{action.title}</span>
                      <span className="customer-action-subtitle">{action.subtitle}</span>
                      <span className="customer-action-arrow">→</span>
                    </button>
                  ))}
                </div>
              </section>

              <div className="customer-profile-card">
                <div className="profile-card-icon">📍</div>
                <div>
                  <strong>{u?.region || 'Your area'}</strong>
                  <p>{u?.service_type || 'Telecom service'}</p>
                </div>
              </div>

              <button
                className="customer-human-help"
                onClick={() => sendText('Connect me to a support executive')}
                disabled={busy}
              >
                <span>👤</span>
                <span>
                  <strong>Need human assistance?</strong>
                  <small>Escalate ticket to live engineering support</small>
                </span>
                <b>→</b>
              </button>
            </div>
          </section>
        </div>

        <div className="customer-right-column">
          <section className="customer-right-panel">
            <section className="customer-ai-card">
              <div className="customer-ai-header">
                <div className="customer-ai-identity">
                  <div className="customer-ai-icon">🤖</div>
                  <div>
                    <h2>TelConnect AI Assistant</h2>
                    <p>Hugging Face DistilBERT & LangGraph Autonomous Engine</p>
                  </div>
                </div>

                <div className="customer-ai-header-actions">
                  <button
                    type="button"
                    className="new-chat-btn"
                    onClick={handleNewChat}
                    title="Start New Conversation"
                    aria-label="Start New Conversation"
                  >
                    <span className="new-chat-icon" aria-hidden="true">
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                      </svg>
                    </span>
                    <span>New Chat</span>
                  </button>

                  <div className="customer-ai-online">
                    <span />
                    Online
                  </div>
                </div>
              </div>

              <div className="chat-scroll customer-chat-scroll" ref={scrollRef}>
                {!messages.length && (
                  <div className="customer-empty-chat">
                    <div className="customer-empty-icon">🤖</div>
                    <h3>Hi {firstName}!</h3>
                    <p>
                      I can troubleshoot network speed, test line latency, diagnose router issues, track tickets, or answer billing queries.
                    </p>
                    <div className="customer-language-note">
                      English · हिन्दी (Hindi)
                    </div>
                  </div>
                )}

                {messages.map((m, i) => (
                  <div key={i} className={`bubble ${m.role === 'user' ? 'user' : 'bot'}`}>
                    {m.role === 'assistant' && (
                      <div className="bot-bubble-head">
                        <span className="customer-message-label">🤖 AI Support</span>
                        <button
                          type="button"
                          className={`tts-btn ${speakingIdx === i ? 'speaking' : ''}`}
                          onClick={() => speakMessage(m.text, i, m.meta?.language)}
                          title="Read aloud"
                          aria-label="Read aloud"
                        >
                          {speakingIdx === i ? '⏹ Stop' : '🔊 Listen'}
                        </button>
                      </div>
                    )}

                    <div className="bubble-body">
                      <FormattedText text={m.text} />
                    </div>

                    {/* Dynamic Diagnostic Card */}
                    {m.meta?.diagnostic && (
                      <div className="diagnostic-card">
                        <div className="diag-header">
                          <span className="diag-title">⚡ Line Diagnostic Result</span>
                          <span
                            className={`diag-badge ${m.meta.diagnostic.status === 'healthy' ? 'good' : 'warning'
                              }`}
                          >
                            {m.meta.diagnostic.status?.toUpperCase()}
                          </span>
                        </div>
                        <div className="diag-grid">
                          <div className="diag-stat">
                            <span className="stat-lbl">Download</span>
                            <span className="stat-val">{m.meta.diagnostic.download_mbps} <small>Mbps</small></span>
                          </div>
                          <div className="diag-stat">
                            <span className="stat-lbl">Upload</span>
                            <span className="stat-val">{m.meta.diagnostic.upload_mbps} <small>Mbps</small></span>
                          </div>
                          <div className="diag-stat">
                            <span className="stat-lbl">Latency</span>
                            <span className="stat-val">{m.meta.diagnostic.ping_ms} <small>ms</small></span>
                          </div>
                          <div className="diag-stat">
                            <span className="stat-lbl">Packet Loss</span>
                            <span className="stat-val">{m.meta.diagnostic.packet_loss_pct}%</span>
                          </div>
                        </div>
                        <div className="diag-summary small muted">
                          {m.meta.diagnostic.summary}
                        </div>
                      </div>
                    )}

                    {m.meta?.path && PATH_LABELS[m.meta.path] && (
                      <span className="tag">
                        ◈ {PATH_LABELS[m.meta.path]}
                        {m.meta.source ? ` · ${m.meta.source}` : ''}
                      </span>
                    )}
                  </div>
                ))}

                {expectConfirm && (
                  <div className="quick-replies customer-confirm">
                    <button className="btn sm" onClick={() => sendText('yes')}>
                      Yes, confirm ✓
                    </button>
                    <button className="btn ghost sm" onClick={() => sendText('no')}>
                      No
                    </button>
                  </div>
                )}

                {expectRating && (
                  <div className="customer-rating">
                    <div className="small muted">How would you rate the resolution?</div>
                    <div className="stars" role="group" aria-label="Rate the resolution 1 to 5">
                      {[1, 2, 3, 4, 5].map((n) => (
                        <button
                          key={n}
                          onClick={() => sendText(String(n))}
                          aria-label={`${n} stars`}
                        >
                          ★
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {suggestions.length > 0 && (
                  <div
                    className="quick-replies"
                    style={{ flexWrap: 'wrap', gap: 8, marginTop: 4 }}
                  >
                    {suggestions.map((s, idx) => (
                      <button
                        key={idx}
                        className="btn ghost sm"
                        style={{
                          borderRadius: 20,
                          fontSize: 12,
                          padding: '5px 12px',
                        }}
                        onClick={() => sendText(s)}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}

                {busy && (
                  <div className="bubble bot customer-thinking">
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-dot" />
                    <span className="thinking-text">
                      Executing LangGraph multi-task workflow…
                    </span>
                  </div>
                )}
              </div>

              <form className="chat-input customer-chat-input" onSubmit={send}>
                <input
                  className="field"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Ask in English or हिन्दी… (e.g. “मेरा इंटरनेट नहीं चल रहा” or “run speed test”)"
                  aria-label="Message"
                />

                <button
                  className="btn customer-send"
                  disabled={busy || !text.trim()}
                >
                  Send →
                </button>
              </form>

              <div className="customer-input-hint">
                💡 Type in English or हिन्दी. AI diagnoses issues and automates tickets.
              </div>
            </section>
          </section>
        </div>
      </main>
    </div>
  );
}
