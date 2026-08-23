# Fleet board — Telecom Complaint Intelligence

## Decisions taken
- SQLite over Postgres, TF-IDF retrieval over ChromaDB+embeddings, stdlib crypto over bcrypt/JWT libs,
  thread loop over APScheduler, React over Streamlit. Rationale in docs/PLAN.md.
- Groq is the only external API; every Groq call has a deterministic offline fallback.
- PII policy: contact columns never mapped; phones/emails redacted from text at ETL.
  Proactive notifications target registered accounts (region+service match), so nothing breaks.

## Closed findings (JD plan review, 2026-08-19)
1. SQLite concurrency -> WAL + busy_timeout=5000 + per-thread connections. Proof: live scheduler + upload concurrent, no lock errors.
2. Tautological F1 gate -> augmented corpus with held-out 25% stratified split; gate asserts macro-F1 >= 0.80 on held-out only.
3. Frontend back-loaded -> UI built immediately after backend core; full browser QA run.
4. Hinglish vs English KB -> HINGLISH_MAP normalisation applied at ingest AND query; verified in browser.
5. PII vs notifications contradiction -> resolved by policy above.
6. Status lookup join -> chat-registered complaints carry customer_id; verified in tests + browser.
7. Root-cause confidence -> stored + asserted in tests.
8. scrypt/LibreSSL -> pbkdf2 fallback; --reload double-scheduler -> documented, run.sh runs without --reload.

## QA findings fixed during browser pass
- ETL dedupe collapsed injected spike -> dedupe keys on source ticket ID when present.
- Heatmap 'high' given to top percentile of a flat pack -> now requires >= 1.6x median deviation.
- 35300% spike display -> formatted as Nx multiplier above 500%.
- "register a complaint" follow-up lost original issue context -> history lookback (regression test added).

## Open / owed
- Real Kaggle Complaints.csv never measured against classifier (only synthetic corpus). Owed: run once with the real file via the upload UI.
- Groq live path untested (no key on this machine); fallback path fully tested.

## v6 upgrade (2026-08-20, PRD v6 "Professional + Whisper")
- Lifecycle statuses + immutable complaint_status_history; resolutions, feedback,
  conversations, audit_logs tables added. DB rebuilt (no migration — demo DB is regenerable).
- Assistant rewritten: intent router (10 intents), registration verification step,
  confirm-to-close loop, feedback ratings, escalate/reopen, billing queries. LLM never mutates
  state; all actions via deterministic functions (PRD 5.3).
- Whisper voice input: POST /api/chat/voice -> Groq whisper-large-v3-turbo; 503 with clear
  message when no key. Frontend MediaRecorder mic button.
- SLA deadlines from complaint timestamp (P1 4h/P2 8h/P3 24h/P4 72h); breaches on dashboard.
- Ticket management endpoints: PATCH complaint (assign/status), propose-resolution, history,
  audit log, feedback list, teams. Transactional customer notifications auto-approved.
- Frontend: animated landing page at /, login moved to /login, chat quick-reply chips +
  star rating + notification bell + mic, queue manage panel with history timeline, audit page,
  v6 dashboard cards. Animations respect prefers-reduced-motion.
- QA findings fixed during v6 pass: ticket summaries no longer embed status text (contradicted
  live status); SLA computed from ingest time -> complaint time; explicit register overrides
  known-fix suggestion (kept from v5 with new KB).
- 35 pytest e2e green incl. new lifecycle/audit/SLA/voice tests. Full browser QA of both roles.
