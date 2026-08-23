# Product Requirements Document (PRD v7.0)

# Telecom Complaint Intelligence & Automated Resolution Assistant (TelConnect)
**Professional, Customer-First Product Specification & Technical Architecture**  
*Cognizant Hackathon • Use Case 13*

---

## Document Specification

| Specification | Details |
| :--- | :--- |
| **Document Version** | **7.0 — Autonomous Multi-Task Agent & Multilingual Intelligence PRD** |
| **Product Name** | **TelConnect** (Telecom Complaint Intelligence & Automated Resolution Assistant) |
| **Product Type** | AI-powered telecom complaint intelligence, autonomous resolution & network operations platform |
| **Primary User** | Telecom Customer (Mobile Data, Broadband, Fiber, Landline) |
| **Operational User** | Support Team, Field Operations, RF Engineers, Network Ops & Admin Teams |
| **Agent Orchestration** | **LangGraph Multi-Task StateGraph** (6-node customer agent & 4-node admin operations agent) |
| **Multilingual Engine** | **Hugging Face DistilBERT** (`distilbert/distilbert-base-multilingual-cased`) + Groq Zero-Shot Neural Translation + Lexical Domain Fallback |
| **Primary AI Provider** | **Groq Cloud API** (Llama-3 models + Whisper voice STT) with complete deterministic offline fallback |
| **Voice Stack** | **Groq Whisper** (Multilingual STT) + **Web Speech API** (Bilingual TTS audio readout) |
| **Operational Database** | **SQLite 3** (`tci.db` with WAL mode, foreign keys, and immutable audit logs) |
| **Knowledge Store** | **ChromaDB** persistent vector database + **Sentence Transformers** (`all-MiniLM-L6-v2` dense embeddings) |
| **Geolocation Engine** | **Geoapify Geocoding API** (dynamic in-memory cache & coordinate boundary validation) |
| **Core Backend** | **Python 3.10+ + FastAPI + Uvicorn** |
| **Frontend UI** | **React 18/19 (Vite SPA)** with 40/60 Split Layout, Leaflet Regional Heatmap, Recharts & Theme Engine (Dark/Light) |
| **Test Coverage** | **106+ Automated Tests Passing** in `backend/tests/` |

> **Product Vision**: Turn telecom complaints from isolated, opaque support tickets into an autonomous, closed-loop intelligence system that understands customer intent in any language, performs dynamic network line diagnostics, provides grounded RAG troubleshooting, tracks live ticket states transparently, detects geographic complaint spikes in real time, generates evidence-backed root-cause dossiers, and proactively prevents recurring complaints.

This PRD preserves and elevates the capabilities of Use Case 13 — complaint classification, sentiment detection, escalation prediction, vector RAG, root-cause analysis, geographic heatmaps, spike detection, and proactive notification — while restructuring them around an end-to-end customer complaint-to-resolution journey and modern agentic architectures.

---

## 1. Product Overview

The **Telecom Complaint Intelligence & Automated Resolution Assistant (TelConnect)** is a customer-facing conversational AI service paired with an operational support and network intelligence control plane.

The platform accepts customer complaints via text or voice, auto-normalizes language across English, Hindi (Devanagari), and Hinglish transliteration, performs instant network line diagnostics, checks for active geo-incidents, retrieves approved troubleshooting standard operating procedures (SOPs), registers and prioritizes tickets with transparent factor scoring, and verifies resolution satisfaction before ticket closure.

The **Admin Operations Console** is the operations control plane used to manage the complaint lifecycle, triage priority-ranked queues, inspect Leaflet geographic heatmaps, investigate automated root-cause hypotheses, approve proactive broadcast notifications, evaluate AI recommendations via the **Admin AI Assistant**, and audit system actions.

### 1.1 Product Principles

1. **Customer First**: The primary workflow begins with the customer's problem and concludes *only* when the customer confirms the resolution or explicitly rates the interaction.
2. **One Source of Truth**: The customer assistant and admin console read and write to the same operational database (`tci.db`), guaranteeing zero data drift and zero stale LLM hallucinations.
3. **AI with Controlled Actions**: The LLM interprets, synthesizes language, and provides contextual empathy. All privileged operations (ticket creation, status transitions, line testing, broadcast approvals) are strictly executed by deterministic backend APIs.
4. **Dynamic by Design**: Complaints can be created by customers, admins, or authorized data feeds; the system operates on a live SQLite database rather than static CSV data.
5. **Closed Loop**: A proposed resolution requires customer confirmation before an eligible complaint is closed. Rejection automatically reopens and escalates the ticket.
6. **Explainable Intelligence**: Classification, priority scoring, escalation risk, and root-cause outputs expose their underlying evidence, mathematical weights, and contributing factor chips rather than opaque numbers.
7. **Zero-Cost & Offline Resilient**: Architected to operate within free-tier limits (Groq Free API, Geoapify Free Plan) with immediate deterministic fallbacks for 100% offline functionality.

### 1.2 Problem Statement

Telecom operators receive large volumes of complaints related to network outages, call drops, broadband slowdowns, billing disputes, and device configurations. Manual triage is slow, customers lack visibility into ticket progress, and network operations teams often discover mass outages only after hundreds of repetitive complaints overwhelm call centers.

The product solves two connected problems:
1. **Helps individual customers reach a verified resolution faster** through intelligent triage, instant line diagnostics, grounded RAG self-service, and transparent status tracking.
2. **Converts complaint data into operational network intelligence** that helps telecom operators detect geographic surges, investigate evidence-backed root causes, and proactively alert affected subscribers before complaints escalate.

---

## 2. Objectives & Success Criteria

### 2.1 Objectives

