# TelConnect Production Deployment Guide: Vercel & Hugging Face Spaces

This guide walks you through the step-by-step production deployment of **TelConnect**:
- **Frontend**: [Vercel](https://vercel.com) (React 19 / Vite SPA on global edge CDN)
- **Backend**: [Hugging Face Spaces](https://huggingface.co/spaces) (FastAPI + ChromaDB + PyTorch on Docker, port 7860)
- **Database**: Embedded SQLite (`tci.db`) + ChromaDB Vector Store

---

## Architecture Overview

```
[Customer / Admin Browser]
           │
           ├─── HTTPS (Global Edge CDN) ───> [Vercel: React 19 Frontend SPA]
           │                                            │
           │                                   VITE_API_URL (HTTPS)
           │                                            │
           └──── REST APIs / WebSockets ───────────────> [Hugging Face Spaces: Docker Container]
                                                                ├── Port: 7860
                                                                ├── Non-root User: UID 1000
                                                                ├── SQLite (tci.db with WAL mode)
                                                                ├── ChromaDB Vector Store
                                                                └── ML Models (scikit-learn, DistilBERT)
```

---

## Deployment Sequence Summary

1. **Deploy Frontend to Vercel** &rarr; Obtain Vercel production domain (`https://<project-name>.vercel.app`).
2. **Deploy Backend to Hugging Face Spaces** &rarr; Set `CORS_ORIGINS` to your Vercel URL; obtain Hugging Face Space URL (`https://<username>-<space-name>.hf.space`).
3. **Update Frontend Environment Variable** on Vercel (`VITE_API_URL`) &rarr; Redeploy frontend.
4. **Run Validation Tests** &rarr; Verify customer chat, voice, diagnostics, admin cockpit, and cold-start wake states.

---

## Step 1: Deploy Frontend on Vercel

1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **Add New...** &rarr; **Project**.
3. Import your GitHub repository: `https://github.com/AbhishekYadav410/TelConnect_NEW`.
4. Configure project settings:
   - **Project Name**: `telconnect-app` (or your preferred name)
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** &rarr; select `frontend` &rarr; click **Continue**.
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `dist` (default)
   - **Install Command**: `npm install` (default)
5. Under **Environment Variables**, add a temporary placeholder:
   - `VITE_API_URL` = `https://placeholder.hf.space` *(you will update this with the real HF Spaces URL in Step 3)*
6. Click **Deploy**.
7. Once deployed, note your live Vercel domain (e.g., `https://telconnect-app.vercel.app`).

---

## Step 2: Deploy Backend to Hugging Face Spaces

### Option A: Create Space via Hugging Face Web UI (Recommended)

1. Log in to [Hugging Face](https://huggingface.co) and go to [New Space](https://huggingface.co/new-space).
2. Configure your Space:
   - **Space Name**: `telconnect-backend` (or preferred name)
   - **License**: `mit` / `apache-2.0`
   - **Select the Space SDK**: Choose **Docker** &rarr; **Blank**.
   - **Space Hardware**: `CPU basic (2 vCPU, 16 GB RAM)` &mdash; **Free**.
   - **Visibility**: `Public` (recommended for frontend API connectivity).
3. Click **Create Space**.
4. In your new Space, navigate to the **Settings** tab:
   - Scroll down to **Variables and secrets**.
   - Under **Secrets**, add:
     - `GROQ_API_KEY`: *(your free Groq API key from https://console.groq.com - optional)*
     - `GEOAPIFY_API_KEY`: *(your free Geoapify key from https://www.geoapify.com - optional)*
   - Under **Variables**, add:
     - `CORS_ORIGINS`: `https://telconnect-app.vercel.app,http://localhost:5173` *(your Vercel URL from Step 1)*
     - `PORT`: `7860`
5. Connect your GitHub repository or push to the Space's Git remote:
   ```bash
   # Add Hugging Face Space remote
   git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/telconnect-backend

   # Push to Space
   git push space main
   ```
6. Hugging Face Spaces will automatically build the `Dockerfile` and start the server.
7. Verify backend health by visiting:
   `https://<YOUR_HF_USERNAME>-telconnect-backend.hf.space/health`
   You should receive:
   ```json
   {
     "status": "healthy"
   }
   ```

---

## Step 3: Connect Frontend to Backend

1. Return to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Open your `telconnect-app` project.
3. Go to **Settings** &rarr; **Environment Variables**.
4. Edit `VITE_API_URL` and set its value to your live Hugging Face Space URL:
   ```text
   https://<YOUR_HF_USERNAME>-telconnect-backend.hf.space
   ```
   *(Note: Do not include a trailing slash)*.
5. Go to the **Deployments** tab, click the three dots on your latest deployment, and select **Redeploy**.

---

## Step 4: Verification & Smoke Test

1. **Open Frontend**: Navigate to your Vercel URL (`https://telconnect-app.vercel.app`).
2. **Cold-Start Resilience Test**:
   - If the Hugging Face Space is sleeping, a floating top banner will display:
     `Initializing AI services... Please wait a few moments.`
   - As soon as the container finishes booting, the banner smoothly disappears and normal operation resumes.
3. **Customer Reporting**:
   - Sign in with demo customer credentials:
     - **Email**: `customer@telconnect.com`
     - **Password**: `demo123`
   - Test conversational complaint intake, Hindi/Hinglish translations, line speed telemetry diagnostics, and ticket creation.
4. **Admin Intelligence Cockpit**:
   - Sign in with demo admin credentials:
     - **Email**: `admin@telconnect.com`
     - **Password**: `demo123`
   - Test the Operations Overview, Interactive Network Heatmap, Priority Queue ($P1 - P4$), Outage Dossiers, AI Operations Assistant (`/admin/assistant`), and Notification Queue.

---

## Environment Variables Reference

### Backend (Hugging Face Spaces Secrets & Variables)
| Variable | Default / Example | Required | Purpose |
| :--- | :--- | :--- | :--- |
| `PORT` | `7860` | Yes | Standard port for Hugging Face Spaces |
| `CORS_ORIGINS` | `https://telconnect-app.vercel.app,http://localhost:5173` | Yes | Authorized frontend domains |
| `GROQ_API_KEY` | `gsk_...` | Optional | Llama-3 & Whisper voice fallback |
| `GEOAPIFY_API_KEY` | `...` | Optional | Geocoding fallback |
| `TCI_DISABLE_SCHEDULER` | `0` | No | Background incident clustering |

### Frontend (Vercel Environment Variables)
| Variable | Value | Required | Purpose |
| :--- | :--- | :--- | :--- |
| `VITE_API_URL` | `https://<username>-<space>.hf.space` | Yes | Production backend URL |
