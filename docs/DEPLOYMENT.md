# Deployment Guide - Complete Walkthrough

This comprehensive guide covers deploying the Resume Optimizer application to production using:
- **Frontend:** Vercel (Free tier)
- **Backend:** Render (Free tier)

**Total Time:** 20-30 minutes  
**Cost:** $0 (Free tier)

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] **GitHub Account** - [Sign up here](https://github.com/signup)
- [ ] **Code pushed to GitHub** (public or private repo)
- [ ] **Vercel Account** - [Sign up here](https://vercel.com/signup) (use GitHub to sign in)
- [ ] **Render Account** - [Sign up here](https://dashboard.render.com/register) (use GitHub to sign in)
- [ ] **Supabase Project** - [Create here](https://supabase.com/dashboard)
- [ ] **Groq API Key** - [Get here](https://console.groq.com/keys)

---

## Part 1: Prepare Your Repository

### 1.1 Verify File Structure

Ensure your repository has this structure:

```
resume-optimizer/
├── backend/
│   ├── core/
│   ├── models/
│   ├── routers/
│   ├── services/
│   ├── main.py
│   ├── requirements.txt
│   ├── render.yaml          ← Important!
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
├── vercel.json              ← Important!
├── .gitignore
└── README.md
```

### 1.2 Push Code to GitHub

```bash
# Check current status
git status

# Add all files
git add .

# Commit changes
git commit -m "Prepare for deployment"

# Push to GitHub
git push origin main
```

**Verify:** Go to your GitHub repository and confirm all files are uploaded.

---

## Part 2: Setup Supabase (Database)

### 2.1 Create Supabase Project

1. Go to https://supabase.com/dashboard
2. Click **"New Project"**
3. Fill in:
   - **Name:** `resume-optimizer`
   - **Database Password:** (save this securely)
   - **Region:** Choose closest to your users
4. Click **"Create new project"**
5. Wait 2-3 minutes for project setup

### 2.2 Create Storage Bucket

1. In your Supabase dashboard, click **"Storage"** in sidebar
2. Click **"Create a new bucket"**
3. Name: `resumes`
4. Set to **"Public bucket"** (or configure RLS policies)
5. Click **"Create bucket"**

### 2.3 Get API Keys

1. Click **"Settings"** (gear icon) in sidebar
2. Click **"API"**
3. Copy and save these values:

| Key | Where to find | Used in |
|-----|---------------|---------|
| **Project URL** | Top of page | Backend + Frontend |
| **anon/public key** | `anon` `public` section | Frontend |
| **service_role key** | `service_role` section (click "Reveal") | Backend ONLY |
| **JWT Secret** | Scroll down to "JWT Settings" | Backend |

⚠️ **NEVER commit service_role key to GitHub!**

### 2.4 Run Database Schema (Optional)

If you have a `supabase_schema.sql` file:

1. In Supabase dashboard, click **"SQL Editor"**
2. Click **"New query"**
3. Paste contents of `supabase_schema.sql`
4. Click **"Run"**

---

## Part 3: Get Groq API Key

1. Go to https://console.groq.com/keys
2. Sign in or create account
3. Click **"Create API Key"**
4. Name: `resume-optimizer`
5. Copy the key (starts with `gsk_...`)
6. **Save it securely** - you can't view it again!

---

## Part 4: Deploy Backend to Render

### 4.1 Create Render Account

1. Go to https://dashboard.render.com/register
2. Click **"Sign in with GitHub"**
3. Authorize Render to access your repositories

### 4.2 Create Web Service

1. From Render dashboard, click **"New +"** button (top right)
2. Select **"Web Service"**
3. You'll see "Connect a repository" - if first time:
   - Click **"Configure account"**
   - Choose **"All repositories"** or select specific repo
   - Click **"Install"**
4. Back in Render, you should see your `resume-optimizer` repo
5. Click **"Connect"** next to your repository

### 4.3 Configure Service Settings

Fill in these **exact** values:

**Basic Information:**
- **Name:** `resume-optimizer-backend` (or your choice - this will be in your URL)
- **Region:** `Oregon (US West)` (or closest to you)
- **Branch:** `main`
- **Root Directory:** `backend` ← **CRITICAL!**

**Build Settings:**
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select **"Free"** ($0/month)

⚠️ **Do NOT click "Create Web Service" yet!** We need to add environment variables first.

### 4.4 Add Environment Variables

Click **"Advanced"** button to expand.

Scroll to **"Environment Variables"** section and click **"Add Environment Variable"** for each:

| Key | Value | Where to get |
|-----|-------|--------------|
| `SUPABASE_URL` | `https://xxx.supabase.co` | Supabase → Settings → API |
| `SUPABASE_SERVICE_KEY` | `eyJhbGci...` (long string) | Supabase → Settings → API → service_role (click Reveal) |
| `SUPABASE_JWT_SECRET` | UUID format | Supabase → Settings → API → JWT Secret |
| `SUPABASE_BUCKET` | `resumes` | Your bucket name |
| `GROQ_API_KEY` | `gsk_...` | From console.groq.com |
| `ALLOWED_ORIGINS` | `["http://localhost:5173"]` | We'll update this later |
| `MAX_FILE_SIZE_MB` | `10` | File size limit |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Email verification toggle |
| `DEBUG` | `false` | Set false for production |

**Double-check:**
- All keys spelled correctly (case-sensitive!)
- No extra spaces in values
- Service key and JWT secret are complete (very long strings)

### 4.5 Deploy Backend

1. Click **"Create Web Service"** (bottom of page)
2. Render will start building your service
3. You'll see logs in real-time:
   ```
   Installing dependencies...
   Successfully installed fastapi uvicorn...
   Build succeeded 🎉
   Starting service...
   ```
4. Wait 3-5 minutes for first deployment
5. Once you see **"Live"** with green indicator, deployment is complete!

### 4.6 Copy Backend URL

At the top of your service page, you'll see:
```
https://resume-optimizer-backend-xxxx.onrender.com
```

**Copy this URL** - you'll need it for frontend deployment.

### 4.7 Verify Backend is Working

Test these URLs in your browser:

1. **Health Check:** `https://your-backend.onrender.com/health`
   
   Should return:
   ```json
   {
     "status": "ok",
     "timestamp": 1234567890.123,
     "version": "2.0.0"
   }
   ```

2. **API Documentation:** `https://your-backend.onrender.com/docs`
   
   Should show interactive API documentation (Swagger UI)

✅ **If both work, backend is successfully deployed!**

⚠️ **Note:** On free tier, backend sleeps after 15 minutes of inactivity. First request after sleep takes ~30 seconds to wake up.

---

## Part 5: Deploy Frontend to Vercel

### 5.1 Create Vercel Account

1. Go to https://vercel.com/signup
2. Click **"Continue with GitHub"**
3. Authorize Vercel

### 5.2 Import Project

1. From Vercel dashboard, click **"Add New..."** → **"Project"**
2. You'll see your GitHub repositories
3. Find `resume-optimizer` and click **"Import"**

### 5.3 Configure Project

Vercel should auto-detect Vite. Configure these settings:

**Framework Preset:**
- Should say **"Vite"** (auto-detected)
- If not, select **"Vite"** from dropdown

**Root Directory:**
- Click **"Edit"** next to Root Directory
- Select **`frontend`** ← **CRITICAL!**
- Click **"Continue"**

**Build and Output Settings:**
- **Build Command:** `npm run build` (default - don't change)
- **Output Directory:** `dist` (default - don't change)
- **Install Command:** `npm install` (default - don't change)

⚠️ **Do NOT click "Deploy" yet!** We need to add environment variables first.

### 5.4 Add Environment Variables

Click **"Environment Variables"** section to expand.

Add these variables:

| Name | Value | Where to get |
|------|-------|--------------|
| `VITE_API_URL` | `https://your-backend.onrender.com` | From Render (Part 4.6) - **NO trailing slash** |
| `VITE_SUPABASE_URL` | `https://xxx.supabase.co` | Supabase → Settings → API |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGci...` | Supabase → Settings → API → anon/public key |

**Important Notes:**
- All environment variable names MUST start with `VITE_`
- `VITE_API_URL` should **NOT** have a trailing slash
- Use your **actual Render backend URL** from Part 4.6
- Use **anon key** (NOT service_role key) for frontend

### 5.5 Deploy Frontend

1. Click **"Deploy"** button
2. Vercel will build your frontend:
   ```
   Cloning repository...
   Installing dependencies...
   Building application...
   Deployment ready!
   ```
3. Wait 2-3 minutes
4. Once complete, you'll see **"Congratulations!"** 🎉

### 5.6 Copy Frontend URL

You'll see your deployment URL:
```
https://resume-optimizer-xxxx.vercel.app
```

**Copy this URL** - you'll need it to update backend CORS.

### 5.7 Test Frontend

Click **"Visit"** button or go to your Vercel URL.

You should see:
- ✅ Login/Register page loads
- ⚠️ API calls might fail (CORS issue) - we'll fix this next!

---

## Part 6: Configure CORS (Connect Frontend ↔ Backend)

Your frontend can't talk to backend yet because of CORS. Let's fix it!

### 6.1 Update Backend CORS Settings

1. Go back to **Render dashboard**
2. Select your **backend service**
3. Click **"Environment"** in left sidebar
4. Find `ALLOWED_ORIGINS` variable
5. Click **"Edit"** (pencil icon)
6. Update value to include your Vercel URL:
   ```json
   ["https://resume-optimizer-xxxx.vercel.app"]
   ```
   Replace `xxxx` with your actual Vercel subdomain
7. Click **"Save Changes"**

Render will automatically redeploy (takes 2-3 minutes).

### 6.2 Verify Connection

1. Go to your Vercel frontend URL
2. Open browser **Developer Tools** (F12)
3. Go to **Console** tab
4. Try to **log in or register**
5. Check for errors:
   - ✅ **No CORS errors** = Success!
   - ❌ **CORS errors** = Double-check URLs match exactly

---

## Part 7: Final Testing

### 7.1 Complete User Flow Test

Test everything works end-to-end:

1. **Register/Login**
   - [ ] Can create account
   - [ ] Can log in
   - [ ] Token stored correctly

2. **Upload Resume**
   - [ ] Can upload PDF/DOCX
   - [ ] File appears in Supabase Storage
   - [ ] No errors in console

3. **Analyze Resume**
   - [ ] Can paste job description
   - [ ] Analysis completes
   - [ ] Score displays correctly

4. **Edit Resume**
   - [ ] Live editor loads
   - [ ] Can make changes
   - [ ] Changes save

5. **View History**
   - [ ] Past analyses show
   - [ ] Can view details

### 7.2 Check Logs for Errors

**Backend (Render):**
1. Render dashboard → Your service
2. Click **"Logs"** tab
3. Look for any errors (red lines)

**Frontend (Vercel):**
1. Browser Developer Tools (F12)
2. Check **Console** tab for errors
3. Check **Network** tab for failed requests

---

## Part 8: Custom Domains (Optional)

### 8.1 Add Custom Domain to Vercel

1. Vercel dashboard → Your project
2. Click **"Settings"**
3. Click **"Domains"**
4. Click **"Add"**
5. Enter your domain: `app.yourdomain.com`
6. Follow DNS instructions (add A/CNAME records)
7. Wait for SSL certificate (automatic, ~5-10 minutes)

### 8.2 Add Custom Domain to Render

1. Render dashboard → Your service
2. Click **"Settings"**
3. Scroll to **"Custom Domains"**
4. Click **"Add Custom Domain"**
5. Enter your domain: `api.yourdomain.com`
6. Add CNAME record to your DNS:
   ```
   api.yourdomain.com → your-service.onrender.com
   ```
7. Wait for SSL certificate (automatic)

### 8.3 Update Environment Variables

After adding custom domains:

**Update Render:**
- `ALLOWED_ORIGINS` = `["https://app.yourdomain.com"]`

**Update Vercel:**
- `VITE_API_URL` = `https://api.yourdomain.com`

Redeploy both services after changes.

---

## Part 9: Troubleshooting


### Common Issues and Solutions

#### Backend Issues

**Problem:** "Application failed to respond"
- **Cause:** Missing environment variables or wrong start command
- **Solution:**
  1. Check Render logs for specific error
  2. Verify all environment variables are set correctly
  3. Ensure `PORT` is not hardcoded in your code (use `$PORT`)
  4. Check `requirements.txt` has all dependencies

**Problem:** "502 Bad Gateway"
- **Cause:** Service starting up or crashed
- **Solution:**
  1. Wait 1-2 minutes (first deploy takes time)
  2. Check logs for Python errors
  3. Verify Supabase credentials are correct
  4. Test locally first: `uvicorn main:app --reload`

**Problem:** CORS Errors in Browser
- **Cause:** Frontend URL not in `ALLOWED_ORIGINS`
- **Solution:**
  1. Check exact URL matches (no trailing slash)
  2. Check URL format: `["https://yourapp.vercel.app"]` (JSON array)
  3. After updating, wait for Render to redeploy (2-3 min)
  4. Hard refresh browser (Ctrl+Shift+R)

**Problem:** "Module not found" errors
- **Cause:** Missing dependency in `requirements.txt`
- **Solution:**
  1. Add missing package to `requirements.txt`
  2. Push to GitHub
  3. Render will auto-redeploy

#### Frontend Issues

**Problem:** "Failed to fetch" / Network errors
- **Cause:** Wrong backend URL or backend down
- **Solution:**
  1. Verify `VITE_API_URL` is correct Render URL
  2. Check no trailing slash in URL
  3. Test backend URL directly in browser
  4. Check browser Network tab for actual error

**Problem:** Blank page after deployment
- **Cause:** Build errors or missing environment variables
- **Solution:**
  1. Check Vercel deployment logs for build errors
  2. Verify all `VITE_` variables are set
  3. Check browser console for JavaScript errors
  4. Ensure `frontend` is set as root directory

**Problem:** Environment variables not working
- **Cause:** Variables must start with `VITE_` or not redeployed
- **Solution:**
  1. Ensure all frontend env vars start with `VITE_`
  2. After adding variables, trigger new deployment
  3. Check Variables are in "Production" environment
  4. Hard refresh browser cache

**Problem:** "Cannot find module" errors
- **Cause:** Missing dependency in `package.json`
- **Solution:**
  1. Add package: `npm install <package>`
  2. Commit updated `package.json` and `package-lock.json`
  3. Push to GitHub

#### Database/Supabase Issues

**Problem:** "Authentication failed"
- **Cause:** Wrong credentials or JWT secret mismatch
- **Solution:**
  1. Verify `SUPABASE_JWT_SECRET` matches Supabase dashboard
  2. Check `SUPABASE_URL` has no trailing slash
  3. Ensure service_role key is complete (very long string)
  4. Check Supabase project is not paused

**Problem:** "Bucket not found"
- **Cause:** Storage bucket not created or wrong name
- **Solution:**
  1. Go to Supabase → Storage
  2. Create bucket named exactly `resumes`
  3. Set bucket to public or configure RLS policies
  4. Verify `SUPABASE_BUCKET=resumes` in backend env vars

**Problem:** "Row Level Security policy violation"
- **Cause:** RLS enabled but no policies set
- **Solution:**
  1. Go to Supabase → Authentication → Policies
  2. Create policies for your tables
  3. Or temporarily disable RLS for testing (not recommended for production)

#### Render-Specific Issues

**Problem:** Service keeps restarting
- **Cause:** Application crash on startup
- **Solution:**
  1. Check logs for Python exceptions
  2. Test locally with same environment variables
  3. Check all required env vars are set
  4. Verify database is accessible

**Problem:** Cold starts taking too long (30+ seconds)
- **Cause:** Free tier limitation
- **Solution:**
  1. This is normal on free tier
  2. Upgrade to $7/month plan to remove cold starts
  3. Or keep backend "warm" with periodic pings

#### Vercel-Specific Issues

**Problem:** Build fails with "command not found"
- **Cause:** Wrong build command or missing package
- **Solution:**
  1. Check `package.json` has build script
  2. Ensure root directory is set to `frontend`
  3. Check Node version compatibility

**Problem:** Routes not working (404 on refresh)
- **Cause:** SPA routing not configured
- **Solution:**
  1. Verify `vercel.json` exists in project root
  2. Check rewrites configuration is present
  3. Redeploy if you just added `vercel.json`

---

## Part 10: Monitoring & Maintenance

### Monitor Render Backend

**View Logs:**
1. Render dashboard → Your service
2. Click **"Logs"** tab
3. Filter by time period
4. Search for specific errors

**Set Up Alerts:**
1. Service → Settings
2. Scroll to **"Deploy notifications"**
3. Enable notifications for:
   - Deploy succeeded
   - Deploy failed
   - Service suspended

### Monitor Vercel Frontend

**View Logs:**
1. Vercel dashboard → Your project
2. Click on a deployment
3. Click **"View Function Logs"**

**Analytics (Requires Pro plan):**
- Vercel → Your project → Analytics
- See page views, performance metrics

### Uptime Monitoring (Free Tools)

Use external services to monitor uptime:
- [UptimeRobot](https://uptimerobot.com/) - Free, 50 monitors
- [Better Uptime](https://betteruptime.com/) - Free tier available
- [StatusCake](https://www.statuscake.com/) - Free tier available

**Setup:**
1. Add monitor for: `https://your-backend.onrender.com/health`
2. Set check frequency: 5 minutes
3. Get email alerts on downtime

### Performance Monitoring

**Backend:**
- Render shows CPU, memory usage in Metrics tab
- Add APM tool like [Sentry](https://sentry.io/) for error tracking

**Frontend:**
- Vercel Analytics (paid)
- Google Analytics (free)
- [Plausible](https://plausible.io/) (privacy-friendly)

---

## Part 11: Continuous Deployment

### How It Works

Both platforms automatically deploy on git push:

```bash
# Make changes to your code
git add .
git commit -m "Add new feature"
git push origin main

# Render and Vercel automatically detect and deploy!
```

**Deployment Timeline:**
- **Vercel:** 2-3 minutes (frontend)
- **Render:** 3-5 minutes (backend)

### Disable Auto-Deploy (Optional)

**Render:**
1. Service → Settings
2. Scroll to "Build & Deploy"
3. Toggle off "Auto-Deploy"

**Vercel:**
1. Project → Settings
2. Git → Ignored Build Step
3. Add condition to skip builds

### Manual Deploy

**Render:**
1. Service → Manual Deploy
2. Select branch
3. Click "Deploy"

**Vercel:**
1. Project → Deployments
2. Click "..." → "Redeploy"

---

## Part 12: Production Checklist

Before announcing your app to users:

### Security
- [ ] All API keys in environment variables (not in code)
- [ ] `.env` files in `.gitignore`
- [ ] `DEBUG=false` on backend
- [ ] CORS restricted to your frontend domain only
- [ ] Supabase RLS policies configured
- [ ] HTTPS enabled (automatic on Vercel/Render)

### Functionality
- [ ] All features tested end-to-end
- [ ] Error handling works
- [ ] Loading states display
- [ ] Mobile responsive
- [ ] Works in Chrome, Firefox, Safari

### Performance
- [ ] Images optimized
- [ ] Large files compressed
- [ ] API responses under 2 seconds
- [ ] Frontend loads in under 3 seconds

### Monitoring
- [ ] Error logging configured
- [ ] Uptime monitoring set up
- [ ] Email alerts configured
- [ ] Logs reviewed regularly

### Documentation
- [ ] README updated with live URLs
- [ ] API documentation accessible
- [ ] Environment variables documented

---

## Part 13: Scaling & Upgrades

### When to Upgrade

**Render Free Tier Limits:**
- ✅ Good for: Portfolios, MVPs, demos
- ❌ Issues: Cold starts (30s), 750 hours/month
- **Upgrade at:** When cold starts hurt UX

**Upgrade Options:**
```
Starter: $7/month
- No cold starts
- 512 MB RAM
- Always on

Standard: $25/month  
- 2 GB RAM
- Better performance
```

**Vercel Free Tier Limits:**
- ✅ Good for: Most apps
- ❌ Issues: 100 GB bandwidth/month
- **Upgrade at:** When you exceed bandwidth

**Upgrade Options:**
```
Pro: $20/month
- 1 TB bandwidth
- Advanced analytics
- Preview deployments with password
```

### Horizontal Scaling

When you outgrow PaaS:
1. Move to containerized deployment (Docker + Kubernetes)
2. Use AWS/GCP/Azure
3. Implement microservices
4. Add caching layer (Redis)
5. Use CDN for static assets

---

## Quick Command Reference

### Render

```bash
# View logs
# Go to: Dashboard → Service → Logs

# Manual deploy
# Go to: Dashboard → Service → Manual Deploy

# Restart service
# Go to: Dashboard → Service → Settings → Restart
```

### Vercel

```bash
# Deploy from CLI
npm i -g vercel
vercel --prod

# View logs
vercel logs <deployment-url>

# List deployments
vercel ls
```

---

## Getting Help

### Official Documentation
- **Render:** https://render.com/docs
- **Vercel:** https://vercel.com/docs
- **Supabase:** https://supabase.com/docs

### Community Support
- **Render Discord:** https://render.com/discord
- **Vercel Discord:** https://vercel.com/discord
- **Supabase Discord:** https://discord.supabase.com/

### Common Links
- **Render Dashboard:** https://dashboard.render.com/
- **Vercel Dashboard:** https://vercel.com/dashboard
- **Supabase Dashboard:** https://supabase.com/dashboard
- **Groq Console:** https://console.groq.com/

---

## Summary

You've successfully deployed your Resume Optimizer! 🎉

**Your URLs:**
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-backend.onrender.com`
- API Docs: `https://your-backend.onrender.com/docs`

**What's Deployed:**
- ✅ Frontend on Vercel (global CDN, instant loading)
- ✅ Backend on Render (API + business logic)
- ✅ Database on Supabase (PostgreSQL + Storage)
- ✅ AI on Groq (LLM API)

**Next Steps:**
1. Share your app URL
2. Gather user feedback
3. Monitor logs for errors
4. Iterate on features
5. Scale when needed

**Questions?** Check troubleshooting section or reach out to platform support!

### 2.1 Create Web Service

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect to GitHub"** (authorize if needed)
4. Select your **resume-optimizer** repository
5. Click **"Connect"**

### 2.2 Configure Service

**Basic Settings:**
- **Name:** `resume-optimizer-backend` (or your choice)
- **Region:** Oregon (US West) or closest to your users
- **Branch:** `main`
- **Root Directory:** `backend`
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select **"Free"** (or upgrade as needed)

### 2.3 Add Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** for each:

| Key | Value | Notes |
|-----|-------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | From Supabase dashboard |
| `SUPABASE_SERVICE_KEY` | `eyJhbGci...` | Settings → API → service_role key |
| `SUPABASE_JWT_SECRET` | `your-jwt-secret` | Settings → API → JWT Secret |
| `SUPABASE_BUCKET` | `resumes` | Your bucket name |
| `GROQ_API_KEY` | `gsk_...` | From console.groq.com |
| `ALLOWED_ORIGINS` | `["https://your-app.vercel.app"]` | Update after frontend deploy |
| `MAX_FILE_SIZE_MB` | `10` | File upload limit |
| `REQUIRE_EMAIL_VERIFICATION` | `false` | Email verification toggle |
| `DEBUG` | `false` | Set to false for production |

### 2.4 Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (3-5 minutes)
3. Once deployed, copy your backend URL: `https://your-app.onrender.com`

### 2.5 Verify Backend

Visit: `https://your-app.onrender.com/health`

Expected response:
```json
{
  "status": "ok",
  "timestamp": 1234567890.123,
  "version": "2.0.0"
}
```

Visit API docs: `https://your-app.onrender.com/docs`

## Step 3: Deploy Frontend to Vercel

### 3.1 Create Project

1. Go to https://vercel.com/dashboard
2. Click **"Add New..."** → **"Project"**
3. Click **"Import Git Repository"**
4. Select **resume-optimizer** repository
5. Click **"Import"**

### 3.2 Configure Project

**Framework Preset:** Vite (should auto-detect)

**Build Settings:**
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Install Command:** `npm install`

### 3.3 Add Environment Variables

Click **"Environment Variables"** and add:

| Name | Value | Notes |
|------|-------|-------|
| `VITE_API_URL` | `https://your-backend.onrender.com` | Your Render backend URL |
| `VITE_SUPABASE_URL` | `https://your-project.supabase.co` | From Supabase dashboard |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGci...` | Settings → API → anon/public key |

### 3.4 Deploy

1. Click **"Deploy"**
2. Wait for deployment (2-3 minutes)
3. Once deployed, copy your frontend URL: `https://your-app.vercel.app`

### 3.5 Verify Frontend

1. Visit your Vercel URL
2. Try logging in
3. Test uploading a resume

## Step 4: Update CORS Configuration

### 4.1 Update Backend ALLOWED_ORIGINS

1. Go to Render dashboard
2. Select your backend service
3. Click **"Environment"**
4. Update `ALLOWED_ORIGINS`:
   ```
   ["https://your-app.vercel.app"]
   ```
   (Replace with your actual Vercel URL)
5. Save changes
6. Service will automatically redeploy

### 4.2 Verify

Test API calls from your frontend. Check browser console for CORS errors.

## Step 5: Configure Custom Domain (Optional)

### Frontend (Vercel)

1. Go to Project Settings → Domains
2. Add your custom domain (e.g., `app.yourdomain.com`)
3. Add DNS records as instructed by Vercel
4. Wait for SSL certificate (automatic)

### Backend (Render)

1. Go to Service Settings → Custom Domains
2. Add your custom domain (e.g., `api.yourdomain.com`)
3. Add CNAME record: `your-app.onrender.com`
4. Wait for SSL certificate (automatic)

### Update Environment Variables

After adding custom domains:
1. Update backend `ALLOWED_ORIGINS` with new frontend domain
2. Update frontend `VITE_API_URL` with new backend domain
3. Redeploy both services

## Troubleshooting

### Backend Issues

**"Application failed to respond"**
- Check Render logs for errors
- Verify all environment variables are set
- Ensure `PORT` is not hardcoded (use `$PORT`)

**"502 Bad Gateway"**
- Service might be starting up (wait 1-2 minutes)
- Check if service crashed in logs

**CORS Errors**
- Verify `ALLOWED_ORIGINS` includes your frontend URL
- Check URL format (no trailing slash)
- Redeploy backend after changes

### Frontend Issues

**"Failed to fetch" errors**
- Verify `VITE_API_URL` is correct (check for typos)
- Check backend is running
- Open Network tab in browser DevTools

**Blank page after deployment**
- Check Vercel build logs for errors
- Verify `dist` folder is being generated
- Check browser console for errors

**Environment variables not working**
- Ensure variables start with `VITE_`
- Redeploy after adding variables
- Check Vercel deployment logs

### Database Issues

**"Authentication failed"**
- Verify Supabase credentials
- Check JWT secret matches
- Ensure RLS policies allow access

**"Bucket not found"**
- Create bucket in Supabase Storage
- Set bucket to public or configure policies
- Verify bucket name matches `SUPABASE_BUCKET`

## Monitoring

### Render

- **Logs:** Dashboard → Your Service → Logs
- **Metrics:** Dashboard → Your Service → Metrics
- **Alerts:** Can configure email alerts for downtime

### Vercel

- **Deployment Logs:** Dashboard → Deployments → View Function Logs
- **Analytics:** Dashboard → Analytics (requires upgrade)
- **Alerts:** Integrated with GitHub for deployment notifications

## Continuous Deployment

Both Vercel and Render automatically redeploy when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Both services will automatically detect and deploy
```

**Deployment Triggers:**
- **Vercel:** Deploys on every push to `main`
- **Render:** Deploys on every push to `main`

**Disable Auto-Deploy:**
- **Vercel:** Project Settings → Git → Disable
- **Render:** Service Settings → Build & Deploy → Disable

## Production Checklist

Before going live:

- [ ] All environment variables set correctly
- [ ] `DEBUG=false` on backend
- [ ] CORS configured with production URLs
- [ ] Custom domains configured (optional)
- [ ] SSL certificates active (automatic)
- [ ] Email verification enabled (optional)
- [ ] Database backups configured (Supabase)
- [ ] API rate limits tested
- [ ] Error logging configured
- [ ] Monitoring alerts set up

## Cost Estimates

### Free Tier Limits

**Render (Free):**
- 750 hours/month
- Sleeps after 15 minutes of inactivity
- Wakes up on request (cold start ~30s)
- 512 MB RAM

**Vercel (Free):**
- 100 GB bandwidth/month
- 6000 build minutes/month
- Instant deployments
- Unlimited sites

**Upgrade Considerations:**
- Render: $7/month for always-on + more resources
- Vercel: $20/month for Pro (more bandwidth, faster builds)

## Next Steps

1. Set up custom domains
2. Configure email verification
3. Set up error monitoring (Sentry)
4. Add analytics (Google Analytics, Plausible)
5. Configure database backups
6. Set up staging environment
7. Add CI/CD tests

## Support

- **Render:** https://render.com/docs
- **Vercel:** https://vercel.com/docs
- **Supabase:** https://supabase.com/docs