| Objective | Expected Outcome |
| :--- | :--- |
| **Automate Complaint Understanding** | Classify intent, category, subcategory, extract entities, and detect sentiment, urgency, and escalation risk using machine learning. |
| **Instant Line & Speed Diagnostics** | Provide on-demand network telemetry tests (download/upload speed, ping latency, jitter, packet loss) directly inside the customer chat. |
| **Improve First-Contact Resolution (FCR)** | Intercept known issues via active incident checks and grounded RAG troubleshooting before escalating to human support. |
| **Create a Complete Complaint Lifecycle** | Support two-phase verification, ticket creation, team assignment, status updates, resolution proposal, customer confirmation, reopening, and escalation. |
| **Give Customers Live Visibility** | Allow authenticated customers to query ticket status, assigned team, SLA deadlines, and status history from the assistant. |
| **Reduce Duplicate Complaints** | Match incoming complaints against active regional incidents and link reports without creating duplicate tickets. |
| **Detect Mass Service Problems** | Group complaints by region and service, detecting abnormal volume surges against rolling historical baselines. |
| **Support Root-Cause Investigation** | Correlate temporal, spatial, and symptom concentrations to generate explainable incident dossiers with confidence bars and evidence bullets. |
| **Proactively Inform Customers** | Draft and review broadcast notifications for affected customers before they file repeated complaints. |
| **Equip NOC with Operations AI** | Provide an autonomous LangGraph decision support agent for NOC admins to query critical complaints, escalation risks, and ChromaDB SOPs. |
| **Improve Operational Efficiency** | Provide an admin dashboard for queue management, heatmap monitoring, incident operations, analytics, and CSV data export. |

### 2.2 Success Criteria

- Customer can report a complaint or run line diagnostics in English, Hindi, or Hinglish without navigating complex forms.
- Every valid complaint receives a unique ticket ID (`TCK-xxx`), $P1 - P4$ priority score, factor chips, and persistent database record.
- Customer can retrieve live ticket status and audit history at any time.
- AI-assisted resolution never silently closes a complaint without explicit customer confirmation (`Yes ✓` closes; `No ✗` reopens/escalates).
- Admin status updates and resolution proposals are reflected in the customer experience in real time.
- Active regional incidents are linked to new complaints, avoiding duplicate tickets and showing live outage progress.
- Admin dashboard surfaces real-time complaint volumes, priority rankings, category distributions, sentiment trends, geographic heatmaps, and evidence-backed incident dossiers.
- 100% offline resilience: all core features function seamlessly even without external API connectivity.

### 2.3 Scope Boundaries

- **Complaint Intelligence & Orchestration**: The MVP focuses on complaint understanding, diagnostic simulation, and resolution orchestration; it does not directly control physical telecom network switches.
- **Simulated OSS/BSS Integration**: Standardized backend API models represent telecom OSS/BSS data feeds.
- **In-App Transactional Notifications**: Real-time in-app notification feeds demonstrate notification delivery; external SMS/push delivery can be integrated via webhooks.
- **Database-Driven Runtime**: The platform uses sample CSV data for initial ingestion and evaluation but relies on SQLite (`tci.db`) and ChromaDB as live operational stores.

---

## 3. Users, Roles & Access Control

| Role | Needs | Key Capabilities |
| :--- | :--- | :--- |
| **Customer** | Fast assistance, instant line tests, clear ticket status, multilingual chat, resolution verification. | Conversational assistant, speech input/output, line diagnostics, ticket creation, status tracking, confirmation, reopen, feedback rating. |
| **Support Admin** | Efficient queue triage, ticket assignment, SLA monitoring, resolution proposal. | Priority queue, ticket management drawer, team assignment, status transitions, customer-facing notes, resolution proposal. |
| **Network Operations (NOC)** | Real-time outage detection, heatmap visualization, root-cause investigation, broadcast alerts. | Regional heatmap, spike detection alerts, root-cause dossiers, field team assignment, broadcast notification approval. |
| **Operations Admin (AI User)** | Decision support, briefing generation, classification reasoning, SOP recommendations. | Admin AI Assistant (`/admin/assistant`), prompt chips, live database snapshot querying, ChromaDB SOP synthesis. |
| **System / AI Agents** | Automated NLP classification, scoring, RAG retrieval, incident correlation, language translation. | LangGraph state machine execution, scikit-learn scoring, ChromaDB retrieval, Groq synthesis, audit logging. |

### 3.1 Access Control & Security Safeguards

- **Strict Customer Data Isolation**: Authenticated customers can access only their own profile, conversations, tickets, history, and notifications via signed Bearer JWT tokens.
- **Role-Based Authorization**: Support and NOC endpoints require valid admin credentials.
- **Controlled Agent Execution**: AI models do not receive raw SQL execution permissions; all mutations occur through authenticated backend API controllers.
- **Immutable Audit Logging**: All privileged administrative and customer lifecycle transitions are logged in `audit_logs` and `complaint_status_history`.

---

## 4. End-to-End Customer Complaint-to-Resolution Journey

```
[Customer Interaction] ──> [1. Intent & Lang Translation]
                                   │
                                   ▼
                       [2. Active Outage Match?]
                              ├── Yes ──> Explain Outage, Root Cause & Link Ticket (No Duplicates)
                              └── No  ──> [3. Grounded RAG SOP Troubleshooting]
                                                ├── Fix Works ──> Confirm & Close (CSAT Feedback)
                                                └── Unresolved ──> [4. Pre-Ticket Verification]
                                                                          │
                                                                          ▼
                                                                [5. Register Ticket (P1-P4, SLA)]
                                                                          │
                                                                          ▼
                                                                [6. Admin Triage & Propose Fix]
                                                                          │
                                                                          ▼
                                                                [7. Confirm-to-Close Loop in Chat]
                                                                      ├── Customer "Yes" ──> Closed & 1-5★ Rating
                                                                      └── Customer "No"  ──> Reopen & Auto-Escalate
```

### 4.1 Step-by-Step Lifecycle Flow

1. **Start**: Customer describes an issue or runs a speed test via text or voice in English, Hindi, or Hinglish.
2. **Translate & Tokenize**: Hugging Face DistilBERT normalizes input into canonical English semantics.
3. **Diagnose**: The agent inspects dynamic telemetry and checks for active geo-incidents.
4. **Resolve**: If eligible, the assistant retrieves approved ChromaDB SOPs and guides the customer through self-service troubleshooting.
5. **Verify**: If unresolved, the assistant summarizes extracted details (category, region, service) and asks for confirmation before ticket creation.
6. **Ticket**: Upon confirmation, a unique ticket ID (`TCK-xxx`), priority tier ($P1 - P4$), SLA deadline, and auto-generated summary are persisted.
7. **Track**: Customer queries live status, assigned team, and SLA deadlines at any time.
8. **Propose Fix**: Support or field teams apply a fix and transition the ticket to `resolved_pending_confirmation`.
9. **Confirm-to-Close**: The assistant prompts the customer in chat. `Yes ✓` closes the ticket and collects a 1–5 star CSAT rating. `No ✗` reopens and auto-escalates to senior teams.

### 4.2 Complaint Status State Machine

