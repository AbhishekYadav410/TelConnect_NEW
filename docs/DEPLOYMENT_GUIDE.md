# TelConnect Deployment Guide: Vercel (Frontend) & Render (Backend)

This guide provides step-by-step instructions for deploying the **TelConnect** platform to production:
- **Frontend**: [Vercel](https://vercel.com) (Fast, global CDN with SPA routing & security headers)
- **Backend**: [Render](https://render.com) (Fully managed Python service with automatic health checks & persistent ML inference)

---

## Architecture Overview

```
[Customer / Admin Browser]
           │
           ├─── HTTPS (Global Edge CDN) ───> [Vercel: React 19 Frontend SPA]
           │                                            │
           │                                   VITE_API_URL (HTTPS)
           │                                            │
           └──── REST APIs / WebSockets ───────────────> [Render: FastAPI + Uvicorn Backend]
                                                                ├── SQLite (tci.db with WAL mode)
                                                                ├── ChromaDB Vector Store
                                                                ├── ML Models (scikit-learn, DistilBERT)
                                                                └── External APIs (Groq, Geoapify)
```

---

## Prerequisites

1. **GitHub Repository**: Your project is hosted at `https://github.com/AbhishekYadav410/TelConnect_NEW`
2. **Vercel Account**: Free account at [vercel.com](https://vercel.com) (Sign in with GitHub)
3. **Render Account**: Free account at [render.com](https://render.com) (Sign in with GitHub)
4. **API Keys (Free Tier)**:
   - **Groq API Key**: Free key from [console.groq.com](https://console.groq.com/keys) (Optional; offline fallbacks engage automatically if omitted)
   - **Geoapify API Key**: Free key from [geoapify.com](https://www.geoapify.com/) (Optional; cached coordinates used if omitted)

---

## Step 1: Deploy Backend on Render

Deploy the FastAPI backend first so you have the production backend URL ready for the frontend.

### Option A: Using the Render Blueprint (`render.yaml`) — Recommended

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** in the top navigation bar and select **Blueprint**.
3. Connect your GitHub repository: `AbhishekYadav410/TelConnect_NEW`.
4. Render will automatically detect `render.yaml` at the root of the repository.
5. In the configuration screen:
   - Enter your `GROQ_API_KEY` (optional).
   - Enter your `GEOAPIFY_API_KEY` (optional).
   - Leave `CORS_ORIGINS` blank for now (you will update it after creating the Vercel deployment).
6. Click **Apply**.
7. Render will build and deploy the backend service. Once deployed, note your service URL (e.g. `https://telconnect-backend.onrender.com`).

---

### Option B: Manual Web Service Setup on Render

If you prefer to configure the Web Service manually:

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Choose **Build and deploy from a Git repository** and select `AbhishekYadav410/TelConnect_NEW`.
4. Configure the service settings:
   - **Name**: `telconnect-backend` (or your preferred name)
   - **Region**: Closest to your users (e.g. *Singapore* or *Frankfurt*)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.routes.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Open **Advanced** settings:
   - **Health Check Path**: `/healthz`
   - **Auto-Deploy**: `Yes`
6. Add **Environment Variables**:

| Variable Name | Value | Purpose |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Optimal Python runtime version |
| `TCI_DISABLE_SCHEDULER` | `0` | Enables background incident analysis |
| `TCI_SCHEDULER_INTERVAL` | `60` | Periodic background cycle (seconds) |
| `GROQ_API_KEY` | `gsk_...` | Groq API key for Llama-3 & Whisper |
| `GEOAPIFY_API_KEY` | `...` | Geoapify key for geolocation |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed origins (update after Vercel deploy) |

7. Click **Create Web Service**. Wait for the build log to display:
   ```text
   Application startup complete.
   Uvicorn running on http://0.0.0.0:10000
   ```
8. Copy your backend URL (e.g. `https://telconnect-backend.onrender.com`).
9. Test the backend by visiting `https://telconnect-backend.onrender.com/healthz` in your browser. You should receive:
   ```json
   {
     "status": "healthy",
     "service": "TelConnect Backend",
     "groq_live": true,
     "ingest_done": true
   }
   ```

---

## Step 2: Deploy Frontend on Vercel

1. Log in to [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** and select **Project**.
3. Import your GitHub repository: `AbhishekYadav410/TelConnect_NEW`.
4. In the **Configure Project** screen:
   - **Project Name**: `telconnect-app` (or your preferred name)
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** and select `frontend` (Click **Continue**)
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
   - **Install Command**: `npm install` (default)
5. Expand **Environment Variables** and add:

| Name | Value | Description |
| :--- | :--- | :--- |
| `VITE_API_URL` | `https://telconnect-backend.onrender.com` | Your Render backend URL (no trailing slash) |

6. Click **Deploy**.
7. Vercel will build the frontend and provide your live production domain (e.g., `https://telconnect-app.vercel.app`).

---

## Step 3: Connect Frontend Domain to Backend CORS

To ensure strict security and prevent Cross-Origin Request Blocked errors:

1. Return to your [Render Dashboard](https://dashboard.render.com).
2. Open your `telconnect-backend` service.
3. Go to the **Environment** tab.
4. Update or add `CORS_ORIGINS`:
   ```text
   https://telconnect-app.vercel.app,http://localhost:5173
   ```
5. Click **Save Changes**. Render will automatically redeploy the backend with the updated CORS policy.

---

## Step 4: Verification & Live Smoke Test

Once both services are deployed, test the complete workflow:

1. **Landing Page**: Open your Vercel URL (`https://telconnect-app.vercel.app`).
2. **Customer Chat**:
   - Log in using demo credentials:
     - **Email**: `customer@telconnect.com`
     - **Password**: `demo123`
   - Test conversational reporting in English and Hindi/Hinglish (*"Mera internet band ho gaya hai"*).
   - Test dynamic line speed diagnostics (*"run speed test"*).
   - Verify that interactive telemetry cards render and voice TTS plays correctly.
3. **Admin Operations Cockpit**:
   - Sign in as Admin:
     - **Email**: `admin@telconnect.com`
     - **Password**: `demo123`
   - Inspect the **Operations Overview** metrics and volume charts.
   - Open **Complaint Queue** to triage priority-ranked tickets ($P1 - P4$).
   - Check the interactive **Network Heatmap** and active outage dossiers.
   - Open the **Admin AI Assistant** (`/admin/assistant`) and ask operational questions.
   - Review and approve broadcast notifications in the **Notify Queue**.

---

## Security & Reliability Precautions Taken

- **Zero-Secret Exposure**: No `.env` secrets or API credentials are included in the source code; all secrets are managed via cloud environment variables.
- **Dynamic CORS Protection**: The backend only responds to authorized origins (your Vercel production domain, preview branches `https://*.vercel.app`, and local development).
- **SPA Routing Rewrites**: `frontend/vercel.json` rewrites all direct page navigations to `/index.html` to prevent 404 errors on browser refreshes.
- **Offline & Rate-Limit Resilience**: If Groq API keys are absent, rate-limited, or temporarily offline, all text generation, translation, and classification features gracefully fall back to local rule-based engines.
- **Database Self-Healing**: On Render instance restarts or cold boots, SQLite (`tci.db`) and ChromaDB vector indices automatically self-initialize and load demo data with zero manual database administration.
- **PII Scrubbing**: Uploaded CSV files and customer messages undergo regex PII masking (names, phone numbers, email addresses) before persistent storage.

---

## Summary of Environment Variables

### Backend (Render)
```env
PYTHON_VERSION=3.11.9
PORT=10000
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
GROQ_API_KEY=gsk_your_groq_api_key
GEOAPIFY_API_KEY=your_geoapify_key
TCI_DISABLE_SCHEDULER=0
TCI_SCHEDULER_INTERVAL=60
```

### Frontend (Vercel)
```env
VITE_API_URL=https://your-backend.onrender.com
```
