# Input Validation & Security

## 📋 Table of Contents

1. [Overview](#overview)
2. [Why Input Validation?](#why-input-validation)
3. [SQL Injection - Not a Concern](#sql-injection---not-a-concern)
4. [What We Validate](#what-we-validate)
5. [Validation Implementation](#validation-implementation)
6. [Security Measures](#security-measures)
7. [Validation by Endpoint](#validation-by-endpoint)
8. [Error Handling](#error-handling)
9. [Testing Validation](#testing-validation)

---

## Overview

This document explains the comprehensive input validation and security measures implemented in the Resume Optimizer application.

### Key Points

✅ **SQL Injection**: NOT a concern (using Supabase ORM with parameterized queries)  
✅ **Input Validation**: REQUIRED (prevents business logic attacks, XSS, cost abuse)  
✅ **Multiple Layers**: Pydantic schemas + custom validators + middleware  
✅ **Practical Approach**: Focused on real threats, not theoretical risks

---

## Why Input Validation?

Even though SQL injection is impossible with Supabase's parameterized queries, input validation is **critical** for:

### 1. **Business Logic Attacks**
```
❌ Without Validation:
- User uploads 50MB "resume" → server crashes
- User sends 100,000 character job description → expensive LLM calls
- User passes 1000 bullet points → timeout/resource exhaustion

✅ With Validation:
- File size limited to 10MB
- Text fields have maximum lengths
- Lists have maximum item counts
```

### 2. **XSS Prevention**
```
❌ Without Validation:
User input: "<script>alert('XSS')</script>"
→ Stored in database
→ Executed in other users' browsers

✅ With Validation:
Dangerous patterns detected and blocked
→ 400 Bad Request error
→ User cannot inject malicious content
```

### 3. **Cost Control**
```
❌ Without Validation:
User sends 50,000 character job description
→ Groq API call costs $$$
→ Abuse can drain your credits

✅ With Validation:
Job descriptions limited to 50,000 characters
→ Reasonable API costs
→ Protected from abuse
```

### 4. **Data Integrity**
```
❌ Without Validation:
User provides invalid UUID: "abc123"
→ Database query fails
→ 500 Internal Server Error
→ Poor user experience

✅ With Validation:
UUID format validated upfront
→ Clear error message
→ 400 Bad Request with helpful detail
→ Better debugging
```

---

## SQL Injection - Not a Concern

### Why SQL Injection is Impossible

Your application uses **Supabase Python client**, which **automatically parameterizes all queries**.

**Example:**
```python
# Your code:
supabase.table("resumes").select("*").eq("user_id", user_input).execute()

# What Supabase does internally:
# SELECT * FROM resumes WHERE user_id = $1
# Parameters: [user_input]
# 
# SQL injection is IMPOSSIBLE because user input is NEVER
# concatenated into the SQL string - it's passed as a parameter
```

**What SQL Injection Looks Like (NOT possible in your app):**
```python
# ❌ Vulnerable (raw SQL concatenation) - YOU DON'T DO THIS
query = f"SELECT * FROM resumes WHERE user_id = '{user_input}'"
# If user_input = "'; DROP TABLE resumes; --"
# Query becomes: SELECT * FROM resumes WHERE user_id = ''; DROP TABLE resumes; --'
# → Database destroyed!

# ✅ Safe (parameterized query) - THIS IS WHAT SUPABASE DOES
query = "SELECT * FROM resumes WHERE user_id = $1"
params = [user_input]
# Even if user_input = "'; DROP TABLE resumes; --"
# Query safely treats it as a literal string value
# → No injection possible
```

**Bottom Line**: You're using an ORM (Supabase client) that prevents SQL injection by design. **You don't need SQL injection protection.**

---

## What We Validate

### 1. **File Uploads**
| Validation | Limit | Reason |
|------------|-------|--------|
| File size | 10 MB | Prevent memory exhaustion |
| File type | PDF, DOCX only | Prevent malware/executables |
| Filename | Sanitized | Prevent path traversal |
| Content | Min 50 chars | Ensure valid resume |

### 2. **Text Inputs**

#### Job Descriptions
| Validation | Limit | Reason |
|------------|-------|--------|
| Minimum length | 50 characters | Ensure meaningful content |
| Maximum length | 50,000 characters | Prevent API abuse |
| Alphanumeric check | ≥30 alphanumeric chars | Detect garbage input |
| No code injection | Pattern detection | Prevent malicious content |

#### Resume Text
| Validation | Limit | Reason |
|------------|-------|--------|
| Minimum length | 100 characters | Ensure valid resume |
| Maximum length | 100,000 characters | Prevent memory issues |
| No code injection | Pattern detection | Security |

#### Names & Titles
| Validation | Limit | Reason |
|------------|-------|--------|
| Maximum length | 100-200 chars | Prevent abuse |
| No control characters | Sanitized | Clean data |
| No HTML | Escaped | XSS prevention |

### 3. **UUIDs (IDs)**
| Validation | Method | Reason |
|------------|--------|--------|
| Format check | UUID parsing | Catch invalid IDs early |
| Not empty | Required check | Prevent null errors |
| Trimmed | Whitespace removal | Clean input |

### 4. **Enumerations (Choice Fields)**

**Validated Fields:**
- `role_type`: Must be one of `sde`, `ml`, `analyst`, `general`
- `persona`: Must be one of `standard`, `faang`, `startup`, `hr`
- `tone`: Must be one of `professional`, `enthusiastic`, `concise`
- `format`: Must be one of `pdf`, `docx`, `both`

**Why**: Prevents invalid values that break application logic

### 5. **Lists (Arrays)**

**Validated:**
- Bullet points: 1-20 items, each ≤1000 characters
- Applied suggestions: 1-50 items
- Query parameters: Limit ≤100

**Why**: Prevent DoS via oversized inputs

### 6. **Integers (Numbers)**

**Validated:**
- `max_suggestions`: 1-50 (inclusive)
- Scores: 0-100 (via Pydantic Field validators)

**Why**: Prevent invalid ranges

---

## Validation Implementation

### Layer 1: Pydantic Schema Validation

**Automatic validation on all request models:**

```python
from pydantic import BaseModel, Field, field_validator
import uuid

class AnalyzeRequest(BaseModel):
    resume_id: str = Field(..., min_length=1, max_length=100)
    job_description: str = Field(..., min_length=50, max_length=50000)
    role_type: Optional[str] = Field(default="general", pattern="^(sde|ml|analyst|general)$")
    
    @field_validator('resume_id')
    @classmethod
    def validate_resume_id(cls, v: str) -> str:
        """Validate UUID format."""
        if not v or not v.strip():
            raise ValueError("Resume ID is required")
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError("Invalid resume ID format")
        
        return v.strip()
```

**What Pydantic Validates:**
- ✅ Required fields (not null/empty)
- ✅ String min/max lengths
- ✅ Integer min/max values (ge/le)
- ✅ Regex patterns for enums
- ✅ List length constraints
- ✅ Custom validators with `@field_validator`

**Errors are automatic:**
```json
{
  "detail": [
    {
      "loc": ["body", "job_description"],
      "msg": "ensure this value has at least 50 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### Layer 2: Custom Security Validators

**Located in:** `backend/core/security.py`

#### UUID Validation
```python
def validate_uuid(value: str, field_name: str = "ID") -> str:
    """Validate UUID format."""
    if not value:
        raise HTTPException(400, f"{field_name} is required.")
    
    try:
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj)
    except ValueError:
        raise HTTPException(400, f"Invalid {field_name} format.")
```

#### Text Sanitization
```python
def sanitize_text_input(
    text: str,
    max_length: int = 100000,
    allow_html: bool = False,
    field_name: str = "text"
) -> str:
    """Sanitize text to prevent XSS and injection."""
    # Check length
    if len(text) > max_length:
        raise HTTPException(400, f"{field_name} exceeds maximum length.")
    
    # Strip whitespace
    text = text.strip()
    
    # Remove null bytes (security risk)
    text = text.replace('\x00', '')
    
    # If HTML not allowed, check for dangerous patterns
    if not allow_html:
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',  # Event handlers
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(400, f"{field_name} contains dangerous content.")
    
    return text
```

#### Job Description Validation
```python
def validate_job_description(jd_text: str) -> str:
    """Validate and sanitize job description."""
    # Sanitize
    jd_text = sanitize_text_input(jd_text, max_length=50000, field_name="Job description")
    
    # Check minimum length
    if len(jd_text) < 50:
        raise HTTPException(400, "Job description too short (min 50 chars)")
    
    # Check for actual content (not just special characters)
    alphanumeric_count = sum(c.isalnum() for c in jd_text)
    if alphanumeric_count < 30:
        raise HTTPException(400, "Job description lacks readable content")
    
    return jd_text
```

#### Code Injection Detection
```python
def detect_code_injection_attempt(text: str) -> bool:
    """Detect potential code injection."""
    dangerous_patterns = [
        r'__import__',
        r'eval\s*\(',
        r'exec\s*\(',
        r'os\.system',
        r'\$\(.*\)',  # Shell command substitution
        r';\s*rm\s+-rf',
        r'<\?php',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False

def validate_no_code_injection(text: str, field_name: str = "input") -> str:
    """Validate no code injection attempts."""
    if detect_code_injection_attempt(text):
        logger.warning(f"Code injection detected in {field_name}")
        raise HTTPException(400, f"{field_name} contains dangerous content.")
    
    return text
```

### Layer 3: Endpoint-Level Validation

**Applied in routers:**

```python
@router.post("/analyze")
async def analyze_resume(
    req: AnalyzeRequest,  # ← Pydantic validation
    current_user: str = Depends(get_current_user),  # ← Authentication
):
    # Layer 2: Custom validation
    from core.security import validate_uuid, validate_job_description, validate_no_code_injection
    
    # Validate UUID
    resume_id = validate_uuid(req.resume_id, "Resume ID")
    
    # Validate and sanitize JD
    job_description = validate_job_description(req.job_description)
    
    # Check for code injection
    validate_no_code_injection(job_description, "Job description")
    
    # Proceed with business logic...
```

### Layer 4: Security Middleware

**Global request validation:**

```python
class SecurityMiddleware(BaseHTTPMiddleware):
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next):
        # Check request body size
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request body too large. Max 10MB."}
                )
        
        # Check for suspicious patterns in URL
        if self._is_suspicious_request(request):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request"}
            )
        
        # Add security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
```

---

## Security Measures

### 1. **XSS Prevention**

**What is XSS?** Cross-Site Scripting - injecting malicious scripts into web pages

**How We Prevent It:**
```python
# Detect dangerous HTML/JavaScript
dangerous_patterns = [
    r'<script[^>]*>.*?</script>',
    r'javascript:',
    r'on\w+\s*=',  # onclick, onerror, etc.
    r'<iframe[^>]*>',
]

# Block if detected
if any(re.search(p, text, re.IGNORECASE) for p in dangerous_patterns):
    raise HTTPException(400, "Input contains potentially dangerous content")
```

**Security Headers:**
```python
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
```

### 2. **Path Traversal Prevention**

**Attack Example:**
```
Filename: "../../etc/passwd"
→ Tries to access system files
```

**Our Protection:**
```python
def sanitize_filename(filename: str) -> str:
    # Get basename only (remove paths)
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Prevent hidden files
    if filename.startswith('.'):
        filename = '_' + filename[1:]
    
    return filename
```

### 3. **Command Injection Prevention**

**Attack Example:**
```
Input: "; rm -rf /"
→ Tries to execute system commands
```

**Our Protection:**
```python
# Detect shell commands
command_patterns = [
    r'\$\(.*\)',      # $(command)
    r'`.*`',          # `command`
    r';\s*rm\s+-rf',  # Dangerous delete
    r';\s*curl\s+',   # Outbound connections
]

# Block if detected
if detect_code_injection_attempt(text):
    raise HTTPException(400, "Dangerous content detected")
```

### 4. **Request Size Limits**

**Prevents:**
- Memory exhaustion
- DoS attacks
- Resource abuse

**Limits:**
```python
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024     # 10MB
MAX_TEXT_LENGTH = 100,000 chars      # Resume
MAX_JD_LENGTH = 50,000 chars         # Job description
```

### 5. **Null Byte Injection Prevention**

**Attack:**
```
Input: "filename.pdf\x00.exe"
→ Some systems stop at \x00, see "filename.pdf"
→ Actually executes "filename.pdf\x00.exe" (executable)
```

**Protection:**
```python
# Remove null bytes
text = text.replace('\x00', '')
```

---

## Validation by Endpoint

### Protected Endpoints (Require Auth + Validation)

#### `/api/upload-resume`
**Validates:**
- ✅ File type (PDF, DOCX only)
- ✅ File size (≤10MB)
- ✅ Filename (sanitized)
- ✅ Content (≥50 chars extracted text)
- ✅ JWT token (authentication)

#### `/api/analyze`
**Validates:**
- ✅ Resume ID (UUID format)
- ✅ Job description (50-50,000 chars, alphanumeric content)
- ✅ Role type (enum: sde|ml|analyst|general)
- ✅ Persona (enum: standard|faang|startup|hr)
- ✅ No code injection
- ✅ JWT token

#### `/api/cover-letter`
**Validates:**
- ✅ Analysis ID (UUID format)
- ✅ Tone (enum: professional|enthusiastic|concise)
- ✅ Applicant name (≤100 chars, no control chars)
- ✅ Company name (≤200 chars, sanitized)
- ✅ Role title (≤200 chars, sanitized)
- ✅ No code injection
- ✅ JWT token

#### `/api/skill-gap`
**Validates:**
- ✅ Analysis ID (UUID format)
- ✅ JWT token

#### `/api/auto-edit-suggestions`
**Validates:**
- ✅ Analysis ID (UUID format)
- ✅ Max suggestions (1-50)
- ✅ JWT token

#### `/api/apply-edits`
**Validates:**
- ✅ Analysis ID (UUID format)
- ✅ Resume text (100-100,000 chars)
- ✅ Applied suggestions (1-50 items)
- ✅ Format (enum: pdf|docx|both)
- ✅ No code injection
- ✅ JWT token

#### `/api/history`
**Validates:**
- ✅ Limit parameter (≤100)
- ✅ JWT token

#### `/api/evolution/{resume_id}`
**Validates:**
- ✅ Resume ID (UUID format)
- ✅ JWT token

### Public Endpoints (No Auth, Still Validated)

#### `/api/live-feedback`
**Validates:**
- ✅ Resume text (≤100,000 chars)
- ✅ Job description (≤50,000 chars)

#### `/api/red-flags`
**Validates:**
- ✅ Resume text (50-100,000 chars)
- ✅ No code injection

#### `/api/rewrite`
**Validates:**
- ✅ Bullet points (1-20 items, each ≤1000 chars)
- ✅ Job context (≤10,000 chars)
- ✅ No code injection

---

## Error Handling

### Validation Error Responses

**Pydantic Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "resume_id"],
      "msg": "Invalid resume ID format",
      "type": "value_error"
    }
  ]
}
```

**Custom Validation Error (400):**
```json
{
  "detail": "Job description is too short. Minimum 50 characters required."
}
```

**File Upload Error (413):**
```json
{
  "detail": "File too large. Maximum size is 10MB."
}
```

**Authentication Error (401):**
```json
{
  "detail": "Missing authentication credentials"
}
```

**Code Injection Detected (400):**
```json
{
  "detail": "Job description contains potentially dangerous content."
}
```

---

## Testing Validation

### Manual Testing

**Test Invalid UUID:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "invalid-uuid",
    "job_description": "Software engineer position..."
  }'

# Expected: 400 Bad Request
# Response: {"detail": "Invalid Resume ID format"}
```

**Test Short Job Description:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "550e8400-e29b-41d4-a716-446655440000",
    "job_description": "Short"
  }'

# Expected: 422 Unprocessable Entity
# Response: {"detail": [{"loc": ["body", "job_description"], "msg": "ensure this value has at least 50 characters"}]}
```

**Test XSS Attempt:**
```bash
curl -X POST http://localhost:8000/api/red-flags \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "<script>alert(\"XSS\")</script>"
  }'

# Expected: 400 Bad Request
# Response: {"detail": "Resume text contains potentially dangerous content"}
```

**Test Oversized File:**
```bash
# Create 15MB file
dd if=/dev/zero of=large.pdf bs=1M count=15

curl -X POST http://localhost:8000/api/upload-resume \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@large.pdf"

# Expected: 413 Request Entity Too Large
# Response: {"detail": "File too large. Maximum size is 10MB."}
```

### Automated Testing

Create `tests/test_validation.py`:

```python
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_invalid_uuid():
    response = client.post("/api/analyze", json={
        "resume_id": "not-a-uuid",
        "job_description": "A" * 100
    })
    assert response.status_code == 400

def test_short_job_description():
    response = client.post("/api/analyze", json={
        "resume_id": "550e8400-e29b-41d4-a716-446655440000",
        "job_description": "Short"
    })
    assert response.status_code == 422

def test_xss_attempt():
    response = client.post("/api/red-flags", json={
        "resume_text": "<script>alert('XSS')</script>"
    })
    assert response.status_code == 400

def test_valid_input():
    response = client.post("/api/red-flags", json={
        "resume_text": "Software Engineer\n\nExperience:\n- Developed web applications\n- Led a team of 5 engineers"
    })
    assert response.status_code == 200
```

---

## Summary

### ✅ What's Protected

1. **File Uploads**: Size, type, content validation
2. **Text Inputs**: Length limits, content checks, XSS prevention
3. **UUIDs**: Format validation
4. **Enums**: Restricted to allowed values
5. **Lists**: Item count limits
6. **Request Size**: 10MB maximum
7. **Code Injection**: Pattern detection and blocking

### ❌ What's NOT a Concern

1. **SQL Injection**: Impossible with Supabase ORM
2. **NoSQL Injection**: Not using MongoDB/NoSQL databases
3. **LDAP Injection**: Not using LDAP
4. **XML Injection**: Not parsing XML

### 🎯 Practical Security

Your implementation follows a **practical, threat-based approach**:

- ✅ Protects against real risks (XSS, DoS, cost abuse)
- ✅ Uses multiple validation layers (Pydantic + custom + middleware)
- ✅ Provides clear error messages
- ✅ Maintains good user experience
- ❌ Doesn't waste time on impossible attacks (SQL injection with ORM)

### 🚀 Production Ready

Your validation implementation is **production-ready** and protects against:

- Business logic attacks ✅
- XSS attacks ✅
- Command injection ✅
- Path traversal ✅
- DoS via oversized inputs ✅
- API cost abuse ✅
- Data corruption ✅

**Bottom Line**: Your application has comprehensive input validation that addresses real security threats while maintaining a smooth user experience.
