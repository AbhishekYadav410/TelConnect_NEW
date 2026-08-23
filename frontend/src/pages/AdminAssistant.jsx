import React, { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';

const SUGGESTED_PROMPTS = [
  {
    icon: '🚨',
    title: 'Immediate Attention',
    query: 'Which complaints need immediate attention?',
  },
  {
    icon: '⚠️',
    title: 'Escalation Risk',
    query: 'Which complaints have the highest escalation risk?',
  },
  {
    icon: '📊',
    title: 'Top Categories',
    query: 'What are the top complaint categories?',
  },
  {
    icon: '📈',
    title: 'Increasing Volume',
    query: 'Why are complaints increasing in this region?',
  },
  {
    icon: '📡',
    title: 'Incident Status',
    query: 'What is the current incident status?',
  },
  {
    icon: '🔍',
    title: 'Likely Root Cause',
    query: 'What is the likely root cause?',
  },
  {
    icon: '🛠️',
    title: 'Action & SOPs',
    query: 'What action should we take?',
  },
  {
    icon: '📋',
    title: 'Daily Summary',
    query: "Summarize today's complaints.",
  },
];

function FormattedContent({ text }) {
  if (!text) return null;
  const lines = String(text).split('\n');

  return (
    <div className="admin-assistant-body">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} style={{ height: 6 }} />;

        // Header ###
        if (trimmed.startsWith('### ')) {
          return (
            <h4 key={idx} style={{ margin: '10px 0 6px', color: 'var(--signal)', fontSize: '14.5px', fontWeight: 600 }}>
              {trimmed.slice(4)}
            </h4>
          );
        }
        if (trimmed.startsWith('#### ')) {
          return (
            <h5 key={idx} style={{ margin: '8px 0 4px', color: 'var(--amber)', fontSize: '13.5px', fontWeight: 600 }}>
              {trimmed.slice(5)}
            </h5>
          );
        }

        // Bold formatting parser
        const parts = line.split(/(\*\*.*?\*\*|`.*?`)/g);
        const rendered = parts.map((part, pIdx) => {
          if (part.startsWith('**') && part.endsWith('**') && part.length >= 4) {
            return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
          }
          if (part.startsWith('`') && part.endsWith('`') && part.length >= 2) {
            return (
              <code
                key={pIdx}
                style={{
                  fontFamily: 'var(--mono)',
                  fontSize: '12px',
                  background: 'rgba(255,255,255,0.06)',
                  padding: '2px 5px',
                  borderRadius: 4,
                  color: 'var(--signal)',
                }}
              >
                {part.slice(1, -1)}
              </code>
            );
          }
          return part;
        });

        const isBullet = trimmed.startsWith('•') || trimmed.startsWith('-') || /^\d+\.\s/.test(trimmed);
        const isSubBullet = line.startsWith('   •') || line.startsWith('  -');

        return (
          <div
            key={idx}
            style={{
              paddingLeft: isSubBullet ? 18 : isBullet ? 6 : 0,
              margin: '3px 0',
              lineHeight: 1.5,
              fontSize: '13.5px',
            }}
          >
            {rendered}
          </div>
        );
      })}
    </div>
  );
}

