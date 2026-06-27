"""
Security utilities for the application.
Includes input validation, security headers, and malicious request detection.
Rate limiting is handled by SlowAPI (see core/rate_limiter.py).
"""
import time
import hashlib
import re
import uuid
from typing import Optional, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging_config import get_logger

logger = get_logger("security")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check for forwarded IP (from proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct IP
    return request.client.host if request.client else "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# Security Middleware
# ═══════════════════════════════════════════════════════════════════════════

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for security headers and request validation.
    """
    
    # Maximum request body size (10MB)
    MAX_REQUEST_SIZE = 10 * 1024 * 1024
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        client_ip = get_client_ip(request)
        logger.debug(f"→ {request.method} {request.url.path} from {client_ip}")
        
        # Check request body size before processing
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.MAX_REQUEST_SIZE:
                logger.warning(f"⚠️ Request body too large from {client_ip}: {content_length} bytes")
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"error": "Request body too large. Maximum 10MB allowed."}
                )
        
        # Check for suspicious patterns
        if self._is_suspicious_request(request):
            logger.warning(f"⚠️ Suspicious request detected from {client_ip}: {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid request"}
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
            
            # Log response
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(f"← {request.method} {request.url.path} → {response.status_code} ({duration_ms:.0f}ms)")
            
            return response
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"✗ {request.method} {request.url.path} failed after {duration_ms:.0f}ms: "
                f"{type(e).__name__}: {str(e)}"
            )
            raise
    
    def _is_suspicious_request(self, request: Request) -> bool:
        """Detect potentially malicious requests."""
        path = request.url.path.lower()
        
        # Check for common attack patterns
        suspicious_patterns = [
            "../",  # Path traversal
            "..\\",  # Path traversal (Windows)
            "<script",  # XSS attempt
            "javascript:",  # XSS attempt
            "eval(",  # Code injection
            "exec(",  # Code injection
            "system(",  # Command injection
            "' or '1'='1",  # SQL injection
            "union select",  # SQL injection
            "drop table",  # SQL injection
            "; rm -rf",  # Command injection
        ]
        
        for pattern in suspicious_patterns:
            if pattern in path:
                return True
        
        # Check for suspicious headers
        user_agent = request.headers.get("user-agent", "").lower()
        if any(bot in user_agent for bot in ["scanner", "crawler", "bot"]) and "googlebot" not in user_agent:
            # Allow legitimate bots like Googlebot
            pass
        
        return False


# ═══════════════════════════════════════════════════════════════════════════
# Input Validation
# ═══════════════════════════════════════════════════════════════════════════

def validate_file_size(file_bytes: bytes, max_size_mb: int = 10) -> None:
    """Validate uploaded file size."""
    max_bytes = max_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        logger.warning(f"File size exceeded: {len(file_bytes)} bytes (max: {max_bytes})")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {max_size_mb}MB."
        )


def validate_file_type(filename: str, allowed_types: list[str]) -> None:
    """Validate file extension."""
    ext = filename.lower().split(".")[-1]
    if ext not in allowed_types:
        logger.warning(f"Invalid file type: {ext} (allowed: {allowed_types})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    import re
    import os
    
    # Get basename (remove any path)
    filename = os.path.basename(filename)
    
    # Remove any non-alphanumeric characters except .-_
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Ensure it doesn't start with a dot (hidden file)
    if filename.startswith('.'):
        filename = '_' + filename[1:]
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


def validate_text_length(
    text: str, 
    max_length: int, 
    field_name: str = "text",
    min_length: int = 0
) -> None:
    """
    Validate text input length.
    
    Args:
        text: Input text to validate
        max_length: Maximum allowed length
        field_name: Name of the field (for error messages)
        min_length: Minimum required length (default: 0)
    
    Raises:
        HTTPException: If text length is invalid
    """
    text_len = len(text) if text else 0
    
    if text_len < min_length:
        logger.warning(f"{field_name} too short: {text_len} chars (min: {min_length})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is too short. Minimum {min_length} characters required."
        )
    
    if text_len > max_length:
        logger.warning(f"{field_name} too long: {text_len} chars (max: {max_length})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is too long. Maximum {max_length} characters allowed."
        )


# ═══════════════════════════════════════════════════════════════════════════
# Advanced Input Validation
# ═══════════════════════════════════════════════════════════════════════════

def validate_uuid(value: str, field_name: str = "ID") -> str:
    """
    Validate UUID format.
    
    Args:
        value: UUID string to validate
        field_name: Name of the field (for error messages)
    
    Returns:
        str: Validated UUID string
    
    Raises:
        HTTPException: If UUID format is invalid
    """
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required."
        )
    
    try:
        # Try to parse as UUID
        uuid_obj = uuid.UUID(value)
        return str(uuid_obj)
    except (ValueError, AttributeError):
        logger.warning(f"Invalid UUID format for {field_name}: {value}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name} format."
        )


def sanitize_text_input(
    text: str,
    max_length: int = 100000,
    allow_html: bool = False,
    field_name: str = "text"
) -> str:
    """
    Sanitize text input to prevent XSS and injection attacks.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML tags (default: False)
        field_name: Name of the field (for error messages)
    
    Returns:
        str: Sanitized text
    
    Raises:
        HTTPException: If input is invalid
    """
    if not isinstance(text, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a string."
        )
    
    # Check length
    if len(text) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} exceeds maximum length of {max_length} characters."
        )
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Remove null bytes (security risk)
    text = text.replace('\x00', '')
    
    # If HTML not allowed, escape/remove HTML tags
    if not allow_html:
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript protocol
            r'on\w+\s*=',  # Event handlers (onclick, onerror, etc.)
            r'<iframe[^>]*>',  # Iframes
            r'<object[^>]*>',  # Object tags
            r'<embed[^>]*>',  # Embed tags
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected in {field_name}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{field_name} contains potentially dangerous content."
                )
    
    return text


def validate_job_description(jd_text: str) -> str:
    """
    Validate and sanitize job description input.
    
    Args:
        jd_text: Job description text
    
    Returns:
        str: Validated and sanitized job description
    
    Raises:
        HTTPException: If validation fails
    """
    # Sanitize input
    jd_text = sanitize_text_input(
        jd_text,
        max_length=50000,  # 50k chars max for JD
        allow_html=False,
        field_name="Job description"
    )
    
    # Check minimum length
    if len(jd_text) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description is too short. Please provide at least 50 characters."
        )
    
    # Check if it contains actual content (not just special characters)
    alphanumeric_count = sum(c.isalnum() for c in jd_text)
    if alphanumeric_count < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job description does not contain sufficient readable content."
        )
    
    return jd_text


def validate_resume_text(resume_text: str) -> str:
    """
    Validate and sanitize resume text input.
    
    Args:
        resume_text: Resume text content
    
    Returns:
        str: Validated and sanitized resume text
    
    Raises:
        HTTPException: If validation fails
    """
    # Sanitize input
    resume_text = sanitize_text_input(
        resume_text,
        max_length=100000,  # 100k chars max for resume
        allow_html=False,
        field_name="Resume text"
    )
    
    # Check minimum length
    if len(resume_text) < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume text is too short. Please provide at least 100 characters."
        )
    
    return resume_text


def validate_string_choice(
    value: str,
    allowed_values: List[str],
    field_name: str = "field",
    case_sensitive: bool = False
) -> str:
    """
    Validate that a string is one of the allowed choices.
    
    Args:
        value: Input value to validate
        allowed_values: List of allowed values
        field_name: Name of the field (for error messages)
        case_sensitive: Whether comparison is case-sensitive
    
    Returns:
        str: Validated value
    
    Raises:
        HTTPException: If value is not in allowed list
    """
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required."
        )
    
    # Compare values
    compare_value = value if case_sensitive else value.lower()
    compare_allowed = allowed_values if case_sensitive else [v.lower() for v in allowed_values]
    
    if compare_value not in compare_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}. Allowed values: {', '.join(allowed_values)}"
        )
    
    return value


def validate_integer_range(
    value: int,
    min_value: int,
    max_value: int,
    field_name: str = "value"
) -> int:
    """
    Validate that an integer is within a specified range.
    
    Args:
        value: Integer value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field (for error messages)
    
    Returns:
        int: Validated value
    
    Raises:
        HTTPException: If value is out of range
    """
    if not isinstance(value, int):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be an integer."
        )
    
    if value < min_value or value > max_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be between {min_value} and {max_value}."
        )
    
    return value


def validate_email(email: str) -> str:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
    
    Returns:
        str: Validated email address
    
    Raises:
        HTTPException: If email format is invalid
    """
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required."
        )
    
    # Basic email regex (RFC 5322 compliant)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format."
        )
    
    # Check length
    if len(email) > 320:  # RFC 5321 limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is too long."
        )
    
    return email.lower()


