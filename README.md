# ResumeIQ — Dynamic Resume Optimizer

> ATS Scoring + AI Recruiter Simulation + Bullet Point Rewriting

Full-stack web app built with **React + TypeScript + Tailwind CSS** (frontend), **FastAPI** (backend), **Supabase** (auth/storage/db), and **Gemini API** (AI).

---

## 🏗 Architecture

```
resume-optimizer/
├── frontend/              # React + TypeScript + Tailwind
│   └── src/
│       ├── components/
│       │   ├── auth/      # LandingPage, AuthPage
│       │   ├── dashboard/ # DashboardLayout (sidebar)
│       │   ├── upload/    # UploadPage (drag-drop + JD)
│       │   ├── results/   # ResultsPage (scores + feedback)
│       │   ├── history/   # HistoryPage (past analyses)
│       │   └── ui/        # ScoreRing, etc.
│       ├── hooks/         # useAuth (Supabase Auth context)
│       ├── services/      # api.ts (all backend calls)
│       ├── lib/           # supabase.ts client
│       └── types/         # TypeScript interfaces
│
├── backend/               # FastAPI (Python)
│   ├── main.py            # App entry point + CORS
│   ├── core/
│   │   ├── config.py      # Pydantic settings
│   │   └── supabase.py    # Supabase client
│   ├── models/
│   │   └── schemas.py     # Pydantic request/response models
│   ├── routers/
│   │   ├── resume.py      # POST /upload-resume
│   │   ├── analysis.py    # POST /analyze, POST /rewrite, GET /analysis/{id}
│   │   └── history.py     # GET /history
│   └── services/
│       ├── parser.py      # PDF/DOCX text extraction
│       ├── ats_engine.py  # Keyword matching + ATS scoring
│       ├── gemini_service.py  # Recruiter sim + bullet rewriting
│       └── storage.py     # Supabase DB operations
│
└── supabase_schema.sql    # Database schema + RLS policies
```

---

## 🚀 Quick Start

### 1. Clone and set up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run `supabase_schema.sql` in the SQL editor
3. Create a storage bucket called `resumes` (private)
4. Enable Google OAuth in Authentication → Providers
5. Copy your **Project URL**, **anon key**, and **service role key**

### 2. Get a Gemini API key

Go to [aistudio.google.com](https://aistudio.google.com) and create an API key.

### 3. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Fill in: SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY

uvicorn main:app --reload
# API running at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 4. Frontend setup

```bash
cd frontend
npm install

# Create .env from template
cp .env.example .env
# Fill in: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY

npm run dev
# App running at http://localhost:5173
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload-resume` | Upload PDF/DOCX, parse and store |
| `POST` | `/api/analyze` | Full analysis (ATS + Recruiter + Rewrite) |
| `POST` | `/api/rewrite` | Standalone bullet point rewriter |
| `GET` | `/api/analysis/{id}` | Fetch specific analysis |
| `GET` | `/api/history` | User's analysis history |

---

## 🧠 How It Works

### ATS Scoring
1. Tokenize + normalize both resume and JD text
2. Remove stopwords
3. Extract single tokens + bigrams (for compound tech terms)
4. `score = (matched / total_jd_keywords) * 100`

### Recruiter Simulation
- Sends resume + JD to Gemini with a structured prompt
- Returns: score/10, strengths, weaknesses, suggestions
- Falls back gracefully if AI call fails

### Bullet Rewriting
- Extracts bullet points via regex (lines starting with `•`, `-`, `*`, numbers)
- Batches 5 bullets per Gemini call
- Prompt enforces: action verbs, measurable outcomes, conciseness

---

## 🚢 Deployment

### Frontend → Vercel
```bash
cd frontend && npm run build
# Deploy dist/ to Vercel
# Set env vars: VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_URL
```

### Backend → Render
- New Web Service → Docker or Python
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`, `ALLOWED_ORIGINS`

---

## 🔐 Security Notes

- Backend uses **service role key** (never exposed to frontend)
- Frontend uses **anon key** only (safe to expose)
- All DB tables have **Row Level Security** — users only see their own data
- File storage uses per-user path prefixes

---

## ✨ Features

- [x] Email/password + Google OAuth
- [x] Drag-and-drop PDF/DOCX upload
- [x] ATS keyword matching engine
- [x] Gemini AI recruiter simulation
- [x] Bullet point rewriting
- [x] Score history with trend chart
- [x] Role-specific optimization (SDE, ML, Analyst)
- [x] Loading step indicators
- [x] Row-level security
- [x] Fully typed (TypeScript + Pydantic)
