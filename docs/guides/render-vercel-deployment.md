# Render & Vercel Deployment Guide

This guide outlines how PaperCraft is deployed to **Render** (Backend FastAPI Service) and **Vercel** (Frontend React SPA).

---

## 🛠️ Prerequisites

Before deploying, ensure you have:
1. A **GitHub Repository** with your PaperCraft code pushed (`main` branch).
2. A **Supabase Project** with PostgreSQL database access and `pgvector` enabled.
3. A **Gemini API key** from Google AI Studio.

---

## 🐍 Backend Deployment on Render

1. Go to [Render Dashboard](https://dashboard.render.com) and click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure Service Settings:
   - **Name**: `papercraft-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables under **Environment**:

```env
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
OPENAI_API_KEY=your-gemini-api-key
OPENAI_CHAT_MODEL=gemini-3.5-flash
OPENAI_GROUNDING_MODEL=gemini-3.5-flash
ALLOWED_ORIGINS=https://paper-craft-labs.vercel.app
```

5. Click **Create Web Service**. Your backend will deploy to `https://papercraft.onrender.com`.

---

## ⚡ Frontend Deployment on Vercel

1. Go to [Vercel Dashboard](https://vercel.com) and click **Add New...** → **Project**.
2. Import your GitHub repository.
3. Set **Framework Preset**: `Vite`.
4. Set **Root Directory**: `frontend`.
5. Add Environment Variables under **Environment Variables**:

```env
VITE_API_BASE_URL=https://papercraft.onrender.com
VITE_SUPABASE_URL=https://your-supabase-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-public-key
```

6. Click **Deploy**. Your frontend will deploy to `https://paper-craft-labs.vercel.app`.

---

## 🔄 CORS & Verification

1. Ensure `ALLOWED_ORIGINS` in Render backend contains your Vercel frontend URL.
2. Visit `https://papercraft.onrender.com/health` in your browser. It should return `{"status":"ok"}`.
3. Open your Vercel URL `https://paper-craft-labs.vercel.app`, upload a test PDF/TXT document, ask a question, and test translation!
