# PRODUCT REQUIREMENTS DOCUMENT

# Telecom Complaint Intelligence & Automated Resolution Assistant
**Professional, admin-oriented product specification**  
*Cognizant Hackathon • Use Case 13*

---

## Document Specification

| Document | Specification |
| :--- | :--- |
| **Version** | 10.0 — Admin-Oriented Multi-Task Agent & Text-Only Intelligence PRD |
| **Product Type** | AI-powered telecom complaint intelligence and automated resolution platform |
| **Primary User** | Support / Operations Admin teams |
| **Secondary User** | Telecom customers |
| **Admin Assistant UI** | Admin Operations Dashboard + Admin AI Assistant |
| **Agent Orchestration** | LangGraph Multi-Task StateGraph (customer workflow + admin operations agent) |
| **Multilingual Engine** | Hugging Face DistilBERT (multilingual-cased) + Groq translation + rule fallback |
| **Primary AI Provider** | Groq API (Llama models) with deterministic offline fallbacks |
| **Customer Interaction** | Text-based conversational assistant |
| **Core Data Store** | SQLite (tci.db with WAL mode, foreign keys, immutable audit logs) |
| **Knowledge Store** | ChromaDB persistent vector store + Sentence Transformers (all-MiniLM-L6-v2) |
| **Geolocation Engine** | Geoapify Geocoding API with caching and India boundary validation |
| **Core Backend** | Python + FastAPI + Uvicorn |
| **UI** | Admin Operations Dashboard + Admin AI Assistant + Customer Assistant (40/60 Split) + Theme Engine (Dark/Light) |

### Product Vision
Give telecom operations teams a single intelligence and control plane to monitor complaints, manage tickets, investigate incidents, use AI-assisted recommendations, detect service-wide patterns, approve proactive actions, and verify that customer-facing resolution outcomes are achieved.

The customer assistant remains the connected service channel, while the product is positioned around the admin control plane: operational visibility, queue management, incident intelligence, auditability and AI decision support.

---

## 1. Product Overview

TelConnect is an admin-oriented telecom complaint intelligence and resolution platform. The Admin Dashboard is the primary operational control plane used to manage the complaint lifecycle, investigate patterns, monitor service issues, update ticket states, manage incidents, evaluate AI recommendations and query operational intelligence.

The customer assistant is the connected text-based service channel: it captures complaints, diagnostics and customer confirmation while feeding authoritative operational data into the admin workflow.

### 1.1 Product Principles

- **Admin first:** The primary workflow starts with operational visibility and ends with a controlled, auditable action or verified outcome.
- **Operational control:** Admins manage queues, tickets, assignments, incidents, alerts, notifications and resolution actions from one dashboard.
- **AI-assisted decisions:** The Admin AI Assistant provides evidence, SOP knowledge, live database context and explainable recommendations; privileged actions remain backend-controlled.
- **Customer outcome:** Admin actions are measured by whether complaints are resolved, tracked and confirmed by the customer.
- **One source of truth:** Admin dashboard and customer assistant use the same backend and SQLite operational database.
- **Dynamic by design:** Runtime complaints, assignments and incidents are database-driven; seed CSV data is not the live source of truth.
- **Closed loop:** Resolution is not final until the customer confirms it; rejected fixes reopen or escalate.
- **Explainable and auditable:** Priority, escalation, root-cause and AI recommendations expose evidence, while privileged actions are logged.
- **Zero-cost and offline resilient:** Core ticket/status operations remain usable with deterministic fallbacks when external AI services are unavailable.

### 1.2 Problem Statement

Telecom operators receive large complaint volumes across network, broadband, billing and service issues. Manual triage, fragmented ticket handling and delayed outage recognition make it difficult for operations teams to understand what is happening, which customers are affected, what should be done next and whether the customer was actually helped.

---

## 2. Objectives

| Admin Objective | Expected Operational Outcome |
| :--- | :--- |
| **Operational overview** | Monitor complaint volume, open tickets, priorities, SLA risk, incidents and trends from one control plane. |
| **Queue & ticket efficiency** | Search, filter, assign, update, escalate and resolve complaints with full status history. |
| **Incident intelligence** | Detect spikes, link complaints to incidents and investigate service-wide impact. |
| **AI decision support** | Use the Admin AI Assistant with live DB snapshots, ChromaDB SOPs and explainable recommendations. |
| **Root-cause investigation** | Combine complaint patterns, geography, history and knowledge evidence into actionable hypotheses. |
| **Proactive operations** | Review and approve customer notifications for confirmed incidents and meaningful ticket events. |
| **Audit & governance** | Keep privileged actions, assignments, status changes and notification decisions traceable. |
| **Customer resolution outcome** | Ensure the operational workflow ultimately produces verified customer resolution or proper escalation. |
| **Customer-facing assistance** | Provide text chat, diagnostics, troubleshooting, ticket tracking and confirmation as the service channel. |

