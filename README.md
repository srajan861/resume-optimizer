# Resume Optimizer

AI-powered resume optimization tool with ATS analysis, real-time editing, and automated tailoring.

## Quick Start (Local Development)

### Prerequisites
- Node.js 20+
- Python 3.11+
- Git

### Setup

```bash
# Clone repository
git clone <repository-url>
cd resume-optimizer

# Backend setup
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd ../frontend
npm install
cp .env.example .env
# Edit .env with your API keys

# Run backend
cd ../backend
uvicorn main:app --reload

# Run frontend (new terminal)
cd ../frontend
npm run dev
```

### Access Points
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Deployment

### Backend (Render)

1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name:** resume-optimizer-backend
   - **Root Directory:** `backend`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`
   - `SUPABASE_JWT_SECRET`
   - `GROQ_API_KEY`
   - `ALLOWED_ORIGINS` = `["https://your-frontend.vercel.app"]`
   - `DEBUG` = `false`
7. Click "Create Web Service"

### Frontend (Vercel)

1. Push code to GitHub
2. Go to [Vercel Dashboard](https://vercel.com/dashboard)
3. Click "Add New..." → "Project"
4. Import your GitHub repository
5. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
6. Add environment variables:
   - `VITE_API_URL` = `https://your-backend.onrender.com`
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
7. Click "Deploy"

### Post-Deployment

1. Update backend `ALLOWED_ORIGINS` with your Vercel URL
2. Update frontend `VITE_API_URL` with your Render URL
3. Redeploy both services

## Environment Variables

### Backend (.env)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_BUCKET=resumes
GROQ_API_KEY=your-groq-key
ALLOWED_ORIGINS=["http://localhost:5173"]
MAX_FILE_SIZE_MB=10
REQUIRE_EMAIL_VERIFICATION=false
DEBUG=true
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

## Architecture

```
├── backend/          FastAPI application (Python 3.11)
│   ├── core/        Auth, security, config
│   ├── models/      Pydantic schemas
│   ├── routers/     API endpoints
│   ├── services/    Business logic
│   └── render.yaml  Render deployment config
├── frontend/         React + Vite application (Node 20)
│   └── src/         Components, services, utils
├── docs/            Documentation
└── vercel.json      Vercel deployment config
```

## Documentation

- [Authentication](docs/AUTHENTICATION_EXPLAINED.md)
- [Input Validation](docs/INPUT_VALIDATION.md)
- [Security Summary](docs/SECURITY_SUMMARY.md)
- [Rate Limiting](docs/GROQ_API_RATE_LIMITING.md)
- [Quick Reference](docs/QUICK_REFERENCE.md)

## Features

- **ATS Analysis:** Score resumes against job descriptions
- **Real-time Editor:** Live resume editing with preview
- **Auto Optimization:** AI-powered resume tailoring
- **Version History:** Track resume changes over time
- **Secure Authentication:** JWT-based auth with Supabase

## Tech Stack

**Backend:**
- FastAPI (Python 3.11)
- Supabase (Database & Storage)
- Groq API (LLM)
- Deployed on Render

**Frontend:**
- React 18
- TypeScript
- Vite
- TailwindCSS
- Supabase Client
- Deployed on Vercel

## License

MIT
