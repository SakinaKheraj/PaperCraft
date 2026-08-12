# PaperCraft — AI Document Assistant & Translator

PaperCraft is an intelligent, high-performance document Q&A assistant and multi-lingual translation web app built with **FastAPI**, **React TypeScript**, **Supabase Postgres**, and **Gemini AI**.

Users can upload custom documents (PDF, TXT, Markdown), ask questions about the contents, get fast AI answers, and instantly translate responses into 8+ languages.

---

## ✨ Features

- 📄 **Custom Document Upload**: Fast document parsing (`.pdf`, `.txt`, `.md`) with chunking and vector storage in Supabase `pgvector`.
- 💬 **Interactive Document Q&A**: Fast context-aware answers grounded in your uploaded documents.
- 🌐 **Live Multi-Lingual Translation**: One-click translation of AI answers into Spanish 🇪🇸, French 🇫🇷, German 🇩🇪, Hindi 🇮🇳, Japanese 🇯🇵, Chinese 🇨🇳, Italian 🇮🇹, and Portuguese 🇵🇹.
- ⚡ **RAG & Vector Search Architecture**: Integrated `pgvector` hybrid semantic search and PydanticAI grounding engine.
- 🎨 **Modern Dark-Mode UI**: Glassmorphic dashboard built with React, Vite, TailwindCSS, Lucide icons, and Shadcn UI components.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite, TypeScript, TailwindCSS, Lucide Icons |
| **Backend** | Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2.0 |
| **Database & Vector Search** | Supabase Postgres, `pgvector`, Alembic migrations |
| **LLM & Embeddings** | Gemini AI (`gemini-3.5-flash`, `text-embedding-004`) |
| **Hosting** | Render (Backend Service) + Vercel (Frontend SPA) |

---

## 📁 Repository Structure

```text
PaperCraft/
├── backend/            # FastAPI backend service
│   ├── app/            # Main application (API routes, database models, schemas)
│   ├── alembic/        # Database migration scripts
│   ├── pyproject.toml  # Python project dependencies
│   └── requirements.txt# Render deployment dependencies
├── frontend/           # React SPA frontend
│   ├── src/            # Components, pages, hooks, contexts, and design system
│   └── package.json    # React dependencies & build scripts
├── docs/               # Architecture notes & deployment guides
└── README.md           # Project documentation
```

---

## ⚙️ Prerequisites & Environment Setup

### 1. Backend Environment (`backend/.env`)

Create `backend/.env`:

```env
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
OPENAI_API_KEY=your-gemini-api-key
OPENAI_CHAT_MODEL=gemini-3.5-flash
OPENAI_GROUNDING_MODEL=gemini-3.5-flash
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:5174,https://paper-craft-labs.vercel.app
```

### 2. Frontend Environment (`frontend/.env`)

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-supabase-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

---

## 🚀 Running Locally

### Backend Setup:

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup:

```bash
cd frontend
pnpm install
pnpm dev
```

Open **`http://localhost:5173`** in your browser.

---

## ☁️ Deployment

- **Backend**: Deployed on [Render](https://render.com) using standard Python runtime.
- **Frontend**: Deployed on [Vercel](https://vercel.com) using Vite React preset.