```
NEW ──> IN_PROGRESS ──> WAITING_FOR_CUSTOMER ──> RESOLVED_PENDING_CONFIRMATION ──> CLOSED
             │                                                │
             ├──> ESCALATED <── REOPENED <────────────────────┘
             └──> REOPENED (Customer reports recurrence)
```

Every status transition creates an immutable record in `complaint_status_history` storing `from_status`, `to_status`, `actor`, `reason`, and `timestamp`.

---

## 5. Autonomous Customer AI Assistant

The Customer AI Assistant is implemented as a 6-node **LangGraph StateGraph** multi-task workflow (`backend/app/agents/agent_graph.py`).

### 5.1 Supported Intents

| Intent | Description & Trigger Examples | Backend Action |
| :--- | :--- | :--- |
| `DIAGNOSTIC` | *"run speed test"*, *"check my line speed"*, *"ping check"* | Executes `run_network_diagnostic` and renders telemetry card. |
| `REPORT_COMPLAINT` | *"internet is down"*, *"broadband red light"*, *"bill extra charge"* | Extracts entities, checks incidents/RAG, stages pre-ticket confirmation. |
| `CHECK_STATUS` | *"what is the status of my ticket?"*, *"track complaint"* | Queries SQLite for live ticket state, assigned team, and SLA deadline. |
| `TROUBLESHOOT` | *"how to reset router"*, *"wifi slow fix"* | Retrieves matching SOPs from ChromaDB vector store. |
| `KNOWN_INCIDENT` | *"outage in Raj Nagar"*, *"is net down in my area?"* | Explains live incident status, root cause, and estimated resolution. |
| `CONFIRM_RESOLUTION` | *"yes, it works now"*, *"fixed"*, *"haan chal gaya"* | Transitions ticket to `closed` and prompts for 1–5 star CSAT rating. |
| `REJECT_RESOLUTION` | *"no, still broken"*, *"nahi chala"* | Reopens ticket, escalates priority, and alerts support queue. |
| `REOPEN_COMPLAINT` | *"issue is back again"*, *"dobara band ho gaya"* | Reopens closed ticket and updates status history timeline. |
| `BILLING_QUERY` | *"why was ₹500 deducted?"*, *"recharge plan details"* | Provides verified billing guidance and invoice breakdown. |
| `ESCALATE` | *"talk to human"*, *"connect to manager"*, *"executive se baat"* | Escalates ticket to senior support queue with priority bump. |
| `GENERAL_QUERY` | Telecom service questions, 5G availability, SIM replacement. | Grounded response from knowledge base documents. |

### 5.2 LangGraph 6-Node Customer Agent Architecture

```
[User Text / Voice] 
         │
         ▼
 1. translate_input (Hugging Face DistilBERT Tokenizer + Lang Detection)
         │
         ▼
 2. route_intent (Intent Classifier & State Continuation Engine)
         │
         ▼
 3. retrieve_context (Active Outage Geo-Match + ChromaDB Dense Vector RAG)
         │
         ▼
 4. execute_action (Line Speed Tests / Ticket DB Mutations / Verified Facts)
         │
         ▼
 5. synthesize_response (Grounded Groq LLM Generation / Zero Hallucination)
         │
         ▼
 6. translate_output (Devanagari Script Formatting / Bilingual Audio TTS)
         │
         ▼
[Rendered Chat Reply + Telemetry Cards]
```

### 5.3 Core Agentic Design Rule
The LLM never directly modifies database states or invents live ticket data. The LLM interprets natural language, provides empathetic responses, and structures output. All mutations (ticket creation, status updates, resolution verification, line speed testing) are executed strictly through deterministic backend Python APIs.

---

## 6. Solution Architecture & System Layers

| System Layer | Components | Operational Purpose |
| :--- | :--- | :--- |
| **1. Presentation Layer** | React 18/19, Vite, React Router v7, Leaflet, Recharts, ThemeContext | Role-separated responsive UI (Landing page, 40/60 Customer Chat, Admin Operations Cockpit, Dark/Light theme). |
| **2. API & Security Layer** | FastAPI, Uvicorn, Pydantic, Scrypt Auth, JWT Tokens | Role-gated REST endpoints, request validation, CORS middleware, background pipeline scheduler. |
| **3. Agentic Layer** | LangGraph StateGraph (Customer 6-Node & Admin 4-Node Workflows) | Multi-task agent execution, state management, tool invocation, verified fact synthesis. |
| **4. Multilingual Engine** | Hugging Face DistilBERT (`distilbert-base-multilingual-cased`) | Multilingual tokenization, language detection, Hinglish normalization, Devanagari script validation. |
| **5. Machine Learning Layer** | scikit-learn (`TF-IDF + LogisticRegression`), Multi-Factor Scoring | Category classification ($\ge 82.4\%$ macro-F1), sentiment/urgency analysis, escalation risk, $P1 - P4$ priority scoring. |
| **6. Vector Knowledge RAG** | ChromaDB Persistent Client + Sentence Transformers (`all-MiniLM-L6-v2`) | Dense semantic vector indexing and cosine similarity retrieval over SOPs, FAQs, and past resolved cases. |
| **7. Generative AI & Speech** | Groq Cloud API (Llama-3.3-70b, Llama-3.1-8b, Whisper-large-v3-turbo) | Fast natural language synthesis, ticket summarization, root-cause narratives, multilingual voice STT. |
| **8. Operational Data Store** | SQLite 3 (`tci.db` with WAL mode) | Single source of truth for users, complaints, status history, incidents, notifications, feedback, and audit logs. |
| **9. Geolocation Engine** | Geoapify Geocoding API (`geo.py`) | Address-to-coordinate lookup with in-memory caching and India boundary validation for heatmap rendering. |
| **10. Anomaly Intelligence** | Rolling-Baseline Spike Detector & Root-Cause Investigator | Statistical surge detection against 7-day baselines, multi-signal evidence dossiers, automated notification drafting. |

---

## 7. Admin Operations Console (16 Modular Subsystems)