### 2.1 Success Criteria

- Admin can see complaint volume, priority, category, sentiment, escalation risk, geographic spikes, incidents and SLA information.
- Admin can assign, update, escalate and resolve tickets while preserving immutable status history.
- Admin can investigate a spike and obtain evidence-backed root-cause signals.
- Admin can use the Operations AI Assistant for complex operational queries without unrestricted database access.
- Customer outcome: every valid complaint has a persistent ticket record and can be confirmed, reopened or escalated.
- Resilience: ticket and status operations remain usable when Groq is unavailable.

### 2.2 Scope Boundaries

- MVP focuses on complaint intelligence, operational orchestration and resolution support; it does not directly control telecom network equipment.
- Real OSS/BSS integration is a future integration point; the hackathon uses simulated telemetry APIs and controlled data feeds.
- External SMS/push delivery is optional for MVP; in-app notifications demonstrate the workflow.
- The supplied complaint dataset is seed/demo data, not the live operational database.

---

## 3. Users & Roles

| Role | Needs | Key Capabilities |
| :--- | :--- | :--- |
| **Support Admin** | Operational control and fast resolution management. | Queue, assignment, priority, status, notes, resolution actions, SLA monitoring, escalation, audit. |
| **Network Operations** | Detect and investigate service-wide problems. | Heatmap, spikes, incident management, root-cause investigation, affected-customer analysis, broadcast approvals. |
| **Operations AI User** | Decision support for NOC/admin workflows. | Admin AI Assistant, prompt chips, live DB snapshots, ChromaDB SOP synthesis, classification explanations. |
| **Customer** | Fast help and transparent resolution status. | Text chat assistant, diagnostics, troubleshooting, ticket tracking, confirmation, reopen and escalation. |
| **System / AI** | Automated intelligence and controlled decision support. | LangGraph agents, ML scoring, spike detection, RAG retrieval, response generation, audit logging. |

### 3.1 Access Control

- Admins access operational complaint and incident data according to role.
- Customers access only their own profile, conversations, complaints, notifications and feedback.
- AI services never receive unrestricted database access; they call authorized backend functions.
- All privileged actions are recorded in the audit log.
- Admin AI recommendations remain subject to backend authorization and operational approval where required.

---

## 4. Admin Operational Complaint Lifecycle

| Step | Admin / System Action | Outcome |
| :---: | :--- | :--- |
| **1. Monitor** | Review dashboard, queue, alerts and complaint intelligence. | Operational picture established. |
| **2. Triage** | Inspect category, priority, sentiment, escalation risk and incident links. | Work prioritized. |
| **3. Investigate** | Use heatmap, spike detection, incident data and AI evidence. | Likely issue scope identified. |
| **4. Assign** | Route to Field Ops, RF Team, Billing, Support L2 or Network Ops. | Ownership established. |
| **5. Resolve** | Add notes, use approved SOP/RAG guidance and record resolution source. | Resolution attempt tracked. |
| **6. Verify** | Customer confirms or rejects the proposed resolution. | Closed-loop outcome captured. |
| **7. Escalate/Reopen** | Escalate or reopen when the issue is unresolved or returns. | No silent closure. |
| **8. Close** | Finalize only after confirmation and preserve complete history. | Auditable complaint lifecycle. |

### 4.1 Customer Service Channel

The customer assistant feeds the same operational lifecycle. Customer steps remain: Start → Verify → Diagnose → Resolve → Confirm → Ticket → Track → Escalate → Reopen → Close. Every status transition is persisted in SQLite with actor, timestamp and reason.

### 4.2 Complaint Status Model

`NEW` → `VERIFICATION_REQUIRED` → `VERIFIED` → `CLASSIFIED` → `DIAGNOSING` → `IN_PROGRESS` → `RESOLVED_PENDING_CONFIRMATION` → `CLOSED`  
Alternative paths: `WAITING_FOR_CUSTOMER`, `HUMAN_ESCALATION`, `REOPENED`.

---

## 5. AI Operations & Customer Assistants

### 5.1 Admin AI Assistant — Primary Decision Support

The Admin AI Assistant is a workflow-driven operations agent. It answers complex operational questions using live database snapshots and ChromaDB SOP knowledge, explains complaint classifications and priority factors, summarizes incidents, and supports NOC/admin decision-making. It does not directly mutate privileged state.

### 5.2 Admin Assistant Capabilities

- Queue and ticket summaries, priority and SLA explanations.
- Incident and spike investigation with affected-region/customer context.
- Root-cause evidence synthesis from structured patterns and approved knowledge.
- SOP retrieval and operational troubleshooting guidance.
- Status, assignment and escalation explanations from authoritative SQLite state.
- Prompt chips and guided operational queries for fast NOC/admin briefings.

