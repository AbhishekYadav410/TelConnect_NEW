# TelConnect Production Deployment Guide: Vercel (Frontend) & Railway (Backend)

This guide provides step-by-step instructions for deploying the **TelConnect** platform:
- **Frontend**: [Vercel](https://vercel.com) (React 19 / Vite SPA on global edge CDN)
- **Backend**: [Railway](https://railway.com) (FastAPI + ChromaDB + PyTorch running on 1 GB RAM & 2 vCPUs)
- **Database**: Embedded SQLite (`tci.db` with WAL mode) + ChromaDB Vector Store

---

## 1. Hardware Feasibility & Resource Allocation

| Platform Component | RAM Usage | Status on Railway (1 GB RAM & 2 vCPUs) |
| :--- | :--- | :--- |
| **FastAPI + Uvicorn Core** | ~50 – 60 MB | Runs on `$PORT` in single-worker mode |
| **SQLite (`tci.db`)** | ~20 – 30 MB | In-process connection pooling |
| **Scikit-Learn Classifiers** | ~30 – 50 MB | Pre-trained joblib vectorizers & models |
| **ChromaDB + SentenceTransformers** | ~140 – 180 MB | `all-MiniLM-L6-v2` dense embedding model |
| **Multilingual DistilBERT** | ~260 – 320 MB | CPU inference singleton loaded on-demand |
| **Linux Container Overhead** | ~40 – 60 MB | Debian/Alpine runtime |
| **Total Estimated Peak RAM** | **~550 – 650 MB** | **~350 – 450 MB safe headroom remaining inside 1 GB RAM** |

---

## 2. Deployment Sequence Overview

```
[1. Deploy Backend on Railway] ────> Obtain Railway URL (e.g., https://telconnect-production.up.railway.app)
              │
              ▼
[2. Deploy Frontend on Vercel] ────> Set VITE_API_URL = Railway URL ────> Obtain Vercel URL
              │
              ▼
[3. Connect CORS on Railway]  ────> Set CORS_ORIGINS = Vercel URL
              │
              ▼
[4. Live Verification Test]   ────> Test Customer Chat, Diagnostics & Admin Dashboard
```

---

## Step 1: Deploy Backend on Railway

1. Sign up / Log in to [Railway](https://railway.com/) (Sign in with GitHub).
2. On your Railway dashboard, click **+ New Project**.
3. Select **Deploy from GitHub repo**.
4. Choose your repository: `AbhishekYadav410/TelConnect_NEW`.
5. In the project canvas, click on the newly created service box to open its settings:
   - Go to the **Settings** tab:
     - **Service Name**: `telconnect-backend` (or your preferred name)
     - **Root Directory**: `backend`
     - **Build Command**: Leave default (Railway Nixpacks automatically detects Python and runs `pip install -r requirements.txt`)
     - **Start Command**: `uvicorn app.routes.main:app --host 0.0.0.0 --port $PORT`
     - **Healthcheck Path**: `/healthz`
     - **Healthcheck Timeout**: `120`
6. Go to the **Variables** tab and add the environment variables:

| Variable Name | Value | Description |
| :--- | :--- | :--- |
| `PORT` | `8000` | Fallback port (Railway dynamically injects `$PORT`) |
| `GROQ_API_KEY` | `gsk_...` | *(Optional)* Your free Groq API key from https://console.groq.com |
| `GEOAPIFY_API_KEY` | `...` | *(Optional)* Your free Geoapify key from https://www.geoapify.com |
| `CORS_ORIGINS` | `http://localhost:5173` | *(Temporary &mdash; you will update this in Step 3)* |
| `TCI_DISABLE_SCHEDULER` | `0` | Enables background incident analysis |

7. **Generate Public Domain**:
   - In the service view, go to **Settings** &rarr; **Networking** (or **Public Networking**).
   - Click **Generate Domain**.
   - Railway will provide a public URL such as `https://telconnect-backend-production.up.railway.app`.
8. Copy your Railway backend URL.
9. Test the backend by visiting `https://your-backend.up.railway.app/healthz` in your browser. You should receive:
   ```json
   {
     "status": "ok",
     "service": "TelConnect Backend",
     "groq_live": true,
     "ingest_done": true
   }
   ```

---

## Step 2: Deploy Frontend on Vercel

1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** &rarr; **Project**.
3. Import your GitHub repository: `https://github.com/AbhishekYadav410/TelConnect_NEW`.
4. In the **Configure Project** screen:
   - **Project Name**: `telconnect-app` (or preferred name)
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** &rarr; select `frontend` &rarr; click **Continue**.
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
   - **Install Command**: `npm install` (default)
5. Expand **Environment Variables** and add:

| Name | Value | Description |
| :--- | :--- | :--- |
| `VITE_API_URL` | `https://your-backend.up.railway.app` | Your live Railway backend URL from Step 1 (no trailing slash) |

6. Click **Deploy**.
7. Once deployed, note your live Vercel domain (e.g., `https://telconnect-app.vercel.app`).

---

## Step 3: Connect Frontend URL to Backend CORS on Railway

1. Return to your [Railway Dashboard](https://railway.com/).
2. Open your `telconnect-backend` service.
3. Go to the **Variables** tab.
4. Update `CORS_ORIGINS`:
   ```text
   https://telconnect-app.vercel.app,http://localhost:5173
   ```
5. Railway will automatically redeploy the service in a few seconds.

---

## Step 4: Verification & Smoke Test

1. **Landing Page**: Open your Vercel URL (`https://telconnect-app.vercel.app`).
2. **Customer Chat Flow**:
   - Sign in with demo customer credentials:
     - **Email**: `customer@telconnect.com`
     - **Password**: `demo123`
   - Test conversational complaint reporting in English, Hindi, and Hinglish.
   - Run a line speed telemetry test (*"run speed test"*).
3. **Admin Operations Cockpit**:
   - Sign in with demo admin credentials:
     - **Email**: `admin@telconnect.com`
     - **Password**: `demo123`
   - Check the **Operations Overview** metrics and volume charts.
   - Open **Complaint Queue** to triage priority tickets ($P1 - P4$).
   - Check the interactive **Network Heatmap** and active outage dossiers.
   - Open the **Admin AI Assistant** (`/admin/assistant`) and ask operational questions.
   - Review and approve broadcast notifications in the **Notify Queue**.

---

## Summary of Environment Variables

### Backend (Railway)
```env
PORT=8000
CORS_ORIGINS=https://your-frontend.vercel.app,http://localhost:5173
GROQ_API_KEY=gsk_your_groq_api_key
GEOAPIFY_API_KEY=your_geoapify_key
TCI_DISABLE_SCHEDULER=0
```

### Frontend (Vercel)
```env
VITE_API_URL=https://your-backend.up.railway.app
```
