# PaperCraft — AI Document Assistant & Translator

PaperCraft is an intelligent, high-performance document Q&A assistant and multi-lingual translation web app built with **FastAPI**, **React TypeScript**, **Supabase Postgres**, and **Google Gemini AI**.

Users can upload custom documents (PDF, TXT, Markdown), organize discussions across dedicated chat threads with automatic per-chat document scoping, receive grounded AI answers, and instantly translate responses into 15+ languages.

---

## ✨ Features

- 📄 **Per-Chat Document Scoping**: Upload files (`.pdf`, `.txt`, `.md`) directly into chat threads with intelligent context matching and automatic chunking in Supabase `pgvector`.
- 💬 **Interactive Document Q&A**: Fast context-aware answers grounded strictly in each conversation's active document.
- 🌐 **Live Multi-Lingual Translation**: One-click translation of AI answers into Spanish 🇪🇸, French 🇫🇷, German 🇩🇪, Hindi 🇮🇳, Japanese 🇯🇵, Chinese 🇨🇳, Italian 🇮🇹, Portuguese 🇵🇹, and more.
- ⚡ **Hybrid RAG & Vector Search**: Integrated `pgvector` hybrid semantic search and fast streaming LLM response pipeline.
- 🎨 **Modern Dark-Mode UI**: Glassmorphic dashboard built with React 18, Vite, TailwindCSS, Lucide icons, and Shadcn UI components.
- 🔐 **Supabase Authentication**: Secure email & password auth with session persistence.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite, TypeScript, TailwindCSS, Lucide Icons, Shadcn UI |
| **Backend** | Python 3.12+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic |
| **Database & Vector Search** | Supabase Postgres, `pgvector`, Alembic migrations |
| **LLM & Embeddings** | Google Gemini API (`gemini-3.5-flash`, `text-embedding-004`) via OpenAI-compatible endpoint |
| **Hosting** | Render (Backend Service) + Vercel (Frontend SPA) |

---

## 📁 Repository Structure

```text
PaperCraft/
├── backend/            # FastAPI backend service
│   ├── app/            # API routes, database models, schemas, and chat orchestrator
│   ├── alembic/        # Database migration scripts
│   ├── ingest/         # Document parsing, chunking, and embedding generation
│   ├── pyproject.toml  # Python project dependencies
│   └── requirements.txt# Render deployment dependencies
├── frontend/           # React SPA frontend
│   ├── src/            # Components, pages, hooks, contexts, and design system
│   └── package.json    # React dependencies & build scripts
├── docs/               # Architecture notes & specifications
└── README.md           # Project documentation
```

---

## ⚙️ Prerequisites & Environment Setup

### 1. Backend Environment (`backend/.env`)

Create `backend/.env`:

```env
# --- Supabase (Auth + API) ---
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres.xxx:password@aws-0-us-east-1.pooler.supabase.com:5432/postgres

# --- Google Gemini API (via OpenAI-Compatible Endpoint) ---
OPENAI_API_KEY=your-gemini-api-key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_CHAT_MODEL=gemini-3.5-flash
OPENAI_GROUNDING_MODEL=gemini-3.5-flash
OPENAI_EMBEDDING_MODEL=text-embedding-004

# --- Server CORS ---
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
npm install
npm run dev
```

Open **`http://localhost:5173`** in your browser.

---

## ☁️ Deployment

- **Backend**: Deployed on [Render](https://render.com) using standard Python runtime.
- **Frontend**: Deployed on [Vercel](https://vercel.com) using Vite React preset.
- **Architecture**: See [docs/architecture.md](docs/architecture.md) for architectural details.