| # | Modular Subsystem | Operational Capabilities & Feature Set |
| :---: | :--- | :--- |
| **1** | **Universal Dataset Ingest** | 3-step wizard: file selection, auto-detected column schema mapping, PII redaction, ML scoring, and pipeline execution. |
| **2** | **Operations Overview** | Real-time stat cards (total, open, in-progress, resolved), volume time series, category breakdown donut, sentiment trend, recurring themes, escalation risk table. |
| **3** | **Complaint Queue** | Priority-ranked ($P1 - P4$) triage workbench with multi-facet filters (category, region, service, status, channel) and live SLA countdowns. |
| **4** | **Ticket Management** | Slide-over drawer displaying customer-safe summaries, priority factor chips, sentiment score, and full audit timeline. |
| **5** | **Assignment & Routing** | One-click assignment to specialized departments (*Field Ops, RF Team, Billing Team, Support L2, Network Ops*). |
| **6** | **Resolution Management** | Propose technical fixes transitioning tickets to `resolved_pending_confirmation` for customer validation. |
| **7** | **Status History Timeline** | Immutable audit trail displaying every status change, actor ID, timestamp, and transition note. |
| **8** | **Leaflet Network Heatmap** | Interactive map of India rendering regional complaint density circles (Red = Surge, Amber = Elevated, Teal = Normal). |
| **9** | **Spike Detection Engine** | Rolling baseline statistical anomaly detector automatically opening incident records upon volume surges. |
| **10** | **Root-Cause Dossiers** | AI-generated investigative dossiers displaying likely causes, confidence gauges ($90\%+$), and $\ge 3$ checkable evidence bullets. |
| **11** | **Incident Operations** | Acknowledge alerts, assign field teams, trigger broadcast notification drafts, and bulk-resolve linked complaints. |
| **12** | **Real-Time Alert Inbox** | Instant alerts on newly detected surges with unread badge counters and direct links to incident dossiers. |
| **13** | **Proactive Notify Queue** | Human-in-the-loop review queue for drafting, reviewing, approving, or rejecting broadcast notifications to affected users. |
| **14** | **Executive Analytics** | Resolution rates, MTTR, escalation percentages, category trends, and customer CSAT satisfaction metrics. |
| **15** | **Live Data Export** | One-click export of filtered complaint records to standards-compliant CSV files. |
| **16** | **🤖 Admin AI Assistant** | LangGraph-powered NOC decision support assistant answering complex operational queries with live DB snapshots and ChromaDB SOPs. |

### 7.1 Admin Console Principle
The Admin Console helps operators rapidly answer four critical questions: **What is happening? Which customers are affected? What action should we take? Has the customer confirmed the resolution?**

---

## 8. Complaint Intelligence & Priority Scoring Pipeline

### 8.1 Machine Learning Capabilities

| Pipeline Capability | Input Data | Output Prediction | Algorithm / Engine |
| :--- | :--- | :--- | :--- |
| **Text Classification** | Complaint text | Category & Subcategory | TF-IDF + Logistic Regression (Macro-F1 $\ge 82.4\%$) |
| **Intent Routing** | Conversational text | 15+ Operational Intents | Regex Matchers + LangGraph Intent Classifier |
| **Entity Extraction** | Complaint text | Region, Service, Device, Symptoms | Regex Entity Extractor + DistilBERT Normalizer |
| **Sentiment Analysis** | Complaint message | Score ($-1.0\text{ to }+1.0$), Label | Lexicon & Rule-based Sentiment Model |
| **Urgency Detection** | Complaint text + context | Urgency Score ($0.0\text{ to }1.0$) | Domain Keyword & Severity Weighting Model |
| **Escalation Risk** | Text + Sentiment + History | Churn & Legal Risk ($0.0\text{ to }1.0$) | Multi-Factor Escalation Risk Predictor |
| **Priority Scoring** | Multi-factor parameters | Priority Score ($0 - 100$), $P1 - P4$ | Explainable Multi-Factor Formula with Factor Chips |
| **Ticket Summary** | Complaint details | Concise 1-sentence summary | Groq Llama-3 / Deterministic Fallback Template |

### 8.2 Multi-Factor Priority Formula & SLA Bands

$$\text{PriorityScore} = \text{clamp}\Big(0, 100, \, w_1 \cdot U + w_2 \cdot S + w_3 \cdot E + w_4 \cdot I + w_5 \cdot R \Big)$$

- $U \in [0, 1]$: Urgency score (detected from emergency keywords like *down, exam, hospital, critical*).
- $S \in [0, 1]$: Inverted sentiment score (higher for negative sentiment).
- $E \in [0, 1]$: Churn / escalation risk probability (e.g., mentions of *TRAI, legal, switch operator*).
- $I \in \{0, 1\}$: Active regional incident indicator ($+20\text{ bonus points}$ if linked to an ongoing outage).
- $R \in [0, 1]$: Repeat contact count for the customer account.

| Priority Tier | Score Range | SLA Target | Automated Operational Action |
| :---: | :---: | :---: | :--- |
| **P1 — Critical** | $80 - 100$ | **2 Hours** | High-priority admin alert; immediate queue banner |
| **P2 — High** | $60 - 79$ | **6 Hours** | Routed to Tier-2 specialist queue |
| **P3 — Medium** | $35 - 59$ | **24 Hours** | Standard operational queue |
| **P4 — Low** | $0 - 34$ | **48 Hours** | General queue |

---

## 9. ChromaDB Vector RAG Knowledge Architecture

RAG is used to make the assistant useful for actual problem resolution rather than simple classification.

### 9.1 Knowledge Sources
- **Standard Operating Procedures (SOPs)**: Step-by-step guides for broadband reset, ONT reconfiguration, APN settings, eSIM activation, billing disputes.
- **Troubleshooting FAQs**: Approved customer self-service steps.
- **Incident Write-Ups**: Historical post-mortems and known fix patterns.
- **Resolved Complaints**: Database of confirmed technical resolutions.

### 9.2 Resolution Decision Matrix

| Condition | Assistant Action |
| :--- | :--- |
| **Active Geo-Incident Exists** | Explain known outage, provide root cause, link report to incident, prevent duplicate ticket. |
| **Known Low-Risk Issue + Good RAG Match** | Guide customer through safe step-by-step troubleshooting SOPs. |
| **Insufficient RAG Knowledge** | Ask targeted clarification questions or escalate; never hallucinate. |
| **Account-Sensitive Query** | Retrieve authenticated data from SQLite or route to human support. |
| **Troubleshooting Succeeds** | Ask customer to confirm resolution (`Yes ✓`). |
| **Customer Rejects Fix** | Reopen ticket, escalate priority, and record previous attempt in history. |

### 9.3 RAG Grounding Rule
Every troubleshooting response must be generated from retrieved approved knowledge. The assistant is strictly prohibited from claiming a cause, ETA, or fix not supported by the retrieved ChromaDB chunks or live SQLite state.

