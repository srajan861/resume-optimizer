# Groq API, Rate Limiting & Throttling — Complete Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Groq API Integration](#groq-api-integration)
3. [Rate Limiting (Per-User Protection)](#rate-limiting-per-user-protection)
4. [Throttling (Global API Protection)](#throttling-global-api-protection)
5. [How They Work Together](#how-they-work-together)
6. [Monitoring & Metrics](#monitoring--metrics)
7. [Troubleshooting](#troubleshooting)
8. [Configuration](#configuration)

---

## Overview

This application uses a **two-layer protection system** to ensure reliable operation while staying within Groq's API limits:

1. **Rate Limiting** — Protects our API from abuse by limiting requests per user/IP
2. **Throttling** — Protects Groq's API by limiting concurrent LLM calls globally

### Why Both?

- **Rate Limiting**: Prevents individual users from overwhelming our API (per-user quotas)
- **Throttling**: Prevents ALL users combined from exceeding Groq's 30 RPM limit (global concurrency)

Think of it as:
- **Rate Limiting** = Traffic cop for each user
- **Throttling** = Global queue manager for Groq API

---

## Groq API Integration

### What is Groq?

Groq is a high-performance LLM API provider that offers:
- **Model**: Llama 3.3 70B (versatile, fast, high-quality)
- **Free Tier Limit**: 30 RPM (Requests Per Minute)
- **Advantages**: Low latency, cost-effective, good quality

### Where Groq is Used

The application makes Groq API calls in **9 different operations**:

| Operation | Endpoint | Groq Calls | Purpose |
|-----------|----------|------------|---------|
| **Full Analysis** | `POST /api/analyze` | 6-7 | Recruiter simulation, JD intelligence, strength breakdown, bullet rewriting, semantic embeddings (2 calls) |
| **Cover Letter** | `POST /api/cover-letter` | 1 | Generate tailored cover letter |
| **Skill Gap Roadmap** | `POST /api/skill-gap` | 1 | Generate learning roadmap |
| **Auto-Edit Suggestions** | `POST /api/auto-edit-suggestions` | 1 | Generate AI edit suggestions |
| **Bullet Rewriting** | `POST /api/rewrite` | 1 | Standalone bullet rewriting |
| **JD Intelligence** | (internal) | 1 | Extract structured data from JD |
| **Strength Breakdown** | (internal) | 1 | Score resume across dimensions |
| **Recruiter Simulation** | (internal) | 1 | Simulate recruiter feedback |
| **Semantic Embeddings** | (internal) | 1 | Generate embedding vectors |

### Files Using Groq API

```
backend/services/
├── llm_service.py          # Main LLM operations (8 functions)
└── embeddings.py           # Semantic similarity embeddings (1 function)
```

### All Groq API Functions

#### llm_service.py (8 throttled functions)
1. `simulate_recruiter()` — Evaluates resume through recruiter persona
2. `rewrite_bullet_points()` / `_rewrite_batch()` — Rewrites weak bullets
3. `generate_cover_letter()` — Creates tailored cover letters
4. `extract_jd_intelligence()` — Parses job descriptions
5. `generate_skill_gap_roadmap()` — Builds learning roadmaps
6. `analyze_strength_breakdown()` — Multi-dimensional scoring
7. `generate_auto_edit_suggestions()` — AI-powered edit suggestions
8. `_call_groq_api()` — Central throttled API wrapper

#### embeddings.py (1 throttled function)
1. `generate_embedding()` — Creates semantic embeddings

**All 9 functions are wrapped with `@groq_throttle` decorator** to ensure global rate limit compliance.

---

## Rate Limiting (Per-User Protection)

### Technology: SlowAPI

**Library**: [SlowAPI](https://slowapi.readthedocs.io/) — Industry-standard, battle-tested rate limiting  
**Method**: Sliding window, IP-based tracking  
**Storage**: In-memory (suitable for single-server deployments)

### Rate Limit Tiers

Rate limits are **aligned with Groq's 30 RPM limit** to prevent exceeding it:

| Tier | Limit | Window | Applied To | Groq Calls |
|------|-------|--------|------------|------------|
| **ai_heavy** | 8/hour | 1 hour | `/api/analyze`, `/api/apply-edits` | 6-7 per request |
| **ai_medium** | 15/hour | 1 hour | `/api/cover-letter`, `/api/skill-gap` | 1 per request |
| **ai_light** | 20/hour | 1 hour | `/api/auto-edit-suggestions`, `/api/rewrite` | 1 per request |
| **upload** | 20/hour | 1 hour | `/api/upload-resume` | 0 |
| **download** | 100/hour | 1 hour | File downloads | 0 |
| **api** | 100/minute | 1 minute | General API calls | Varies |
| **auth** | 10/5 minutes | 5 minutes | Authentication | 0 |

### Why These Limits?

**Math Behind `ai_heavy` (8/hour)**:
```
8 requests/hour × 7 Groq calls/request = 56 Groq calls/hour
56 calls/hour ÷ 60 minutes = ~0.93 calls/minute per user

With 10 concurrent users:
10 users × 0.93 calls/min = 9.3 calls/min (safe under 30 RPM)

Even with 20 concurrent users:
20 users × 0.93 calls/min = 18.6 calls/min (still under 30 RPM)
```

**Buffer**: Throttling layer adds an additional 5 RPM buffer for safety.

### How Rate Limiting Works

1. **Request comes in** → IP address extracted
2. **Check limit** → SlowAPI checks if IP has exceeded limit
3. **Allow or Block**:
   - **Under limit** → Request proceeds
   - **Over limit** → Return `429 Too Many Requests`

### Rate Limit Response

**Status Code**: `429 Too Many Requests`

**Response Body**:
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. 1 per 1 minute",
  "retry_after": "Please wait a few minutes before trying again"
}
```

**Headers**:
```http
Retry-After: 60
```

### Implementation

**File**: `backend/core/rate_limiter.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

RATE_LIMITS = {
    "ai_heavy": "8/hour",
    "ai_medium": "15/hour",
    "ai_light": "20/hour",
    "upload": "20/hour",
    "download": "100/hour",
    "api": "100/minute",
    "auth": "10/5minutes",
}
```

**Usage in Routers**:
```python
from core.rate_limiter import limiter, get_rate_limit

@router.post("/analyze")
@limiter.limit(get_rate_limit("ai_heavy"))
async def analyze_resume(request: Request, req: AnalyzeRequest):
    # Rate limited to 8 requests/hour per IP
    ...
```

---

## Throttling (Global API Protection)

### Technology: asyncio.Semaphore

**Method**: Global semaphore with max concurrent slots  
**Scope**: Applies to **all users combined** (not per-user)  
**Purpose**: Ensure we never exceed Groq's 30 RPM limit globally

### Configuration

**File**: `backend/core/throttle.py`

```python
GROQ_RPM_LIMIT = 30          # Groq's free tier limit
GROQ_BUFFER = 5              # Safety buffer
MAX_CONCURRENT_GROQ_CALLS = 25  # 30 - 5 = 25 concurrent calls max

groq_semaphore = asyncio.Semaphore(MAX_CONCURRENT_GROQ_CALLS)
```

### How Throttling Works

1. **Before Groq call** → Acquire semaphore slot
2. **Slot available?**
   - **Yes** → Make API call, release slot when done
   - **No** → **Wait** until a slot becomes available (automatic queuing)
3. **After call completes** → Slot released for next request

### The `@groq_throttle` Decorator

All Groq API calls are wrapped with this decorator:

```python
from core.throttle import groq_throttle

@groq_throttle
async def _call_groq_api(prompt: str, model: str = MODEL) -> str:
    client = get_client()
    response = client.chat.completions.create(...)
    return response.choices[0].message.content
```

**What it does**:
1. Checks available slots
2. Waits if all 25 slots are occupied
3. Logs warnings at 80% capacity (20/25 slots)
4. Logs alerts at 90% capacity (23/25 slots)
5. Tracks metrics (total calls, throttled calls, failed calls)

### Throttling vs Rate Limiting

| Feature | Rate Limiting | Throttling |
|---------|---------------|------------|
| **Scope** | Per-user/IP | Global (all users) |
| **Purpose** | Prevent individual abuse | Protect Groq API |
| **Limit Type** | Requests per time window | Concurrent requests |
| **Response** | 429 error + block | Automatic queuing + wait |
| **Technology** | SlowAPI | asyncio.Semaphore |
| **Storage** | In-memory cache | In-memory semaphore |

### Metrics Tracking

Throttling tracks the following metrics (reset hourly):

```python
_call_metrics = {
    "total_calls": 0,        # Total Groq calls made
    "throttled_calls": 0,    # Calls that had to wait
    "failed_calls": 0,       # Calls that failed
    "last_reset": time.time(),
}
```

Access metrics via:
```python
from core.throttle import get_groq_metrics

metrics = get_groq_metrics()
# {
#   "total_calls": 120,
#   "throttled_calls": 5,
#   "failed_calls": 0,
#   "available_slots": 23,
#   "max_concurrent": 25,
#   "utilization_percent": 8.0
# }
```

---

## How They Work Together

### Example: 100 Users Making Requests

**Scenario**: 100 users all try to run `/api/analyze` at the same time.

#### Step 1: Rate Limiting (Per-User)
- Each user gets **8 requests/hour** allowance
- First 8 requests from each user: ✅ Allowed
- 9th request from any user: ❌ **Blocked with 429 error**

#### Step 2: Throttling (Global)
- Even if all users are under their rate limit, Groq API can only handle **25 concurrent calls**
- Requests 1-25: ✅ Execute immediately
- Requests 26-100: ⏳ **Wait in queue** until a slot opens
- No errors thrown, just automatic queuing

### Request Flow Diagram

```
User Request
     ↓
┌────────────────────┐
│  Rate Limiter      │ ← Per-user check (SlowAPI)
│  (IP-based)        │
└────────┬───────────┘
         │ Under limit?
         ├─ YES → Continue
         └─ NO  → Return 429
              ↓
┌────────────────────┐
│  Throttle Layer    │ ← Global check (Semaphore)
│  (Global)          │
└────────┬───────────┘
         │ Slot available?
         ├─ YES → Acquire slot
         └─ NO  → Wait in queue
              ↓
┌────────────────────┐
│  Groq API Call     │ ← Make LLM request
└────────┬───────────┘
         │
         ↓ Release slot
    Return result
```

### Concurrency Example

**Scenario**: 50 concurrent users, each running full analysis (7 Groq calls)

**Without Throttling**:
```
50 users × 7 calls = 350 concurrent Groq calls
Groq limit: 30 RPM
Result: ❌ API quota exceeded, requests fail
```

**With Throttling**:
```
Max concurrent: 25 calls
Requests 1-25: Execute immediately
Requests 26-350: Queued and processed as slots free
Average wait time: 2-5 seconds per queued request
Result: ✅ All requests succeed, none exceed Groq's limit
```

---

## Monitoring & Metrics

### Health Check Endpoint

**Endpoint**: `GET /api/status`

**Response**:
```json
{
  "status": "operational",
  "timestamp": 1703123456.789,
  "services": {
    "groq": "operational",
    "supabase": "operational"
  },
  "groq_metrics": {
    "total_calls": 120,
    "throttled_calls": 5,
    "failed_calls": 0,
    "available_slots": 23,
    "max_concurrent": 25,
    "utilization_percent": 8.0
  }
}
```

### Log Monitoring

#### Watch Throttling Warnings
```bash
tail -f backend/logs/resume-optimizer.log | grep "throttling"
```

**Example Logs**:
```
WARNING | ⏳ Groq API throttling: 20/25 calls active (80%+ capacity)
WARNING | 🚨 High Groq API utilization: 23/25 calls
INFO    | 📊 Groq API metrics (last hour): total=120, throttled=5, failed=0
```

#### Watch Rate Limit Violations
```bash
tail -f backend/logs/resume-optimizer.log | grep "Rate limit"
```

**Example Logs**:
```
WARNING | Rate limit exceeded: 192.168.1.1 on /api/analyze
```

### Metrics Dashboard (Future)

You can integrate metrics with monitoring tools:

**Prometheus Example**:
```python
from prometheus_client import Counter, Gauge

groq_calls_total = Counter('groq_calls_total', 'Total Groq API calls')
groq_throttled_total = Counter('groq_throttled_total', 'Throttled Groq calls')
groq_slots_available = Gauge('groq_slots_available', 'Available Groq slots')
```

---

## Troubleshooting

### Issue 1: Users Getting 429 Errors

**Symptoms**:
- Users receive "Rate limit exceeded" message
- Happens after several requests

**Diagnosis**:
```bash
# Check rate limit logs
grep "Rate limit exceeded" backend/logs/resume-optimizer.log

# See which IPs are hitting limits
grep "Rate limit" backend/logs/resume-optimizer.log | awk '{print $10}' | sort | uniq -c
```

**Solutions**:

1. **Increase Rate Limits** (if justified):
   ```python
   # backend/core/rate_limiter.py
   RATE_LIMITS = {
       "ai_heavy": "12/hour",  # Increased from 8
   }
   ```

2. **User Behavior**:
   - Educate users to avoid rapid successive requests
   - Implement better frontend feedback (show remaining quota)

3. **Whitelist VIPs** (optional):
   ```python
   WHITELISTED_IPS = ["192.168.1.100", "10.0.0.5"]
   
   @limiter.limit(get_rate_limit("ai_heavy"), exempt_when=lambda req: req.client.host in WHITELISTED_IPS)
   ```

### Issue 2: Slow Response Times

**Symptoms**:
- Requests take 10+ seconds to complete
- Users experience delays

**Diagnosis**:
```bash
# Check Groq utilization
curl http://localhost:8000/api/status | jq '.groq_metrics.utilization_percent'

# Watch throttling logs
tail -f backend/logs/resume-optimizer.log | grep "throttling"
```

**Possible Causes**:
1. **High utilization** (>80%): Too many concurrent requests
2. **Throttling queue**: Requests waiting for slots

**Solutions**:

1. **Increase Concurrency Limit** (risky — may exceed Groq limit):
   ```python
   # backend/core/throttle.py
   MAX_CONCURRENT_GROQ_CALLS = 28  # Increased from 25 (less buffer)
   ```

2. **Optimize Groq Calls**:
   - Reduce `max_tokens` in prompts
   - Use caching for repeated requests
   - Batch similar operations

3. **Upgrade Groq Plan**:
   - Groq's paid plans have higher RPM limits
   - Example: Pro plan might have 100+ RPM

### Issue 3: Groq API Errors

**Symptoms**:
- 500 errors from Groq
- "API quota exceeded" messages

**Diagnosis**:
```bash
# Check failed calls
grep "Groq API call failed" backend/logs/resume-optimizer-errors.log

# Check if we're exceeding 30 RPM
grep "API quota exceeded" backend/logs/resume-optimizer-errors.log
```

**Solutions**:

1. **Verify Throttle Settings**:
   ```python
   # Should be ≤25 to stay under 30 RPM
   assert MAX_CONCURRENT_GROQ_CALLS <= 25
   ```

2. **Check Groq Dashboard**:
   - Log in to [console.groq.com](https://console.groq.com)
   - View usage metrics
   - Verify API key is active

3. **Add Retry Logic** (optional):
   ```python
   from tenacity import retry, stop_after_attempt, wait_exponential
   
   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
   @groq_throttle
   async def _call_groq_api(...):
       ...
   ```

### Issue 4: Throttle Metrics Not Updating

**Symptoms**:
- `/api/status` shows stale metrics
- Utilization always 0%

**Diagnosis**:
```python
# Check semaphore value
from core.throttle import groq_semaphore
print(f"Available slots: {groq_semaphore._value}")
```

**Solution**:
- Metrics reset every hour
- Restart backend if semaphore is stuck:
  ```bash
  pkill -f "python main.py"
  python backend/main.py
  ```

---

## Configuration

### Environment Variables

**File**: `backend/.env`

```bash
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here

# Debug Mode (affects error detail level)
DEBUG=False  # Set to True for development only
```

### Adjusting Rate Limits

**File**: `backend/core/rate_limiter.py`

```python
RATE_LIMITS = {
    "ai_heavy": "8/hour",     # ← Change these values
    "ai_medium": "15/hour",
    "ai_light": "20/hour",
    "upload": "20/hour",
    "download": "100/hour",
    "api": "100/minute",
    "auth": "10/5minutes",
}
```

**After changing**:
1. Restart backend server
2. Test with `curl` or Postman
3. Monitor logs for impact

### Adjusting Throttle Settings

**File**: `backend/core/throttle.py`

```python
# Groq API limits
GROQ_RPM_LIMIT = 30           # ← Update if you upgrade Groq plan
GROQ_BUFFER = 5               # ← Adjust safety buffer (3-10)
MAX_CONCURRENT_GROQ_CALLS = GROQ_RPM_LIMIT - GROQ_BUFFER
```

**Warning**: Setting `MAX_CONCURRENT_GROQ_CALLS` too high will cause Groq API errors!

**Safe ranges**:
- Free tier (30 RPM): 20-25 concurrent
- Pro tier (100 RPM): 80-95 concurrent

### Multi-Server Deployment

If deploying to **multiple servers** (e.g., Kubernetes, load balancer), in-memory rate limiting won't work properly.

**Solution**: Use Redis for distributed rate limiting.

**Setup**:
```bash
pip install redis slowapi[redis]
```

**Configuration**:
```python
# backend/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from redis import Redis

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
)
```

**Environment Variables**:
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
```

---

## Summary

### ✅ What We Have

| Feature | Technology | Purpose | Status |
|---------|-----------|---------|--------|
| **Rate Limiting** | SlowAPI | Per-user quotas | ✅ Active |
| **Throttling** | asyncio.Semaphore | Global Groq protection | ✅ Active |
| **Logging** | Structured logs | Monitor usage | ✅ Active |
| **Metrics** | In-memory tracking | Real-time stats | ✅ Active |
| **Health Check** | `/api/status` endpoint | System monitoring | ✅ Active |

### 🎯 Key Numbers

- **Groq API Limit**: 30 RPM (free tier)
- **Throttle Limit**: 25 concurrent calls (5 RPM buffer)
- **Rate Limits**:
  - Heavy AI: 8/hour per user
  - Medium AI: 15/hour per user
  - Light AI: 20/hour per user
- **Protected Endpoints**: 11 endpoints with rate limits
- **Throttled Functions**: 9 functions with `@groq_throttle`

### 📂 Key Files

```
backend/
├── core/
│   ├── rate_limiter.py      # Rate limiting config (SlowAPI)
│   ├── throttle.py          # Throttling layer (semaphore)
│   └── logging_config.py    # Logging setup
├── services/
│   ├── llm_service.py       # 8 throttled Groq functions
│   └── embeddings.py        # 1 throttled Groq function
└── routers/
    ├── analysis.py          # Rate-limited analysis endpoints
    └── auto_editor.py       # Rate-limited editor endpoints
```

---

## Additional Resources

- **SlowAPI Docs**: https://slowapi.readthedocs.io/
- **Groq API Docs**: https://console.groq.com/docs
- **Python asyncio**: https://docs.python.org/3/library/asyncio.html
- **Groq Console**: https://console.groq.com (view usage stats)

---

**Status**: ✅ PRODUCTION-READY  
**Last Updated**: 2026-06-24