### 5.3 Customer Assistant — Text Service Channel

The customer assistant handles `REPORT_COMPLAINT`, `DIAGNOSTIC`, `CHECK_STATUS`, `TROUBLESHOOT`, `KNOWN_INCIDENT`, `CONFIRM_RESOLUTION`, `REJECT_RESOLUTION`, `REOPEN_COMPLAINT`, `BILLING_QUERY`, `ESCALATE` and `GENERAL_QUERY` through the LangGraph customer workflow.

### 5.4 LangGraph Workflows

- **Admin workflow:** query → retrieve live DB context → retrieve SOP/knowledge → reason → explain recommendation → authorized action when permitted.
- **Customer workflow:** translate_input → route_intent → retrieve_context → execute_action → synthesize_response → translate_output.

---

## 6. Solution Architecture

| Layer | Components | Purpose |
| :--- | :--- | :--- |
| **Admin Layer** | React operations dashboard, Admin AI Assistant, Theme Engine | Primary control plane: queue, tickets, incidents, heatmap, analytics, alerts, notifications and audit. |
| **Customer Layer** | React 40/60 text chat, diagnostic cards | Complaint reporting, diagnostics, troubleshooting, tracking and confirmation. |
| **API Layer** | Python + FastAPI + Uvicorn + hashlib-based authentication | Central business logic, authorization and deterministic actions. |
| **AI Orchestration** | LangGraph Multi-Task StateGraph | Controls multi-turn state continuation and tool execution. |
| **Multilingual NLP** | Hugging Face DistilBERT (multilingual-cased) | Tokenization, Hinglish normalization and Devanagari validation. |
| **ML Intelligence** | scikit-learn (TF-IDF + Logistic Regression) + Multi-Factor Scoring | Classification, sentiment, urgency, escalation and priority scoring. |
| **Vector RAG** | ChromaDB + Sentence Transformers (all-MiniLM-L6-v2) | Grounded troubleshooting, FAQs, SOPs and approved resolved cases. |
| **Generative AI** | Groq API (Llama models) + offline fallbacks | Conversation, summaries, explanations and root-cause narrative. |
| **Geolocation** | Geoapify Geocoding API + cache | Location coordinates for Leaflet regional heatmap. |
| **Operational DB** | SQLite (tci.db with WAL mode) | Live complaints, users, status history, incidents, notifications and audit logs. |
| **Analytics / Detection** | Spike detection, heatmap, incident engine | Proactive operational intelligence. |

### 6.1 Data Flow

Admin/customer/API input → validation → complaint persistence → SQLite → incident/duplicate evaluation → resolution/ChromaDB RAG → ticket lifecycle → notification/analytics → feedback.

**Operational source of truth:** SQLite. **Knowledge retrieval:** ChromaDB. **Generation/reasoning:** Groq. The LLM cannot become the source of live ticket truth.

---

## 7. Admin Operations Dashboard

All useful admin-dashboard capabilities from the original concept are retained and organized into 16 operational modules.

| Dashboard Module | Features & Operational Capabilities |
| :--- | :--- |
| **1. Overview** | Total complaints, open tickets, resolved/closed tickets, high-priority complaints, SLA breaches, active incidents, complaint trends. |
| **2. Complaint Queue** | Search/filter by status, category, service, region, priority, sentiment, escalation risk, date and incident. |
| **3. Ticket Management** | View ticket detail, customer-safe summary, category, priority, AI analysis, incident link, status, SLA, assignment and history. |
| **4. Assignment & Escalation** | Assign to support team/person (Field Ops, RF Team, Billing, Support L2, Network Ops), mark waiting for customer. |
| **5. Resolution Management** | Add resolution notes, propose resolution, record resolution source, move to RESOLVED_PENDING_CONFIRMATION. |
| **6. Status Management** | NEW, IN_PROGRESS, WAITING_FOR_CUSTOMER, ESCALATED, RESOLVED_PENDING_CONFIRMATION, CLOSED, REOPENED. |
| **7. Complaint Intelligence** | Category distribution, sentiment, urgency, escalation risk, priority distribution and recurring issue analysis. |
| **8. Heatmap** | Leaflet geographic complaint density with filters and drill-down to underlying complaints (Red=Spike, Amber=Elevated, Teal=Normal). |
| **9. Spike Detection** | Rolling baseline comparison, abnormal complaint volume alerts and automatic incident creation. |
| **10. Root-Cause Investigator** | Likely cause, confidence bar (90%+), evidence signals (>=3 bullets), affected region/service and supporting complaint patterns. |
| **11. Incident Management** | Create/acknowledge/assign/update/resolve incidents; link complaints; inspect affected customers. |
| **12. Proactive Alerts** | Admin alert inbox for complaint spikes, SLA risks, active incidents and escalation risks with unread badges. |
| **13. Notification Center** | Draft, review and approve incident/customer notifications; view delivery/read state for in-app notifications. |
| **14. Executive Analytics** | Resolution rate, response time, escalation rate, SLA performance, category trends, duplicate complaints and customer feedback. |
| **15. Data Ingestion** | Admin-only 3-step CSV upload wizard with auto-schema detection, PII redaction and pipeline triggering. |
| **16. Operations AI Assistant** | LangGraph decision support agent answering complex operational queries with live DB snapshots and ChromaDB SOPs. |