---

## 10. Dynamic Data & Database Schema

The SQLite operational database (`backend/data/tci.db`) serves as the single source of truth across all components.

```
[users] 1 ──── ∞ [complaints] 1 ──── ∞ [complaint_status_history]
   │                 │
   │                 ├── 1 ──── 1 [resolutions]
   │                 └── ∞ ──── 1 [incidents] 1 ──── ∞ [notifications]
   └── 1 ──── ∞ [feedback]
```

### 10.1 Core Database Tables

| Table Name | Primary Purpose & Key Fields |
| :--- | :--- |
| `users` | Customer and admin profiles (`user_id`, `role`, `name`, `email`, `password_hash`, `region`, `service_type`). |
| `complaints` | Live complaint records (`complaint_id`, `customer_id`, `text`, `category`, `region`, `lat`, `long`, `service_type`, `sentiment`, `urgency`, `escalation_risk`, `priority_score`, `priority_label`, `sla_deadline`, `status`, `incident_id`, `assigned_to`, `ticket_summary`, `created_at`). |
| `complaint_status_history` | Immutable audit trail (`history_id`, `complaint_id`, `from_status`, `to_status`, `actor`, `reason`, `created_at`). |
| `incidents` | Mass outage dossiers (`incident_id`, `region`, `service_type`, `complaint_count`, `spike_pct`, `root_cause`, `confidence`, `evidence`, `status`, `admin_ack_status`, `opened_at`, `resolved_at`). |
| `notifications` | Transactional & broadcast notifications (`notification_id`, `recipient_id`, `recipient_type`, `incident_id`, `text`, `match_reason`, `approval_status`, `read`, `created_at`). |
| `resolutions` | Technical resolution proposals (`resolution_id`, `complaint_id`, `proposed_by`, `source`, `text`, `created_at`). |
| `feedback` | Customer CSAT ratings (`feedback_id`, `complaint_id`, `customer_id`, `rating`, `comment`, `created_at`). |
| `kb_docs` | RAG source documents (`doc_id`, `kind`, `title`, `body`, `category`). |
| `audit_logs` | Security and administrative audit trail (`log_id`, `user_id`, `role`, `action`, `target`, `payload`, `created_at`). |

---

## 11. Verification, Status & Resolution Management

### 11.1 Customer Verification
- Authenticate customer before exposing personal complaint information.
- For a new complaint, summarize extracted details and request confirmation before ticket creation.
- Identify existing complaints through authenticated account state rather than trusting arbitrary ticket numbers.

### 11.2 Live Status Visibility
- Customers can query ticket status in natural language (English, Hindi, Hinglish).
- Assistant retrieves authoritative live state directly from SQLite (`tci.db`).
- Returns ticket ID, current status, assigned team, SLA countdown, and resolution notes.

### 11.3 Confirm-to-Close Loop
- Support or AI proposes a resolution $\to$ ticket moves to `resolved_pending_confirmation`.
- Customer is prompted in the chat interface to verify if the service is restored.
- **Yes ✓**: Confirms resolution $\to$ ticket moves to `closed` $\to$ prompts for 1–5 star CSAT feedback.
- **No ✗**: Reopens ticket $\to$ moves to `reopened` / `escalated` $\to$ routes to senior support queue.

---

## 12. Mass Complaint Intelligence & Root-Cause Analysis

### 12.1 Complaint Spike Detection
- Compares complaint volume in rolling 6-hour windows against 7-day historical baselines per region and service.
- Automatically opens an `incident` record when complaint density exceeds statistical thresholds ($3\times - 300\times$ surge).
- Links subsequent incoming complaints to the active incident to prevent duplicate tickets.

### 12.2 Leaflet Geographic Heatmap
- Visualizes real-time complaint density across Indian telecom circles.
- Color-coded density circles: **Red** (abnormal surge), **Amber** (elevated volume), **Teal** (normal baseline).
- Interactive popup displays regional statistics, active incidents, and direct drill-down links.

### 12.3 AI Root-Cause Investigator

| Evidence Signal | Analytical Computation | Operational Example |
| :--- | :--- | :--- |
| **Volume Anomaly** | Multiplier vs historical rolling baseline. | $352\times$ surge above normal baseline in Raj Nagar. |
| **Geographic Concentration** | Percentage of complaints originating in target region. | $94.2\%$ of recent complaints concentrated in Ghaziabad circle. |
| **Service Concentration** | Percentage of complaints targeting a specific service. | $98.1\%$ of complaints involve Fiber Broadband. |
| **Symptom Alignment** | Dominant symptom keyword cluster. | *"Red optical light blinking / No LOS signal"* in $89\%$ of reports. |
| **Historical Match** | Cosine similarity against past resolved incidents. | $92\%$ match with historical incident `INC-2025-0873` (Optical Fiber Feeder Cut). |

**Dossier Output**: Likely cause (*"Optical Fiber Cut / Physical Feeder Severance"*) + Confidence Gauge ($92\%$) + $\ge 3$ verifiable evidence bullets + Recommended field remediation action.

---

## 13. Proactive Customer Notification

| Event Trigger | Notification Target | Operational Behavior |
| :--- | :--- | :--- |
| **Ticket Created** | Complaining Customer | In-app confirmation with ticket ID, summary, and SLA target. |
| **Ticket Assigned** | Complaining Customer | Update indicating assigned engineering/support team. |
| **Status Updated** | Complaining Customer | In-app notification of status transition with notes. |
| **Resolution Proposed** | Complaining Customer | Prompt in chat asking customer to verify fix and confirm closure. |
| **Mass Incident Detected** | All Affected Subscribers in Region | AI drafts broadcast notification $\to$ queued for **Admin Approval** before delivery. |

### 13.1 Human-in-the-Loop Notification Policy
Transactional updates are delivered automatically. Mass outage broadcast notifications are held in the **Notify Queue** (`/admin/notifications`) and delivered only after explicit review and approval by an operations admin, eliminating false-positive broadcast spam.

---

## 14. Dynamic Network & Line Diagnostics

To provide actionable value beyond text chatting, the platform incorporates an on-demand network telemetry engine (`/api/chat/diagnostic`).

### 14.1 Telemetry Diagnostic Schema

