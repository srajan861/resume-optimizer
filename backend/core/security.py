"""
Security utilities for the application.
Includes input validation, security headers, and malicious request detection.
Rate limiting is handled by SlowAPI (see core/rate_limiter.py).
"""
import time
import hashlib
from typing import Optional
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
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log incoming request
        client_ip = get_client_ip(request)
        logger.debug(f"→ {request.method} {request.url.path} from {client_ip}")
        
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


def validate_text_length(text: str, max_length: int, field_name: str = "text") -> None:
    """Validate text input length."""
    if len(text) > max_length:
        logger.warning(f"{field_name} too long: {len(text)} chars (max: {max_length})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is too long. Maximum {max_length} characters."
        )


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
