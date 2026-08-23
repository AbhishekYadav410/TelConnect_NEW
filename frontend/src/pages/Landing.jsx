import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const FEATURES = [
  ['🗺', 'Live network heatmap', 'Complaint density per region against its own rolling baseline — an outage turns red before the call-center floods.'],
  ['⚡', 'Automatic spike detection', 'A background engine watches every region + service. Breach the baseline and an incident opens itself, alerting admins in real time.'],
  ['🔎', 'Evidence-backed root cause', 'Not "there is an outage" but why — likely cause, confidence %, and checkable evidence bullets grounded in computed signals.'],
  ['💬', 'AI resolution assistant', 'Customers talk naturally — English or Hindi, typed or spoken. Known fixes resolve in chat; real issues become verified tickets.'],
  ['🔁', 'Closed-loop lifecycle', 'Nothing closes silently. Every fix waits for the customer to confirm; rejections reopen and escalate with full history preserved.'],
  ['📣', 'Proactive notifications', 'Affected customers are matched to incidents and informed before they call — with human approval on every mass send.'],
];

const JOURNEY = [
  ['Report', 'Customer describes the issue naturally — voice or text. Intent routing + verification, no forms.'],
  ['Diagnose', 'Incident check, RAG knowledge retrieval, ML classification, priority + SLA in milliseconds.'],
  ['Resolve', 'Known fix guided in chat, or a tracked ticket with live status the customer can always see.'],
  ['Confirm', 'The customer verifies the fix. Yes closes it. No reopens and escalates. The loop always closes.'],
];

const STATS = [
  [1276, 'complaints triaged in the live demo'],
  [2, 'incidents auto-detected with distinct root causes'],
  [92, '% top root-cause confidence, evidence-backed'],
  [0, '₹ infrastructure cost — 100% free tier'],
];

function CountUp({ target, active }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!active) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { setVal(target); return; }
    const t0 = performance.now();
    let raf;
    const tick = (t) => {
      const p = Math.min((t - t0) / 1400, 1);
      setVal(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, target]);
  return <>{val.toLocaleString()}</>;
}

export default function Landing() {
  const nav = useNavigate();
  const [statsActive, setStatsActive] = useState(false);
  const statsRef = useRef(null);

  useEffect(() => {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          if (e.target === statsRef.current) setStatsActive(true);
        }
      });
    }, { threshold: 0.18 });
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);

  return (
    <div className="landing">
      <nav className="land-nav">
        <div className="land-brand">
          <span className="sigbars p4" aria-hidden="true"><i /><i /><i /><i /></span>
          TelConnect
        </div>
        <button className="btn ghost sm" onClick={() => nav('/login')}>Sign in</button>
      </nav>

      {/* ---------- hero: radar sweep over a live complaint map ---------- */}
      <header className="hero">
        <div className="radar" aria-hidden="true">
          <div className="radar-ring r1" /><div className="radar-ring r2" /><div className="radar-ring r3" />
          <div className="radar-sweep" />
          <span className="ping p-red" style={{ top: '38%', left: '56%' }} />
          <span className="ping p-amber" style={{ top: '55%', left: '40%' }} />
          <span className="ping p-teal" style={{ top: '30%', left: '35%' }} />
          <span className="ping p-teal d2" style={{ top: '62%', left: '62%' }} />
          <span className="ping p-teal d3" style={{ top: '46%', left: '70%' }} />
        </div>
        <div className="hero-copy">
          <p className="eyebrow rise">Telecom Complaint Intelligence &amp; Automated Resolution</p>
          <h1 className="rise d1">See the outage<br />before the <em>200th</em> complaint.</h1>
          <p className="hero-sub rise d2">
            An AI platform that understands every complaint, resolves what it can in chat,
            tracks what it can't as live tickets — and watches the whole network for
            mass incidents with evidence-backed root causes.
          </p>
          <div className="hero-cta rise d3">
            <button className="btn lg" onClick={() => nav('/login')}>Launch the platform →</button>
            <button className="btn ghost lg" onClick={() =>
              document.getElementById('how')?.scrollIntoView({ behavior: 'smooth' })}>
              How it works
            </button>
          </div>
          <p className="hero-foot rise d4">
            Groq LLM · scikit-learn ML · RAG knowledge base · runs 100% on free tier
          </p>
        </div>
      </header>

      {/* ---------- stats ---------- */}
      <section className="land-stats reveal" ref={statsRef}>
        {STATS.map(([n, label], i) => (
          <div key={i} className="land-stat">
            <div className="land-stat-num"><CountUp target={n} active={statsActive} />{label.startsWith('%') ? '' : ''}</div>
            <div className="land-stat-label">{label}</div>
          </div>
        ))}
      </section>

      {/* ---------- journey ---------- */}
      <section className="land-section" id="how">
        <h2 className="reveal">One loop, from complaint to confirmed fix</h2>
        <div className="journey">
          {JOURNEY.map(([title, body], i) => (
            <div key={title} className="journey-step reveal" style={{ transitionDelay: `${i * 120}ms` }}>
              <div className="journey-dot">{i + 1}</div>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- features ---------- */}
      <section className="land-section">
        <h2 className="reveal">Two surfaces. One source of truth.</h2>
        <p className="land-section-sub reveal">
          Customers get a single conversational assistant. Operators get a full control plane.
          Both read and write the same live database — a real closed loop, not two demos.
        </p>
        <div className="feature-grid">
          {FEATURES.map(([icon, title, body], i) => (
            <div key={title} className="feature-card reveal" style={{ transitionDelay: `${(i % 3) * 100}ms` }}>
              <div className="feature-icon" aria-hidden="true">{icon}</div>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------- final CTA ---------- */}
      <section className="land-final reveal">
        <h2>Watch it catch the Raj Nagar outage.</h2>
        <p>The live demo ships with 1,276 complaints, a broadband outage in progress and a congestion
          cluster building — log in and watch the platform find both.</p>
        <button className="btn lg" onClick={() => nav('/login')}>Launch the platform →</button>
        <p className="small muted" style={{ marginTop: 14 }}>
          admin@telecom.com / admin123 · rohan@example.com / customer123
        </p>
      </section>

      <footer className="land-footer">
        Cognizant Hackathon · Use Case 13 · FastAPI + React + Groq · every component free &amp; open source
      </footer>
    </div>
  );
}