### 7.1 Dashboard Principle

The dashboard helps an operator answer four questions quickly: **What is happening? Which customers are affected? What should we do? Has the customer actually been helped?**

---

## 8. Complaint Intelligence Pipeline

| Capability | Input | Output |
| :--- | :--- | :--- |
| **Text Classification** | Complaint text | Category/subcategory/service type (Macro-F1 >= 82.4%). |
| **Intent Detection** | Conversation message | Supported assistant intent (15+ categories). |
| **Entity Extraction** | Complaint text | Location, service, device, timing and issue details. |
| **Sentiment Analysis** | Complaint text/conversation | Positive/neutral/negative/critical signal. |
| **Urgency Detection** | Complaint + context | Urgency score/level (0.0 to 1.0). |
| **Escalation Risk** | Complaint + history + sentiment | Escalation probability/risk level (churn & TRAI threats). |
| **Priority Scoring** | Urgency + impact + risk + incident context | P1/P2/P3/P4 priority with contributing factor chips. |
| **Duplicate Detection** | New complaint + existing complaints/incidents | Similarity/link recommendation. |
| **Ticket Summary** | Full conversation/complaint | Concise agent-ready 1-sentence summary. |

### 8.1 Priority Example & Formula

$$\text{Priority} = \text{clamp}(0, 100, \, w_1 \cdot \text{Urgency} + w_2 \cdot \text{Sentiment} + w_3 \cdot \text{Escalation} + w_4 \cdot \text{Incident} + w_5 \cdot \text{Repeat})$$

- **P1 (Critical, 80-100):** SLA 2 Hours — High priority alert drafted; immediate queue banner.
- **P2 (High, 60-79):** SLA 6 Hours — Routed to Tier-2 specialist queue.
- **P3 (Medium, 35-59):** SLA 24 Hours — Standard operational queue.
- **P4 (Low, 0-34):** SLA 48 Hours — General queue.

The dashboard displays the major contributing factor chips rather than only a numeric score.

---

## 9. RAG-Based Automated Resolution

RAG is used to make the assistant useful for actual resolution rather than only classification.

### 9.1 Knowledge Base

- Telecom troubleshooting SOPs (broadband reset, ONT reconfiguration, APN settings, eSIM).
- FAQs and approved service guidance.
- Billing/service policies.
- Historical confirmed resolutions.
- Incident resolution notes and post-mortems.

### 9.2 Resolution Decision

| Condition | Assistant Behaviour |
| :--- | :--- |
| **Known incident exists** | Explain incident, provide available guidance and link complaint to incident where appropriate. |
| **Known low-risk issue + good RAG match** | Guide customer through safe step-by-step troubleshooting SOPs. |
| **Insufficient knowledge** | Ask clarification or escalate; do not hallucinate. |
| **Account-sensitive issue** | Use authenticated backend data or route to human support. |
| **Troubleshooting succeeds** | Ask customer to confirm resolution (Yes ✓). |
| **Customer rejects resolution** | Reopen/escalate and preserve the previous attempt. |

### 9.3 RAG Grounding Rule

Every troubleshooting response should be generated from retrieved approved knowledge. The assistant should not claim a cause, ETA, policy or fix that is not supported by the retrieved ChromaDB chunks or live SQLite backend state.

---

## 10. Dynamic Data & Complaint Lifecycle

The original dataset remains useful for model training/evaluation and demonstration, but runtime operation is database-driven.

| Data Source | Use |
| :--- | :--- |
| **Historical CSV / Demo data** | Model development, evaluation, historical analytics and seed records. |
| **Customer Assistant** | Real-time complaint creation and customer interactions. |
| **Admin Dashboard** | Status updates, assignments, resolution notes and incident actions. |
| **Dynamic Line Diagnostics** | Real-time simulated telemetry for line speed, latency, jitter and packet loss. |
| **Background Detection** | Complaint aggregation, spike detection and incident generation. |

### 10.1 Core Database Entities