export default function AdminAssistant() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState({});
  const scrollRef = useRef(null);

  const loadHistory = async () => {
    try {
      const history = await api.get('/api/admin/assistant/history');
      if (Array.isArray(history)) {
        setMessages(history.map((m) => ({ role: m.role, text: m.text, meta: m.meta })));
      }
    } catch {
      /* Keep existing state */
    }
  };

  useEffect(() => {
    api.get('/api/health').then(setHealth).catch(() => {});
    loadHistory();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, busy]);

  const sendQuery = async (queryText) => {
    const q = (queryText || input).trim();
    if (!q || busy) return;
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: q }]);
    setBusy(true);

    try {
      const res = await api.post('/api/admin/assistant/chat', { text: q });
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: res.reply,
          meta: res.meta,
        },
      ]);
    } catch (ex) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `### ❌ Request Failed\n\nCould not process query: ${ex.message}. Please check backend logs.`,
          meta: { error: true },
        },
      ]);
    } finally {
      setBusy(false);
    }
  };

  const handleFormSubmit = (e) => {
    e.preventDefault();
    sendQuery();
  };

  const clearChat = async () => {
    if (confirm('Clear assistant conversation history?')) {
      try {
        await api.post('/api/admin/assistant/clear', {});
        setMessages([]);
      } catch (ex) {
        alert(ex.message);
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 82px)' }}>
      {/* Page Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div>
          <h2 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>🤖</span> TelConnect AI Assistant
          </h2>
          <p className="page-sub" style={{ margin: '2px 0 0' }}>
            Decision support for complaints, incidents, priorities, escalation risks, and ChromaDB SOP recommendations.
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="badge grey" style={{ fontSize: '11px' }}>
            {health.groq_live ? '⚡ Groq LLM active' : 'Offline fallback active'}
          </span>
          <span className="badge teal" style={{ fontSize: '11px' }}>
            📚 ChromaDB RAG ready
          </span>
          {messages.length > 0 && (
            <button className="btn ghost sm" onClick={clearChat} style={{ fontSize: '11.5px', padding: '4px 8px' }}>
              Clear history
            </button>
          )}
        </div>
      </div>

      {/* Suggested Prompts Shelf */}
      <div style={{ marginBottom: 12 }}>
        <div className="small muted" style={{ marginBottom: 6, fontWeight: 500 }}>
          Suggested Operational Queries:
        </div>
        <div
          style={{
            display: 'flex',
            gap: 6,
            overflowX: 'auto',
            paddingBottom: 4,
            scrollbarWidth: 'thin',
          }}
        >
          {SUGGESTED_PROMPTS.map((item) => (
            <button
              key={item.title}
              className="btn ghost sm"
              onClick={() => sendQuery(item.query)}
              disabled={busy}
              style={{
                fontSize: '12px',
                padding: '5px 10px',
                whiteSpace: 'nowrap',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
                borderRadius: '16px',
                border: '1px solid var(--line)',
                background: 'var(--panel)',
              }}
            >
              <span>{item.icon}</span>
              <span>{item.query}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Conversation Scroll Container */}
      <div
        ref={scrollRef}
        className="card"
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 16,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          marginBottom: 12,
          background: 'var(--panel)',
        }}
      >
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--muted)' }}>
            <div style={{ fontSize: '42px', marginBottom: 10 }}>🤖</div>
            <h3 style={{ color: 'var(--text)', marginBottom: 6 }}>TelConnect Operations AI Assistant</h3>
            <p style={{ maxWidth: 540, margin: '0 auto 20px', fontSize: '13.5px', lineHeight: 1.5 }}>
              Ask questions about real-time complaint volumes, SLA breaches, escalation risks, active incident root causes, or standard operating procedures (SOPs).
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, flexWrap: 'wrap' }}>
              {SUGGESTED_PROMPTS.slice(0, 4).map((p) => (
                <button
                  key={p.title}
                  className="btn ghost sm"
                  onClick={() => sendQuery(p.query)}
                  style={{ borderRadius: 14 }}
                >
                  {p.icon} {p.title}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, idx) => {
          const isUser = m.role === 'user';
          return (
            <div
              key={idx}
              className={`bubble ${isUser ? 'user' : 'bot'}`}
              style={{
                maxWidth: isUser ? '75%' : '88%',
                borderRadius: 10,
                padding: '12px 16px',
                boxShadow: 'var(--card-shadow)',
              }}
            >
              {!isUser && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    marginBottom: 6,
                    paddingBottom: 4,
                    borderBottom: '1px solid var(--line)',
                  }}
                >
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--signal)' }}>
                    🤖 TelConnect Intelligence
                  </span>
                  {m.meta?.source && (
                    <span className="badge grey" style={{ fontSize: '10px', marginLeft: 'auto' }}>
                      {m.meta.source === 'groq_live' ? '⚡ Groq LLM' : '📊 Grounded DB + RAG'}
                    </span>
                  )}
                  {m.meta?.docs?.length > 0 && (
                    <span className="badge teal" style={{ fontSize: '10px' }}>
                      📚 {m.meta.docs.length} SOPs cited
                    </span>
                  )}
                </div>
              )}

              <FormattedContent text={m.text} />

              <div className="tag" style={{ marginTop: 8, fontSize: '10.5px', opacity: 0.7 }}>
                {isUser ? 'Admin' : 'AI Assistant'}
              </div>
            </div>
          );
        })}

        {busy && (
          <div
            className="bubble bot"
            style={{
              maxWidth: '60%',
              borderRadius: 10,
              padding: '12px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <span className="live-dot" />
            <span style={{ fontSize: '13px', color: 'var(--muted)' }}>
              Analyzing live complaints &amp; ChromaDB knowledge base…
            </span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form onSubmit={handleFormSubmit} className="chat-input" style={{ padding: 0, border: 'none' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about complaints, incidents, priorities, escalation risks, or resolution SOPs..."
          disabled={busy}
          style={{
            flex: 1,
            padding: '12px 16px',
            borderRadius: 8,
            border: '1px solid var(--line)',
            background: 'var(--field-bg)',
            color: 'var(--text)',
            fontSize: '14px',
          }}
        />
        <button
          type="submit"
          className="btn"
          disabled={busy || !input.trim()}
          style={{
            padding: '0 24px',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <span>Ask</span>
          <span>→</span>
        </button>
      </form>
    </div>
  );
}
