# BIS Assistant — Production Cloud Deployment Guide

A step-by-step, end-to-end production deployment guide for the **AI-Powered BIS Standards & Services Assistant**.

---

## 1. Deployment Topology & Dependency Flow

Deploy services in this exact order to avoid circular dependencies:

```
┌─────────────────────────────────────────────────────────────┐
│                 DEPLOYMENT ORDER & DATA FLOW                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [STEP 1] Push Latest Code to GitHub                       │
│        │                                                    │
│        ├─────────────────────────────┐                      │
│        ▼                             ▼                      │
│   [STEP 2] Supabase             [STEP 3] Qdrant Cloud       │
│   - PostgreSQL (port 6543)      - Free 1GB Vector Cluster   │
│   - Storage: 'bis-documents'    - Cluster URL & API Key     │
│        │                             │                      │
│        └──────────────┬──────────────┘                      │
│                       ▼                                     │
│   [STEP 4] Render — Node.js Backend (main-backend/)         │
│   - Runs Express, Prisma, JWT Auth, Chats                   │
│   - Run: prisma migrate deploy & node seed-admin.js         │
│        │                                                    │
│        ▼                                                    │
│   [STEP 5] Render — FastAPI AI Service (ai-service/)        │
│   - Runs RAG, Ingestion, Qdrant, Supabase Storage           │
│        │                                                    │
│        ▼                                                    │
│   [STEP 6] Vercel — React Frontend (frontend/)              │
│   - Static SPA on global CDN                                │
│   - Sets VITE_NODE_API_URL & VITE_AI_API_URL                │
│        │                                                    │
│        ▼                                                    │
│   [STEP 7] Update FRONTEND_URL on Render Backends           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Prerequisites & Free Tier Accounts

Create free accounts on the following platforms (all have generous free tiers):

| Platform | Role | Free Tier Limits |
|----------|------|------------------|
| **[GitHub](https://github.com)** | Source code repository | Unlimited public/private repos |
| **[Supabase](https://supabase.com)** | PostgreSQL & Storage | 500MB DB, 1GB Storage, 2 projects |
| **[Qdrant Cloud](https://cloud.qdrant.io)** | Vector Database | 1GB free-forever cluster (1M+ vectors) |
| **[Render](https://render.com)** | Node.js Backend & Python AI Service | 750 free instance hours/month |
| **[Vercel](https://vercel.com)** | React Frontend | Unlimited bandwidth & deployments |
| **[Groq Cloud](https://console.groq.com)** | Fast LLM Inference | Free rate-limited API tier |

---

## 3. Step 1: Commit and Push Code to GitHub

Make sure all latest changes are committed to your GitHub repository:

```bash
git add .
git commit -m "feat: configure cloud deployment with supabase storage, qdrant cloud and split api endpoints"
git push origin main
```

---

## 4. Step 2: Set Up Supabase (PostgreSQL + PDF Storage)

Supabase provides both the relational database for authentication/chat and permanent cloud object storage for PDF files.

### 4.1 Create Project
1. Log in to [supabase.com](https://supabase.com) and click **New Project**.
2. **Name**: `bis-assistant` (or your choice).
3. **Database Password**: Choose a strong password and save it securely.
4. **Region**: Select **South Asia (Mumbai) — `ap-south-1`** for the lowest latency from India.
5. Click **Create new project** and wait ~2 minutes for provisioning.

### 4.2 Copy Transaction Pooler Connection String
1. In the Supabase dashboard, navigate to **Project Settings** (gear icon) → **Database**.
2. Scroll to the **Connection String** section and select the **Transaction** tab (port `6543`).
   > [!IMPORTANT]
   > Do **NOT** use the Direct Connection (`port 5432`) on Render. Render uses dynamic outbound IPs that exhaust direct connections. Always use the **Transaction Pooler** (`port 6543`).
3. Your connection string will look like:
   ```
   postgresql://postgres.xxxxxx:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
   ```
4. Replace `[YOUR-PASSWORD]` with your actual database password. This is your `DATABASE_URL`.

### 4.3 Create Storage Bucket for Permanent PDFs
1. In the left sidebar, click **Storage** (folder icon).
2. Click **New Bucket**.
3. **Name**: `bis-documents` *(must match exactly)*.
4. **Public bucket**: Toggle **ON** (enables preview viewing in browser).
5. Click **Save bucket**.

### 4.4 Get Supabase API Credentials
1. Navigate to **Project Settings** → **API**.
2. Copy:
   - **Project URL** (e.g., `https://abcdefghijklm.supabase.co`) → This is `SUPABASE_URL`.
   - **service_role secret key** (click reveal) → This is `SUPABASE_SERVICE_ROLE_KEY`.
   > [!WARNING]
   > Keep `service_role` secret private. It bypasses row-level security and is only used server-side in the AI microservice.