| Entity | Purpose |
| :--- | :--- |
| **users** | Customer/admin identity and role. |
| **complaints** | Live complaint/ticket record with priority and SLA. |
| **complaint_status_history** | Immutable status transition history. |
| **chat_messages** | Conversation messages, detected intents and metadata. |
| **resolutions** | Troubleshooting/resolution attempts and confirmation. |
| **incidents** | Mass-service issue and root-cause information. |
| **notifications** | Ticket/incident notification records. |
| **kb_docs** | RAG source metadata. |
| **feedback** | Customer resolution rating (1-5 stars) and comments. |
| **audit_logs** | Operational/security trace. |

### 10.2 Required Complaint Fields
`complaint_id, customer_id, text, category, region, lat, long, service_type, sentiment, urgency, escalation_risk, priority_score, priority_label, sla_deadline, status, incident_id, assigned_to, ticket_summary, created_at`

---

## 11. Verification, Status & Resolution Management

This section addresses the most important gap in a basic chatbot: what happens after the customer reports the issue?

### 11.1 Customer Verification

- Authenticate customer before exposing personal complaint information.
- For a new complaint, summarize extracted details and ask for confirmation before ticket creation.
- For an existing complaint, identify it through the authenticated customer's account rather than trusting an arbitrary ticket ID.
- If required information is missing or inconsistent, ask targeted clarification questions.

### 11.2 Ticket Status Visibility

- Customer can ask for the status in natural language (English, Hindi, Hinglish).
- Assistant retrieves the current authoritative state directly from SQLite (`tci.db`).
- Response includes status, last update, assigned team, SLA countdown, and a short explanation.
- Status history is available for transparency in the customer drawer.

### 11.3 Resolution Confirmation

- AI/admin proposes a resolution → Ticket enters `RESOLVED_PENDING_CONFIRMATION`.
- Customer is explicitly asked whether the issue is fixed.
- **YES** → record confirmation → `CLOSED` → CSAT feedback.
- **NO** → `REOPENED` / `HUMAN_ESCALATION` → support queue.

### 11.4 Customer Feedback

After closure, the customer can provide a 1–5 star rating and optional comment. Feedback is stored against the complaint and surfaced in admin analytics for resolution-quality monitoring.

---

## 12. Mass Complaint Intelligence & Root-Cause Analysis

The operational intelligence features turn raw complaints into actionable network insights.

### 12.1 Complaint Spike Detection

- Group complaints by time window (6h rolling), region, category and service type.
- Compare current volume against a rolling 7-day historical baseline.
- Flag statistically abnormal increases (3x to 300x surge) according to configured thresholds.
- Create or update an incident record and link future matching complaints.

### 12.2 Geographic Heatmap

- Show complaint density by region via interactive Leaflet map.
- Filter by time, category, service and severity.
- Drill down from region → incident → complaint list.
- Highlight abnormal regions (Red surge circles) and active incidents.

### 12.3 AI Root-Cause Investigator

| Evidence Signal | Analytical Computation | Example |
| :--- | :--- | :--- |
| **Volume anomaly** | Multiplier vs historical rolling baseline. | Complaint count is 352x above baseline in Raj Nagar. |
| **Geographic concentration** | Percentage of complaints in target area. | 94.2% of complaints are from Ghaziabad circle. |
| **Service concentration** | Dominant service proportion. | 98.1% of complaints involve broadband/fiber. |
| **Time correlation** | Temporal cluster window onset. | Complaints started sharply within a 2-hour window. |
| **Historical similarity** | Cosine similarity to past incidents. | 92% match to INC-2025-0873 (Optical fiber cut). |
| **Knowledge evidence** | ChromaDB SOP corroboration. | Retrieved SOP supports physical line severance. |

**Root-cause output:** likely cause + confidence gauge (90%+) + evidence signals (>=3 checkable bullets) + affected scope + recommended action. AI output remains a hypothesis until confirmed by operations.

---

## 13. Proactive Customer Notification

| Trigger | Notification Content & Purpose |
| :--- | :--- |
| **Ticket created** | Complaint/ticket reference ID, summary and SLA deadline target. |
| **Ticket assigned** | Support ownership update indicating assigned engineering department. |
| **Status changed** | Meaningful lifecycle update with customer-visible admin note. |
| **Resolution proposed** | Customer asked to verify service in chat before closure. |
| **Incident detected/confirmed** | Affected customers in region informed of known issue and ETA. |
| **Complaint reopened** | Customer and support receive relevant update on escalation. |
| **SLA risk/breach** | Customer and support alerted where priority threshold is reached. |

### 13.1 MVP Notification Policy

In-app transactional updates are generated automatically from authenticated complaint state. **Mass proactive incident notifications must be reviewed and approved by an admin in the Notify Queue (`/admin/notifications`) to eliminate false-positive broadcast spam.** SMS/push provider integration is supported as optional webhooks.

---

## 14. Dynamic Network & Line Diagnostics