| Metric | Healthy Range (Broadband/Fiber) | Healthy Range (Mobile Data) | Degraded Range (Active Incident) |
| :--- | :--- | :--- | :--- |
| **Download Speed** | $94.0 - 298.0\text{ Mbps}$ | $35.0 - 78.0\text{ Mbps}$ | $1.5 - 12.0\text{ Mbps}$ |
| **Upload Speed** | $88.0 - 290.0\text{ Mbps}$ | $15.0 - 32.0\text{ Mbps}$ | $0.5 - 4.0\text{ Mbps}$ |
| **Ping Latency** | $12.0 - 28.0\text{ ms}$ | $22.0 - 45.0\text{ ms}$ | $120.0 - 280.0\text{ ms}$ |
| **Jitter** | $1.2 - 4.5\text{ ms}$ | $3.5 - 8.0\text{ ms}$ | $25.0 - 65.0\text{ ms}$ |
| **Packet Loss** | $0.0\%$ | $0.0 - 0.5\%$ | $8.0 - 22.0\%$ |
| **Line Health** | **Optimal / Healthy** | **Optimal / Healthy** | **Degraded (Incident Linked)** |

Telemetry results are rendered as interactive visual cards in the chat stream and read out via speech synthesis.

---

## 15. Backend REST API Specifications

