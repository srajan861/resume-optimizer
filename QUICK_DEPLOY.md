# Quick Deploy Guide (15 Minutes)

Ultra-condensed deployment guide. For detailed instructions, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Prerequisites (5 min)

1. ✅ Code pushed to GitHub
2. ✅ [Supabase account](https://supabase.com/dashboard) + project created
3. ✅ [Groq API key](https://console.groq.com/keys)
4. ✅ [Render account](https://dashboard.render.com/register)
5. ✅ [Vercel account](https://vercel.com/signup)

## Step 1: Supabase Setup (3 min)

```bash
1. Create project on Supabase
2. Create storage bucket: "resumes" (public)
3. Copy these from Settings → API:
   - Project URL
   - anon/public key  
   - service_role key
   - JWT Secret
```

## Step 2: Deploy Backend to Render (5 min)

1. **Render Dashboard** → **New +** → **Web Service**
2. Connect GitHub repo: `resume-optimizer`
3. **Configure:**
   ```
   Name: resume-optimizer-backend
   Root Directory: backend
   Build: pip install -r requirements.txt
   Start: uvicorn main:app --host 0.0.0.0 --port $PORT
   Plan: Free
   ```

4. **Add Environment Variables:**
   ```
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_SERVICE_KEY=eyJhbGci... (long string)
   SUPABASE_JWT_SECRET=your-jwt-secret
   SUPABASE_BUCKET=resumes
   GROQ_API_KEY=gsk_...
   ALLOWED_ORIGINS=["http://localhost:5173"]
   MAX_FILE_SIZE_MB=10
   REQUIRE_EMAIL_VERIFICATION=false
   DEBUG=false
   ```

5. **Create Web Service** → Wait 3-5 min
6. **Copy backend URL**: `https://xxx.onrender.com`
7. **Test**: Visit `https://xxx.onrender.com/health`

## Step 3: Deploy Frontend to Vercel (4 min)

1. **Vercel Dashboard** → **Add New** → **Project**
2. Import GitHub repo: `resume-optimizer`
3. **Configure:**
   ```
   Framework: Vite (auto-detected)
   Root Directory: frontend
   Build: npm run build
   Output: dist
   ```

4. **Add Environment Variables:**
   ```
   VITE_API_URL=https://your-backend.onrender.com
   VITE_SUPABASE_URL=https://xxx.supabase.co
   VITE_SUPABASE_ANON_KEY=eyJhbGci... (anon key)
   ```

5. **Deploy** → Wait 2-3 min
6. **Copy frontend URL**: `https://xxx.vercel.app`

## Step 4: Update CORS (2 min)

1. **Render** → Your service → **Environment**
2. Edit `ALLOWED_ORIGINS`:
   ```json
   ["https://your-actual-frontend.vercel.app"]
   ```
3. Save → Render auto-redeploys (2-3 min)

## Step 5: Test (1 min)

Visit your Vercel URL and test:
- ✅ Login/Register
- ✅ Upload resume
- ✅ Analyze resume
- ✅ No CORS errors in console

---

## 🎉 Done!

**Your URLs:**
- Frontend: `https://xxx.vercel.app`
- Backend: `https://xxx.onrender.com`
- API Docs: `https://xxx.onrender.com/docs`

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS errors | Update `ALLOWED_ORIGINS` with exact Vercel URL |
| Backend 502 | Wait 30s (cold start on free tier) |
| Frontend blank | Check Vercel logs, verify env vars start with `VITE_` |
| API fails | Verify `VITE_API_URL` has no trailing slash |

**Need help?** See detailed guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