To deliver real-time utility beyond conversational text, the platform provides an on-demand network telemetry diagnostic tool (`/api/chat/diagnostic`).

| Metric | Broadband / Fiber | Mobile Data | Degraded (Active Outage) |
| :--- | :--- | :--- | :--- |
| **Download Speed** | 94.0 - 298.0 Mbps | 35.0 - 78.0 Mbps | 1.5 - 12.0 Mbps |
| **Upload Speed** | 88.0 - 290.0 Mbps | 15.0 - 32.0 Mbps | 0.5 - 4.0 Mbps |
| **Ping Latency** | 12.0 - 28.0 ms | 22.0 - 45.0 ms | 120.0 - 280.0 ms |
| **Jitter** | 1.2 - 4.5 ms | 3.5 - 8.0 ms | 25.0 - 65.0 ms |
| **Packet Loss** | 0.0% | 0.0 - 0.5% | 8.0 - 22.0% |
| **Line Health** | Optimal / Healthy | Optimal / Healthy | Degraded (Incident Linked) |

Customer requests speed test → Backend inspects customer region & active incidents → Returns telemetry payload → Rendered as a visual diagnostic card in chat.

---

## 15. Backend REST API Specifications

| Method & Route | Role | Purpose & Functionality |
| :--- | :---: | :--- |
| `POST /api/auth/login` | Public | Customer/admin authentication using implemented password hashing and role-aware authorization. |
| `POST /api/auth/signup` | Public | Customer self-registration with region and service. |
| `POST /api/chat` | Customer | Text conversational endpoint executing LangGraph StateGraph. |
| `POST /api/chat/diagnostic` | Customer | Executes real-time network speed/latency diagnostics. |
| `GET /api/my/tickets` | Customer | Lists authenticated customer's own tickets. |
| `GET /api/my/tickets/{id}/history` | Customer | Status history timeline for a specific owned ticket. |
| `POST /api/admin/upload/ingest` | Admin | Universal CSV ingestion with auto-schema mapping & ETL. |
| `GET /api/admin/queue` | Admin | Filterable, paginated priority-ranked ticket queue. |
| `PATCH /api/admin/complaints/{id}` | Admin | Updates ticket status, team assignment, and notes. |
| `POST /api/admin/complaints/{id}/propose-resolution` | Admin | Proposes technical fix (`resolved_pending_confirmation`). |
| `GET /api/admin/heatmap` | Admin | Regional complaint density & spike data for Leaflet map. |
| `GET /api/admin/incidents` | Admin | Lists active outage incidents & root-cause dossiers. |
| `POST /api/admin/assistant/chat` | Admin | Admin AI Assistant decision support LangGraph endpoint. |
| `GET /api/admin/audit` | Admin | Immutable security & administrative audit logs. |

### 15.1 API Security

- hashlib-based password hashing and role-aware authorization on protected routes.
- Customer ownership verification on every complaint read/write.
- Server-side validation of all status transitions.
- Comprehensive audit logging for privileged actions.
- API keys and secrets stored securely in environment variables.

---

## 16. Free / Low-Cost AI & API Strategy

The platform is engineered to run on 100% free-tier or open-source components with zero required software spend.

| Component | MVP Choice | Operational Role & Cost Profile |
| :--- | :--- | :--- |
| **Generative LLM API** | Groq Free Plan | Assistant responses, ticket summaries, root-cause narratives (Zero cost). |
| **Embeddings** | sentence-transformers | all-MiniLM-L6-v2 local CPU embeddings (Zero cost). |
| **Vector Store** | ChromaDB (local) | Persistent vector store for SOP retrieval (Zero cost). |
| **Multilingual Tokenizer** | Hugging Face DistilBERT | distilbert-base-multilingual-cased (Zero cost). |
| **Classification & ML** | scikit-learn | Complaint category and intent classification (Zero cost). |
| **Database** | SQLite (local) | Live operational state in WAL mode (Zero cost). |
| **Backend** | Python + FastAPI | REST API and background scheduler (Zero cost). |
| **Geocoding** | Geoapify (Free tier) | Location coordinates with memory cache (Zero cost). |

---

## 17. Non-Functional Requirements

| Category | Requirement & Implemented Standard |
| :--- | :--- |
| **Performance** | Customer/API interaction latency <= 1.5s on live Groq LLM, <= 50ms on offline fallback. |
| **Availability** | Ticket/status operations remain usable even if external LLM services are offline. |
| **Security** | hashlib-based password hashing and role-based authorization guards; no JWT requirement in the implemented flow. |
| **Privacy** | Automatic regex PII redaction of names, phone numbers and emails upon ingestion. |
| **Reliability** | Deterministic SQLite transactions; AI failures never create invalid states. |
| **Explainability** | AI classification, priority scores and root causes expose contributing factors and evidence. |
| **Auditability** | Status, assignment, resolution, escalation and notification actions are logged immutably. |
| **Language** | English, Hindi (Devanagari) and Hinglish transliteration support. |
| **Cost** | Free-tier architecture with zero cloud infrastructure overhead for the hackathon MVP. |

### 17.1 AI Safety Rules

- Never fabricate live ticket status or ticket IDs.
- Never claim an outage is confirmed when it is only an unverified AI hypothesis.
- Never claim resolution without explicit customer confirmation.
- Never reveal another customer's private data.
- Never perform privileged database actions directly from generated text.
- When confidence or evidence is insufficient, ask for clarification or escalate.

---

## 18. Technology Stack — Implemented Project Stack

| Area | Technology / Implementation |
| :--- | :--- |
| **Admin Frontend** | React + Vite; Admin Operations Dashboard; Admin AI Assistant; Recharts; React-Leaflet; shared Dark/Light Theme Engine. |
| **Customer Frontend** | React + Vite; 40/60 customer text-chat layout; diagnostic cards. |
| **Backend** | Python + FastAPI + Uvicorn; REST-style backend APIs and deterministic business logic. |
| **Authentication** | hashlib-based password hashing with role-aware authorization. |
| **AI Orchestration** | LangGraph Multi-Task StateGraph; separate customer and admin workflows. |
| **ML / NLP** | Hugging Face DistilBERT multilingual model; scikit-learn TF-IDF + Logistic Regression; multi-factor priority scoring. |
| **RAG / Knowledge** | ChromaDB persistent vector store + Sentence Transformers (all-MiniLM-L6-v2). |
| **Generative AI** | Groq Cloud API for Llama models, with deterministic offline fallbacks. |
| **Database** | SQLite 3 (tci.db) with WAL mode, foreign keys, status history and audit logs. |
| **Geolocation** | Geoapify Geocoding REST API with caching; Leaflet for regional heatmaps. |
| **Development / Runtime** | VS Code, npm/Vite frontend workflow, Python virtual environment, FastAPI/Uvicorn backend runtime. |

### 18.1 Separation of Responsibilities

| System | Should Do | Should Not Do |
| :--- | :--- | :--- |
| **SQLite** | Store authoritative live operational state. | Generate natural-language answers. |
| **ChromaDB** | Retrieve semantic SOP knowledge. | Store authoritative live ticket status. |
| **scikit-learn ML** | Classify/score structured complaint data. | Perform privileged database mutation. |
| **Groq LLM** | Reason over supplied context and generate language. | Invent current system state or ticket IDs. |
| **FastAPI** | Authorize and execute state transitions. | Depend on generated text for authorization. |
| **Admin Dashboard** | Operate, monitor and approve broadcasts. | Bypass backend authorization or audit logs. |

---

## 19. Testing & Acceptance Criteria

| Scenario | Admin-Oriented Acceptance Criteria |
| :--- | :--- |
| **Admin overview** | Dashboard shows complaint volume, open/resolved tickets, high priority, SLA risk and active incidents. |
| **Queue management** | Admin can search/filter, assign, update, escalate and inspect ticket history. |
| **Incident investigation** | Spike detection creates/updates an incident and links matching complaints. |
| **Root cause** | Dashboard shows evidence signals, confidence and affected scope for an AI hypothesis. |
| **Admin AI** | Operations AI answers using live DB snapshots and approved ChromaDB SOPs without unrestricted DB access. |
| **Notification approval** | Admin reviews/approves proactive incident notifications before broadcast. |
| **Customer resolution** | Customer confirmation closes an eligible complaint; rejection reopens/escalates. |
| **Authorization** | A customer cannot read another customer's complaint even with its ticket ID. |
| **AI outage** | Groq unavailable → deterministic ticket/status APIs continue to work with offline fallbacks. |

### 19.1 Key KPIs & Validated Benchmarks

- **Complaint classification macro-F1:** >= 82.4% on the held-out split.
- **Intent routing accuracy:** >= 95.0% across 15+ supported intents.
- **Ticket creation correctness:** 100% in automated workflow tests.
- **Status retrieval correctness:** 100% in authorized customer tests.
- **Resolution confirmation capture:** 100% of AI-assisted resolution attempts.
- **Test suite pass rate:** 100% (106+ passing backend tests as specified in the PRD).

---

## 20. Implementation Plan & Demo