| Method | Endpoint | Access Role | Description & Functionality |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/auth/login` | Public | Authenticates customer or admin; returns JWT token. |
| `POST` | `/api/auth/signup` | Public | Customer self-registration with region and service selection. |
| `GET` | `/api/auth/me` | Authenticated | Retrieves current authenticated user profile. |
| `POST` | `/api/chat` | Customer | Customer conversational endpoint executing LangGraph StateGraph. |
| `GET` | `/api/chat/history` | Customer | Retrieves customer conversation message history. |
| `POST` | `/api/chat/diagnostic` | Customer | Runs dynamic line speed and connectivity diagnostics. |
| `POST` | `/api/chat/voice` | Customer | Multilingual voice transcription via Groq Whisper. |
| `GET` | `/api/my/tickets` | Customer | Lists authenticated customer's own tickets. |
| `GET` | `/api/my/tickets/{id}/history` | Customer | Status history timeline for a specific owned ticket. |
| `GET` | `/api/my/notifications` | Customer | In-app notification feed for the authenticated customer. |
| `POST` | `/api/admin/upload/preview` | Admin | Analyzes uploaded CSV and returns suggested column mappings. |
| `POST` | `/api/admin/upload/ingest` | Admin | Ingests CSV with mapping, runs ETL, ML scoring, and spike engine. |
| `GET` | `/api/admin/analytics/summary` | Admin | High-level metrics, volume time series, category donuts, sentiment. |
| `GET` | `/api/admin/analytics/risk` | Admin | Ranked escalation risk table with contributing factor chips. |
| `GET` | `/api/admin/queue` | Admin | Filterable, paginated complaint queue with ticket summaries. |
| `PATCH` | `/api/admin/complaints/{id}` | Admin | Updates ticket status, assigned team, and customer-visible notes. |
| `POST` | `/api/admin/complaints/{id}/propose-resolution` | Admin | Proposes technical fix (`resolved_pending_confirmation`). |
| `GET` | `/api/admin/heatmap` | Admin | Regional complaint density and spike data for Leaflet map. |
| `GET` | `/api/admin/incidents` | Admin | Lists active and historical outage incidents. |
| `POST` | `/api/admin/incidents/{id}/ack` | Admin | Acknowledges incident and assigns field engineering teams. |
| `POST` | `/api/admin/incidents/{id}/resolve` | Admin | Marks incident resolved and closes linked complaint tickets. |
| `GET` | `/api/admin/alerts` | Admin | Real-time spike alert inbox for operations admins. |
| `GET` | `/api/admin/notifications/queue`| Admin | Review queue for drafted broadcast notifications. |
| `POST` | `/api/admin/notifications/{id}/approval` | Admin | Approves or rejects proactive broadcast notifications. |
| `POST` | `/api/admin/assistant/chat` | Admin | Admin AI Assistant endpoint executing LangGraph Operations Agent. |
| `GET` | `/api/admin/audit` | Admin | Tamper-evident audit logs capturing all privileged actions. |
| `GET` | `/api/admin/export.csv` | Admin | Exports current filtered complaints to downloadable CSV. |

---

## 16. Free / Zero-Cost AI & API Strategy

The entire architecture is engineered to run on **100% free-tier or local open-source components**:

| Component | Technology Choice | Operational Role & Free-Tier Limits |
| :--- | :--- | :--- |
| **Generative LLM** | Groq Cloud API (`llama-3.3-70b-versatile`) | Fast conversational generation, summaries, root-cause narratives (Free Tier). |
| **Speech Recognition** | Groq Whisper (`whisper-large-v3-turbo`) | Multilingual voice transcription (Free Tier). |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local CPU vector embeddings (Zero API cost). |
| **Vector Store** | ChromaDB Persistent Client | Local embedded vector database (Zero API cost). |
| **Multilingual Tokenizer** | Hugging Face Multilingual DistilBERT | Local CPU tokenization & language normalization (Zero API cost). |
| **ML Classification** | scikit-learn (`TF-IDF + LogisticRegression`) | Local CPU classification & scoring (Zero API cost). |
| **Geocoding** | Geoapify Geocoding API | Free Tier geocoding with dynamic in-memory caching. |
| **Database** | SQLite 3 (WAL Mode) | Serverless relational database (Zero infrastructure cost). |

### 16.1 Deterministic Offline Fallback Protocol
Every external API call (Groq LLM, Whisper STT, Geoapify Geocoding) includes an immediate, deterministic offline fallback. If API keys are missing or rate limits are reached, TelConnect continues operating with full feature parity using rule-based text generation, lexical translations, and built-in geocodes.

---

## 17. Non-Functional Requirements & AI Safety

### 17.1 Non-Functional Requirements
- **Performance**: Customer chat API latency $\le 1.5\text{s}$ on live LLM, $\le 50\text{ms}$ on offline fallback.
- **Availability**: System operates independently of external API uptime via deterministic fallbacks.
- **Security**: Password hashing via scrypt/PBKDF2, signed JWT tokens, role-based route guards.
- **Privacy & PII Protection**: Customer phone numbers, emails, and names are stripped or masked during ingestion before storage or LLM prompting.
- **Explainability**: No raw numeric black-box scores; all ML outputs expose contributing factor chips and evidence bullets.
- **Auditability**: All privileged operations, status changes, assignments, and approvals are logged immutably.

### 17.2 AI Safety Rules
1. **Never fabricate live ticket status or ticket IDs**.
2. **Never claim an outage is confirmed when it is only an unverified AI hypothesis**.
3. **Never silently close a ticket without explicit customer confirmation**.
4. **Never expose one customer's private data or ticket history to another customer**.
5. **Never execute privileged database mutations directly from unvalidated LLM output**.

---

## 18. Technology Stack & Separation of Responsibilities

```
TelConnect Full-Stack Architecture
├── Presentation: React 18/19, Vite, React Router v7, Leaflet, React-Leaflet, Recharts, ThemeEngine
├── Backend API: Python 3.10+, FastAPI, Uvicorn, Pydantic
├── Agent Framework: LangGraph StateGraph (Multi-Task State Machines)
├── Vector DB: ChromaDB PersistentClient, Sentence-Transformers (all-MiniLM-L6-v2)
├── Multilingual NLP: Hugging Face Transformers (distilbert-base-multilingual-cased)
├── AI & Speech: Groq API (Llama-3, Whisper) with Deterministic Offline Fallback
├── Geocoding: Geoapify Geocoding REST API (Cached)
├── Operational DB: SQLite 3 (WAL Mode)
└── Testing Suite: Pytest, HTTPX, FastAPI TestClient (106+ Tests)
```

### 18.1 Separation of Responsibilities

| System Component | Must Do | Must NOT Do |
| :--- | :--- | :--- |
| **SQLite (`tci.db`)** | Store authoritative live operational state and audit history. | Generate natural language text. |
| **ChromaDB** | Index and retrieve dense semantic SOPs and resolution knowledge. | Store live ticket status. |
| **scikit-learn ML** | Score categories, sentiment, urgency, escalation risk, and priority. | Execute database writes directly. |
| **Groq LLM** | Synthesize natural language, explanations, and empathetic summaries. | Invent ticket IDs or mutate state without APIs. |
| **FastAPI Backend** | Authenticate, authorize, and execute deterministic state transitions. | Rely on LLM text for authorization decisions. |
| **Admin Console** | Provide operational control, triage queues, heatmaps, and audit logs. | Bypass backend validation or security checks. |

---

## 19. Testing & Acceptance Criteria

### 19.1 Acceptance Scenarios

| Scenario | Acceptance Criteria |
| :--- | :--- |
| **New Complaint Intake** | Customer describes issue $\to$ assistant collects details $\to$ user confirms $\to$ ticket registered in SQLite. |
| **Known Outage Interception** | Assistant matches active geo-incident $\to$ explains root cause $\to$ links report without duplicate ticket. |
| **RAG Troubleshooting** | Assistant retrieves approved SOP $\to$ guides user $\to$ requests confirmation of resolution. |
| **Confirm-to-Close Loop** | Customer confirms fix (`Yes ✓`) $\to$ ticket closes $\to$ CSAT rating recorded. Customer rejects (`No ✗`) $\to$ reopens & escalates. |
| **Dynamic Line Diagnostic** | Customer requests speed test $\to$ telemetry card rendered in stream $\to$ voice TTS summary readout. |
| **Multilingual Interaction** | Hindi/Hinglish text $\to$ normalized by DistilBERT $\to$ accurately classified $\to$ replies in Devanagari script. |
| **Admin AI Decision Support** | Admin asks operational questions $\to$ LangGraph Agent synthesizes live DB metrics and ChromaDB SOPs. |
| **Spike Detection & Dossier** | Simulated surge $\to$ anomaly detector fires $\to$ red heatmap alert $\to$ evidence dossier generated. |
| **Human-in-the-Loop Broadcast** | Incident detected $\to$ notifications drafted $\to$ delivered only upon explicit admin approval. |
| **API Auth & Data Isolation** | Customer cannot access another user's tickets even with valid ticket IDs. |
| **Offline Resilience** | Backend functions and tests pass with zero external API keys. |

### 19.2 Target KPIs & Validated Results

| KPI Metric | Benchmark Target | Implemented & Validated Result |
| :--- | :---: | :---: |
| **Category Macro-F1 Score** | $\ge 80.0\%$ | **$\ge 82.4\%$** (Held-out test split) |
| **Intent Routing Accuracy** | $\ge 90.0\%$ | **$\ge 95.0\%$** across 15+ conversational intents |
| **Ticket State Integrity** | $100\%$ | **$100\%$** (Strict transition constraints in SQLite) |
| **Customer Data Isolation** | $100\%$ | **$100\%$** (Role-based JWT verification on all routes) |
| **Automated Test Suite** | $100\%$ Pass Rate | **106+ Tests Passing** in `backend/tests/` |
| **Zero-Cost Operation** | $100\%$ Free Tier | Operates on free-tier APIs and offline local fallbacks |

---

## 20. Implementation Plan & Minimum Successful Demo

### 20.1 Implementation Phases

| Phase | Milestone Description |
| :---: | :--- |
| **Phase 1** | SQLite schema design, connection management, demo account seeding, and role-based JWT auth. |
| **Phase 2** | Universal CSV ingestion engine, auto-schema detection, and PII redaction pipeline. |
| **Phase 3** | scikit-learn ML models: category classifier, sentiment, urgency, escalation risk, and multi-factor priority. |
| **Phase 4** | ChromaDB vector store setup, SentenceTransformer embeddings, and SOP indexing. |
| **Phase 5** | LangGraph Customer Agent (6-node StateGraph) and dynamic line diagnostics engine. |
| **Phase 6** | LangGraph Admin Operations Agent (4-node StateGraph) and decision support cockpit. |
| **Phase 7** | Rolling-baseline spike detector, Leaflet geographic heatmap, and AI root-cause investigator. |
| **Phase 8** | Proactive notification approval queue and in-app transactional notification feed. |
| **Phase 9** | React frontend: 40/60 chat split, admin cockpit, Dark/Light theme engine, and test validation. |

### 20.2 Minimum Successful Demo Script

1. **Admin Ingest**: Admin logs in, uploads demo CSV via 3-step wizard, and confirms schema mapping.
2. **Operations Cockpit**: Admin inspects live KPIs, outage volume spike, and priority-ranked risk table.
3. **Network Heatmap**: Admin views Raj Nagar glowing red and navigates to the incident dossier.
4. **Root-Cause Dossier**: Admin inspects $92\%$ confidence cause, 5 evidence bullets, acknowledges, and drafts notifications.
5. **Notify Queue**: Admin approves drafted broadcast notifications.
6. **Admin AI Assistant**: Admin queries *"Which complaints need immediate attention?"* and receives structured intelligence.
7. **Customer Closed Loop**: Customer logs in, sees proactive banner, runs line speed test, describes issue in Hinglish, experiences incident-aware interception without duplicate tickets, and verifies resolution in the confirm-to-close loop.

---

## 21. Product Differentiation

| Feature / Dimension | Traditional Telecom Ticketing | Basic Generative Chatbots | **TelConnect Platform** |
| :--- | :--- | :--- | :--- |
| **Resolution Focus** | Creates static, passive tickets. | Generates generic, unverified text. | **Autonomous closed-loop resolution with verification.** |
| **Network Telemetry** | Requires separate speed test apps. | Cannot test physical lines. | **On-demand line & speed diagnostics inside chat.** |
| **Multilingual NLP** | Rigid keyword matching. | Prone to Hindi transliteration errors. | **Hugging Face DistilBERT + Groq Neural Translation.** |
| **Operational Linkage** | Disconnected from call centers. | No operational backend. | **Direct integration with NOC heatmap & spike alerts.** |
| **Outage Detection** | Discovered after hundreds of calls. | None. | **Real-time rolling baseline anomaly detection.** |
| **Root-Cause Analysis** | Manual post-mortem analysis. | Speculative hallucinations. | **Evidence-backed dossiers with confidence metrics.** |
| **Proactive Comms** | Uncontrolled mass SMS blasts. | None. | **Human-in-the-loop review and approval queue.** |
| **Operational Cost** | Expensive enterprise licenses. | High per-token API costs. | **100% Free-Tier & Zero-Cost Architecture.** |

### 21.1 Final Product Definition
**A unified telecom operations and customer resolution platform that merges conversational support, dynamic network diagnostics, grounded vector RAG, and live ticket tracking with operational intelligence—including classification, sentiment, escalation prediction, geographic heatmaps, automated spike detection, AI root-cause dossiers, and proactive notification.**

---

## 22. Recommended Presentation Flow

| Scene | Demonstration Action | Key Message to Judges |
| :--- | :--- | :--- |
| **1. Customer Inconvenience** | Customer reports broadband failure in Hindi/Hinglish. | True multilingual understanding without form fatigue. |
| **2. Dynamic Telemetry** | Customer triggers instant line speed diagnostic. | Real-time diagnostic capability inside conversational UI. |
| **3. Incident Interception** | Assistant links complaint to active outage with plain-English ETA. | Prevents duplicate ticket flooding and calms subscribers. |
| **4. Grounded RAG Fix** | Customer receives approved SOP steps for self-service fix. | First-Contact Resolution without human intervention. |
| **5. Confirm-to-Close** | Customer verifies fix (`Yes ✓`) and rates interaction 5 stars. | Closed-loop accountability; nothing closes silently. |
| **6. Admin Cockpit** | Admin monitors priority queue, SLA countdowns, and risk tables. | Single source of truth across all operations. |
| **7. Anomaly & Heatmap** | Leaflet heatmap highlights red outage surge in real time. | Transforms complaints into proactive network alerts. |
| **8. Root-Cause Dossier** | AI presents evidence-backed cause with $92\%$ confidence. | Explainable AI backed by empirical data signals. |
| **9. Proactive Broadcast** | Admin reviews and approves drafted customer notifications. | Human-in-the-loop safety prevents false broadcasts. |
| **10. Admin AI Assistant** | Admin asks complex NOC operational questions. | Autonomous decision support for network operations. |

---

## 23. Risks & Mitigations

| Identified Risk | Risk Severity | Implemented Mitigation Strategy |
| :--- | :---: | :--- |
| **Groq API Rate Limits (429)** | Medium | In-process caching, efficient prompt sizing, and 100% deterministic offline fallback. |
| **LLM Hallucinations** | High | Strict verified facts compile step, ChromaDB RAG grounding, zero unverified state mutations. |
| **False Root Cause Claims** | Medium | Multi-signal evidence threshold ($\ge 3$ signals required); output labeled as hypothesis until verified. |
| **Duplicate Ticket Ingestion** | Low | Universal CSV ingestion deduplication and active incident auto-linking. |
| **PII Data Leakage** | High | Automatic regex redaction of phone numbers, emails, and names during ingestion. |
| **Stale Ticket Memory** | Medium | Always query live SQLite database (`tci.db`) for ticket state. |

---

## 24. Requirements Traceability to Use Case 13

| Use Case 13 Requirement | PRD v7.0 Implementation Details |
| :--- | :--- |
| **Complaint Classification** | `TF-IDF + LogisticRegression` category model ($\ge 82.4\%$ macro-F1). |
| **Sentiment & Urgency Detection** | Lexicon & rule-based sentiment model with negative polarity weighting. |
| **Priority Scoring ($P1 - P4$)** | Multi-factor explainable formula with SLA deadlines and contributing factor chips. |
| **Escalation Risk Prediction** | Multi-factor churn and regulatory threat detection model. |
| **Resolution Recommendation** | ChromaDB vector store + Sentence Transformers dense retrieval over approved SOPs. |
| **Ticket Summaries** | One-sentence plain-language summaries generated by Groq / template fallback. |
| **Conversational Assistant** | LangGraph 6-Node Customer Multi-Task StateGraph with voice STT / TTS. |
| **Vector DB / RAG** | ChromaDB persistent vector database with cosine similarity indexing. |
| **Root-Cause Intelligence** | Multi-signal anomaly detector, Leaflet heatmap, and evidence dossiers. |
| **Operational Dashboard** | 16-module Admin Operations Cockpit with Admin AI Assistant. |
| **Customer Experience** | 40/60 split UI, dynamic line diagnostics, status tracking, confirm-to-close loop. |

---

## 25. Conclusion & Appendix

This PRD establishes a complete, enterprise-grade product architecture that bridges customer service and network operations into a unified system.

> **The ultimate strength of TelConnect is not simply that a chatbot can reply to a message. It is that the system understands the customer's problem, attempts grounded resolution, tracks live ticket states transparently, verifies satisfaction, and simultaneously analyzes complaint patterns across the network to detect, investigate, and proactively resolve mass outages.**

---
*TelConnect Engineering Team • Cognizant Hackathon (Use Case 13)*
