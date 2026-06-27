# Deployment Checklist

Quick checklist for deploying to Vercel + Render.

## Pre-Deployment

- [ ] All code committed and pushed to GitHub
- [ ] `.env` files NOT committed (check `.gitignore`)
- [ ] Supabase project created and configured
- [ ] Groq API key obtained
- [ ] Supabase bucket created: `resumes`

## Backend (Render)

- [ ] Create new Web Service on Render
- [ ] Connect GitHub repository
- [ ] Set Root Directory: `backend`
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables:
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_SERVICE_KEY`
  - [ ] `SUPABASE_JWT_SECRET`
  - [ ] `SUPABASE_BUCKET` = `resumes`
  - [ ] `GROQ_API_KEY`
  - [ ] `ALLOWED_ORIGINS` = `["https://your-frontend.vercel.app"]`
  - [ ] `MAX_FILE_SIZE_MB` = `10`
  - [ ] `DEBUG` = `false`
  - [ ] `REQUIRE_EMAIL_VERIFICATION` = `false`
- [ ] Deploy and wait for completion
- [ ] Copy backend URL: `https://______.onrender.com`
- [ ] Test health endpoint: `/health`
- [ ] Test API docs: `/docs`

## Frontend (Vercel)

- [ ] Create new Project on Vercel
- [ ] Import GitHub repository
- [ ] Set Framework: Vite (auto-detected)
- [ ] Set Root Directory: `frontend`
- [ ] Add environment variables:
  - [ ] `VITE_API_URL` = `https://your-backend.onrender.com`
  - [ ] `VITE_SUPABASE_URL`
  - [ ] `VITE_SUPABASE_ANON_KEY`
- [ ] Deploy and wait for completion
- [ ] Copy frontend URL: `https://______.vercel.app`
- [ ] Test login functionality
- [ ] Test file upload

## Post-Deployment

- [ ] Update backend `ALLOWED_ORIGINS` with actual Vercel URL
- [ ] Redeploy backend (automatic on Render)
- [ ] Test full application flow:
  - [ ] Login/Register
  - [ ] Upload resume
  - [ ] Analyze resume
  - [ ] Edit resume
  - [ ] Download results
- [ ] Check browser console for errors
- [ ] Check Network tab for failed requests

## Production Checklist

- [ ] Remove test data from database
- [ ] Set up error monitoring (optional)
- [ ] Configure custom domain (optional)
- [ ] Set up database backups
- [ ] Test on mobile devices
- [ ] Test with real users
- [ ] Monitor logs for first 24 hours

## Common URLs

**Backend:**
- Health: `https://your-backend.onrender.com/health`
- API Docs: `https://your-backend.onrender.com/docs`
- OpenAPI: `https://your-backend.onrender.com/openapi.json`

**Frontend:**
- App: `https://your-app.vercel.app`

## Need Help?

See detailed guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