def validate_list_length(
    items: List,
    max_items: int,
    min_items: int = 0,
    field_name: str = "list"
) -> List:
    """
    Validate list length.
    
    Args:
        items: List to validate
        max_items: Maximum number of items allowed
        min_items: Minimum number of items required
        field_name: Name of the field (for error messages)
    
    Returns:
        List: Validated list
    
    Raises:
        HTTPException: If list length is invalid
    """
    if not isinstance(items, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must be a list."
        )
    
    if len(items) < min_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must contain at least {min_items} items."
        )
    
    if len(items) > max_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} cannot contain more than {max_items} items."
        )
    
    return items


def detect_code_injection_attempt(text: str) -> bool:
    """
    Detect potential code injection attempts in text input.
    
    Args:
        text: Input text to check
    
    Returns:
        bool: True if potential injection detected, False otherwise
    """
    # Patterns that might indicate code injection
    dangerous_patterns = [
        r'__import__',  # Python import
        r'eval\s*\(',  # Eval function
        r'exec\s*\(',  # Exec function
        r'compile\s*\(',  # Compile function
        r'os\.system',  # OS system calls
        r'subprocess\.',  # Subprocess
        r'open\s*\([^)]*["\'][rwa]',  # File operations
        r'\$\(.*\)',  # Shell command substitution
        r'`.*`',  # Shell backticks
        r';\s*rm\s+-rf',  # Dangerous shell command
        r';\s*curl\s+',  # Outbound connections
        r';\s*wget\s+',  # Outbound connections
        r'<\?php',  # PHP code
        r'<%.*%>',  # ASP/JSP code
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def validate_no_code_injection(text: str, field_name: str = "input") -> str:
    """
    Validate that text doesn't contain code injection attempts.
    
    Args:
        text: Text to validate
        field_name: Name of the field (for error messages)
    
    Returns:
        str: Validated text
    
    Raises:
        HTTPException: If potential injection detected
    """
    if detect_code_injection_attempt(text):
        logger.warning(f"Potential code injection detected in {field_name}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} contains potentially dangerous content."
        )
    
    return text


# ═══════════════════════════════════════════════════════════════════════════
# API Key / Token Utilities
# ═══════════════════════════════════════════════════════════════════════════

def hash_api_key(api_key: str) -> str:
    """Hash API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(provided: str, stored_hash: str) -> bool:
    """Verify API key against stored hash."""
    return hash_api_key(provided) == stored_hash


# ═══════════════════════════════════════════════════════════════════════════
# Error Response Helper
# ═══════════════════════════════════════════════════════════════════════════

def create_error_response(
    error: Exception,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    include_details: bool = False,
) -> JSONResponse:
    """Create standardized error response."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Log error
    logger.error(f"Error response: {error_type}: {error_msg}")
    
    response_data = {
        "error": error_type if include_details else "An error occurred",
        "message": error_msg if include_details else "Please try again later",
    }
    
    if include_details:
        import traceback
        response_data["traceback"] = traceback.format_exc()
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )
