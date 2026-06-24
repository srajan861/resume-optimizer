# Resume Optimizer - Quick Reference Guide

## 🚀 Start the Application

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
Runs on: `http://localhost:8000`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on: `http://localhost:5173`

---

## 📊 Rate Limits (Current)

| Endpoint | Limit | Groq Calls |
|----------|-------|------------|
| `/api/analyze` | 8/hour | 6-7 |
| `/api/cover-letter` | 15/hour | 1 |
| `/api/skill-gap` | 15/hour | 1 |
| `/api/auto-edit-suggestions` | 20/hour | 1 |
| `/api/apply-edits` | 20/hour | 0 |
| `/api/upload-resume` | 20/hour | 0 |

**Groq API Limit**: 30 RPM (free tier)  
**Throttle Limit**: 25 concurrent calls (global)

---

## 🛡️ Security Features

✅ Rate limiting (SlowAPI) - Per-user/IP  
✅ Throttling (Semaphore) - Global Groq API protection  
✅ Input validation (file size, type, text length)  
✅ Security headers (XSS, clickjacking protection)  
✅ Suspicious request detection  
✅ Error masking in production (DEBUG=False)

---

## 📝 Logging

**Location**: `backend/logs/`
- `resume-optimizer.log` - All logs
- `resume-optimizer-errors.log` - Errors only

**Watch logs**:
```bash
tail -f backend/logs/resume-optimizer.log
```

---

## 🔍 Monitoring

### Check System Status
```bash
curl http://localhost:8000/api/status
```

### View Groq Metrics
- Available slots: How many concurrent calls available
- Utilization: % of throttle capacity used
- Total calls: Calls made in last hour
- Throttled calls: Calls that had to wait

---

## 🎯 Key Files

### Core
- `backend/main.py` - FastAPI app with global handlers
- `backend/core/config.py` - Environment settings
- `backend/core/rate_limiter.py` - Rate limiting config
- `backend/core/throttle.py` - Groq API throttling
- `backend/core/security.py` - Input validation & security
- `backend/core/logging_config.py` - Logging setup

### Routers
- `backend/routers/resume.py` - Resume upload
- `backend/routers/analysis.py` - Main analysis pipeline
- `backend/routers/auto_editor.py` - AI-powered editing
- `backend/routers/history.py` - User history
- `backend/routers/evolution.py` - Resume tracking

### Services
- `backend/services/llm_service.py` - All LLM calls (throttled)
- `backend/services/ats_engine.py` - ATS scoring
- `backend/services/embeddings.py` - Semantic matching (throttled)
- `backend/services/latex_service.py` - LaTeX generation
- `backend/services/parser.py` - PDF/DOCX parsing
- `backend/services/storage.py` - Database operations

---

## 🐛 Troubleshooting

### Rate Limit Errors (429)
**Problem**: Too many requests from same IP  
**Solution**: Wait a few minutes or adjust limits in `core/rate_limiter.py`

### Groq API Errors
**Problem**: Exceeding 30 RPM  
**Check**: `/api/status` endpoint for utilization  
**Solution**: Throttling should prevent this automatically

### File Upload Fails
**Check**: File size (max 10MB) and type (PDF/DOCX only)  
**Logs**: Look for validation errors in logs

### LaTeX Generation Issues
**Check**: Resume text quality and length  
**Fallback**: Uses deterministic rule-based generator

---

## 📚 Documentation

1. **IMPLEMENTATION_SUMMARY.md** - Complete project overview
2. **LOGGING_AND_ERROR_HANDLING.md** - Logging guide
3. **RATE_LIMITING_AND_THROTTLING_COMPLETE.md** - Rate limiting details
4. **CACHING_AND_RATE_LIMITING.md** - Caching decision rationale
5. **SECURITY_AND_LOGGING.md** - Security features
6. **QUICK_REFERENCE.md** - This file

---

## 🔧 Environment Variables

### Backend (.env)
```bash
GROQ_API_KEY=your_groq_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_BUCKET=resumes
DEBUG=False  # True for development
MAX_FILE_SIZE_MB=10
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com
```

### Frontend (.env)
```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_API_URL=http://localhost:8000
```

---

## 🎯 Common Tasks

### Update Rate Limits
Edit `backend/core/rate_limiter.py`:
```python
RATE_LIMITS = {
    "ai_heavy": "8/hour",  # Change number here
    ...
}
```

### View Throttle Settings
Check `backend/core/throttle.py`:
```python
MAX_CONCURRENT_GROQ_CALLS = 25  # Adjust if needed
```

### Check Logs for Errors
```bash
grep "ERROR" backend/logs/resume-optimizer.log
```

### Monitor Groq Usage
```bash
grep "Groq" backend/logs/resume-optimizer.log | tail -20
```

---

## ✅ Pre-Deployment Checklist

- [ ] Set `DEBUG=False` in backend/.env
- [ ] Update `ALLOWED_ORIGINS` in backend/.env
- [ ] Run `supabase_schema.sql` in Supabase
- [ ] Create storage bucket: "resumes"
- [ ] Test all endpoints
- [ ] Verify rate limiting works
- [ ] Check logs are rotating
- [ ] Test with production data
- [ ] Monitor `/api/status` endpoint

---

## 🚨 Emergency Commands

### Stop All Processes
```bash
# Backend
pkill -f "python main.py"

# Frontend
pkill -f "npm run dev"
```

### Clear Logs
```bash
cd backend/logs
rm *.log
```

### Reset Rate Limits
Restart the backend server - rate limits reset on restart

---

## 📞 Key Metrics to Monitor

1. **Request Duration** - Should be < 10 seconds
2. **Error Rate** - Should be < 1%
3. **Groq Utilization** - Should stay < 80%
4. **Rate Limit Hits** - Track 429 responses
5. **Throttling Events** - Check warning logs

---

## 🎉 Quick Test

```bash
# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/api/status

# Upload test (replace with actual file)
curl -X POST http://localhost:8000/api/upload-resume \
  -F "file=@resume.pdf" \
  -F "user_id=test-user-123"
```

---

**Need help?** Check the detailed documentation files listed above.