---

## 5. Step 3: Set Up Qdrant Cloud (Vector Database)

1. Log in to [cloud.qdrant.io](https://cloud.qdrant.io).
2. Click **Create Cluster**.
3. Choose the **Free** tier (1 node, 0.5 vCPU, 1GB RAM — free forever).
4. Select a cloud region close to Render (e.g., `GCP us-east4` or `AWS us-east-1`).
5. **Cluster Name**: `bis-assistant-cluster`.
6. Click **Create**.
7. Once created:
   - Copy the **Cluster URL** (format: `https://xxxxxx-xxxx.us-east4-0.gcp.cloud.qdrant.io:6333`).
   - Click **API Keys** → **Create Key** → copy the generated key.

---

## 6. Step 4: Deploy Node.js Backend on Render

1. Log in to [render.com](https://render.com) and click **New +** → **Web Service**.
2. Connect your GitHub repository (`bis-assistant`).
3. Configure the service:
   - **Name**: `bis-node-backend`
   - **Region**: Choose closest to Supabase/Qdrant (e.g., `Singapore` or `Frankfurt` / `Oregon`)
   - **Branch**: `main`
   - **Root Directory**: `main-backend` *(crucial!)*
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npx prisma generate`
   - **Start Command**: `npm start` *(or: `npx prisma migrate deploy && node seed-admin.js && node index.js`)*
   - **Plan**: `Free`
4. Expand **Advanced** → **Add Environment Variables**:

| Variable Key | Value |
|--------------|-------|
| `DATABASE_URL` | `postgresql://postgres.xxx:[PASSWORD]@aws-0-ap-southeast-2.pooler.supabase.com:6543/postgres` |
| `JWT_SECRET` | Generate a 32+ character random secret (e.g. `openssl rand -hex 32`) |
| `AI_SERVICE_URL` | Placeholder: `https://bis-ai-service.onrender.com` *(we will verify after Step 5)* |
| `FRONTEND_URL` | Placeholder: `https://bis-assistant.vercel.app` *(we will update after Step 6)* |
| `NODE_ENV` | `production` |
| `PORT` | `3000` |

5. Click **Deploy Web Service**.
6. Wait for the build and deployment to complete.

### 4.1 Automatic Migrations & Admin Seed (No Shell Needed!)
> [!TIP]
> **Why Render Free Doesn't Need a Shell:**
> On Render's Free tier, the interactive terminal shell is disabled. We solved this by configuring `npm start` to automatically run:
> ```bash
> npx prisma migrate deploy && node seed-admin.js && node index.js
> ```
> Every time Render deploys or restarts:
> 1. It applies any pending Prisma migrations to Supabase PostgreSQL.
> 2. It runs `seed-admin.js` to ensure the admin user (`admin@bis.gov.in` / `admin123`) exists.
> 3. It starts the Express server.
>
> You will see all migration and admin creation logs directly in the **Logs** tab in Render!
>
> **Alternative (Run from local machine right now):**
> Because Supabase is a cloud database accessible over the internet, you can also run migrations directly from your local terminal:
> ```bash
> cd main-backend
> npx prisma migrate deploy
> node seed-admin.js
> ```

---

## 7. Step 5: Deploy FastAPI AI Service on Render

1. On Render, click **New +** → **Web Service**.
2. Connect the same GitHub repository.
3. Configure the service:
   - **Name**: `bis-ai-service`
   - **Region**: Same region as the Node backend
   - **Branch**: `main`
   - **Root Directory**: `ai-service` *(crucial!)*
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`
4. Expand **Advanced** → **Add Environment Variables**:

| Variable Key | Value |
|--------------|-------|
| `GROQ_API_KEY` | `gsk_xxxxxxxxxxxxxxxxxxxx` |
| `GROQ_MODEL` | `qwen/qwen3.8-27b` |
| `QDRANT_URL` | `https://xxxxxx.us-east4-0.gcp.cloud.qdrant.io:6333` |
| `QDRANT_API_KEY` | Your Qdrant Cloud API Key |
| `QDRANT_COLLECTION_NAME` | `bis_documents` |
| `SUPABASE_URL` | `https://xxxxxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase `service_role` secret |
| `SUPABASE_STORAGE_BUCKET` | `bis-documents` |
| `FRONTEND_URL` | `https://bis-assistant.vercel.app` *(update after Step 6)* |
| `NODE_BACKEND_URL` | `https://bis-node-backend.onrender.com` |

5. Click **Deploy Web Service**.
6. Note the AI service URL (e.g., `https://bis-ai-service.onrender.com`).

> [!NOTE]
> If your actual Render URLs differ from the placeholders, return to `bis-node-backend` → **Environment** and update `AI_SERVICE_URL`.

---

## 8. Step 6: Deploy Frontend on Vercel

1. Log in to [vercel.com](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import your GitHub repository (`bis-assistant`).
4. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click Edit → select `frontend` → click Continue.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand **Environment Variables** and add:

| Key | Value |
|-----|-------|
| `VITE_NODE_API_URL` | `https://bis-node-backend.onrender.com` |
| `VITE_AI_API_URL` | `https://bis-ai-service.onrender.com` |

6. Click **Deploy**.
7. Vercel will build and assign a domain (e.g., `https://bis-assistant.vercel.app` or `https://bis-assistant-xxxx.vercel.app`).

---

## 9. Step 7: Synchronize Production URLs

Now that you have your live Vercel URL:

1. **On Render (`bis-node-backend`)**:
   - Go to **Environment** → Update `FRONTEND_URL` to your exact Vercel URL (e.g. `https://bis-assistant.vercel.app`).
   - Save Changes (Render will automatically redeploy).

2. **On Render (`bis-ai-service`)**:
   - Go to **Environment** → Update `FRONTEND_URL` to your exact Vercel URL.
   - Save Changes (Render will automatically redeploy).

This ensures CORS cookies (`httpOnly`, `SameSite=None`, `Secure`) and headers operate smoothly across subdomains.

---

## 10. End-to-End Verification Checklist

Perform these tests on your live Vercel URL to verify the entire system:

- [ ] **1. Authentication**:
  - Visit the live frontend URL.
  - Log in with Admin credentials (`admin@bis.gov.in` / `admin123`).
  - Verify that the admin dashboard loads and cookie is set in DevTools → Application → Cookies.

- [ ] **2. PDF Upload & Supabase Storage**:
  - In Admin view, upload a BIS PDF (e.g., `IS 4250 Electric Mixer.pdf`).
  - Verify upload succeeds.
  - Check your Supabase Dashboard → **Storage** → `bis-documents/pdfs/` to confirm the file is saved permanently.

- [ ] **3. Ingestion & Chunking**:
  - Click **Process** on the uploaded document.
  - Verify page extraction, Indian Standard detection, and chunk count.
  - Check Supabase Storage → `bis-documents/processed/{doc_id}/` to confirm `pages.json` and `chunks.json` are backed up.

- [ ] **4. Vector Indexing**:
  - Click **Index in Qdrant**.
  - Wait for embedding generation and upsert.
  - Check [cloud.qdrant.io](https://cloud.qdrant.io) dashboard to confirm points exist in collection `bis_documents`.

- [ ] **5. PDF In-Browser Viewing**:
  - Click the document preview/file link.
  - Verify the PDF renders inline in the browser viewer.

- [ ] **6. RAG Assistant & Chat**:
  - Navigate to the Assistant chat view.
  - Ask a question (e.g., *"What are the safety requirements in IS 4250?"*).
  - Verify the assistant answers with citations, source badges, and clause numbers.

- [ ] **7. User Registration**:
  - Log out of Admin.
  - Click **Register**, create a normal user account.
  - Log in and verify normal user access (chat access enabled, admin document upload disabled).

---

## 11. Production Maintenance & FAQ

### Q: Why is my first request slow after inactivity?
Render's free tier spins services down after 15 minutes of inactivity. When the next request arrives, it takes ~30–50 seconds for a "cold start".
- **Solution for college demo**: Keep a tab open or ping the `/api/health` endpoint a few minutes before presenting.
- **Permanent Solution**: Add a free health check cron via [cron-job.org](https://cron-job.org) pinging `https://your-service.onrender.com/api/health` every 10 minutes.

### Q: What if Render AI service throws Out of Memory (OOM)?
The `sentence-transformers/all-MiniLM-L6-v2` embedding model takes ~400MB RAM. Render free tier provides 512MB RAM.
If OOM occurs during multiple concurrent uploads:
1. Upgrade the AI service to Render Starter plan ($7/mo, 2GB RAM).
2. Or use an external embedding API (e.g., Voyage AI or OpenAI `text-embedding-3-small`).

### Q: How do I change the Admin password in production?
In the Render Shell of `bis-node-backend`:
```bash
node -e "
const bcrypt = require('bcryptjs');
const { PrismaClient } = require('@prisma/client');
const prisma = new PrismaClient();
bcrypt.hash('YOUR_NEW_PASSWORD', 10).then(h => 
  prisma.user.update({ where: { email: 'admin@bis.gov.in' }, data: { password: h } })
).then(() => console.log('Password updated')).finally(() => prisma.\$disconnect());
"
```