| Phase | Implementation Milestone |
| :---: | :--- |
| **1** | Admin dashboard foundation, SQLite schema, authentication, role-based access and demo accounts. |
| **2** | FastAPI complaint/status APIs, CSV schema mapper and audit logging. |
| **3** | Admin AI Assistant + LangGraph admin workflow + live DB snapshots + ChromaDB SOP retrieval. |
| **4** | Admin queue, ticket drawer, assignment, priority/SLA and status management. |
| **5** | Leaflet heatmap, Geoapify geocoding, spike detection and incident management. |
| **6** | Root-cause investigator, evidence dossier and confidence gauge. |
| **7** | Proactive notification queue, admin approval and in-app notification feed. |
| **8** | Customer LangGraph assistant, conversation state, intent routing and DistilBERT. |
| **9** | Complaint verification, ticket creation, live status tracking and line diagnostics. |
| **10** | ChromaDB/SentenceTransformers troubleshooting and resolution confirmation loop. |
| **11** | Reopen/escalation workflow, customer feedback and analytics. |
| **12** | Theme engine (Dark/Light), text-chat UI validation and full test-suite validation. |

### 20.1 Minimum Successful Admin Demo

- Admin opens the dashboard and immediately sees queue, priority, SLA, incident and trend information.
- Admin filters a complaint cluster and investigates the associated incident/heatmap.
- Admin asks the Operations AI Assistant why the spike is occurring and receives evidence-backed analysis.
- Admin assigns the affected tickets to the appropriate support/network team.
- Admin updates status and proposes a resolution; the customer receives the update.
- Customer confirms or rejects the resolution; the dashboard reflects the resulting closed or reopened state.
- Admin reviews and approves a proactive notification for affected customers.
- Admin uses the audit trail to verify the operational actions.

---

## 21. Product Differentiation

| Traditional Complaint System | Proposed TelConnect Platform |
| :--- | :--- |
| **Passive ticketing** | Admin control plane with live queue, assignments, SLA and resolution actions. |
| **Fragmented reporting** | Unified operational intelligence across complaints, incidents, heatmaps and analytics. |
| **Manual investigation** | Admin AI Assistant combines live DB context, SOP retrieval and evidence synthesis. |
| **Outages discovered late** | Complaint spikes trigger anomaly alerts, incident records and root-cause dossiers. |
| **No governance layer** | Role-based access, controlled actions, immutable audit logs and notification approval. |
| **Customer status is opaque** | Admin updates flow to the customer text channel with live authoritative state. |
| **Dataset-driven operation** | SQLite is the dynamic operational source; CSV is seed/analysis data only. |
| **Generic AI chatbot** | Controlled LangGraph multi-task agents connected to authorized backend functions. |

### 21.1 Final Product Definition

An admin-oriented telecom complaint intelligence and automated resolution platform that gives support and network operations teams a unified control plane for complaint triage, ticket management, incident detection, heatmaps, root-cause analysis, AI decision support, proactive notifications and auditability, while a connected customer text assistant provides diagnostics, troubleshooting, status tracking and explicit resolution confirmation.

---

## 22. Recommended Presentation Flow

| Scene | Admin-Led Demonstration | Message to Judges |
| :--- | :--- | :--- |
| **Admin overview** | Open dashboard with queue, SLA risk, incidents and trends. | TelConnect starts with operational visibility. |
| **Complaint intelligence** | Open a complaint and show category, sentiment, urgency, priority and escalation risk. | The system turns raw complaints into actionable intelligence. |
| **Incident / heatmap** | Inspect a spike and drill into region, service and affected complaints. | Operations can detect service-wide issues early. |
| **Admin AI Assistant** | Ask why the spike is occurring and retrieve SOP/evidence. | AI supports decisions without bypassing authorization. |
| **Ticket action** | Assign, update, escalate or propose resolution from the dashboard. | The admin remains in control of operational actions. |
| **Customer confirmation** | Customer accepts/rejects the fix; dashboard reflects the outcome. | Closed-loop resolution prevents silent closure. |
| **Notification** | Admin reviews and approves a proactive incident notification. | Human-in-the-loop reduces false-positive broadcasts. |
| **Audit** | Show status/action history. | Every privileged action is traceable. |
| **Customer channel** | Briefly demonstrate text chat, diagnostics and live status. | The customer experience is the service channel, not the operational control plane. |

---

## 23. Requirements Traceability to Use Case 13

| Use Case Requirement | PRD Implementation |
| :--- | :--- |
| **Prioritize critical complaints** | Multi-Factor Priority Scoring + Admin Queue + SLA deadlines. |
| **Predict escalation risk** | Escalation Risk model + alerts. |
| **Detect service problems** | Spike detection + Leaflet heatmap + Incident Management. |
| **Recommend resolution actions** | ChromaDB Vector RAG + approved SOP procedures. |
| **Complaint triage assistant** | LangGraph customer multi-task workflow. |
| **Operations AI decision support** | LangGraph Admin Operations Agent (/admin/assistant). |
| **Classify complaint categories** | TF-IDF + Logistic Regression (Macro-F1 >= 82.4%). |
| **Customer experience** | 40/60 text chat, line diagnostics, confirm-to-close loop. |
