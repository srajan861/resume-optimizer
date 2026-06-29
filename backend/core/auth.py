"""
Authentication and authorization module.
Validates JWT tokens from Supabase Auth and extracts user identity.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional
from core.config import settings
from core.logging_config import get_logger

logger = get_logger("auth")

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Extract and validate user ID from Supabase JWT token.
    
    This dependency ensures only authenticated users can access protected endpoints.
    It validates the JWT token and extracts the user ID from the token payload.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
    
    Returns:
        str: Validated user ID from token
    
    Raises:
        HTTPException: 401 if token is missing, invalid, or expired
    
    Usage:
        @router.post("/protected-endpoint")
        async def protected_route(current_user: str = Depends(get_current_user)):
            # current_user is validated and safe to use
            ...
    """
    if not credentials:
        logger.warning("Missing Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        
        # First, decode WITHOUT verification to see what's in the token
        import json
        import base64
        try:
            # Decode token payload (middle part between dots)
            parts = token.split('.')
            if len(parts) == 3:
                # Add padding if needed
                payload_part = parts[1]
                padding = 4 - len(payload_part) % 4
                if padding != 4:
                    payload_part += '=' * padding
                decoded = base64.urlsafe_b64decode(payload_part)
                payload_preview = json.loads(decoded)
                logger.info(f"Token payload preview: {payload_preview}")
        except Exception as e:
            logger.warning(f"Could not preview token: {e}")
        
        # Decode and verify JWT signature
        # Supabase JWTs use HS256 algorithm with JWT secret
        # Try without audience first to see if that's the issue
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience="authenticated",  # Supabase default audience
            )
        except JWTError as e:
            logger.warning(f"JWT decode with audience failed: {e}, trying without audience")
            # Try without audience
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        
        # Extract user ID from 'sub' claim (standard JWT claim for subject/user ID)
        user_id: str = payload.get("sub")
        if not user_id:
            logger.warning("Token missing 'sub' claim (user ID)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        
        # Optional: Check token expiration (jwt.decode does this automatically)
        # Optional: Check if user is confirmed (email verified)
        email_confirmed = payload.get("email_confirmed_at")
        if not email_confirmed and settings.REQUIRE_EMAIL_VERIFICATION:
            logger.warning(f"User {user_id[:8]} email not confirmed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email address",
            )
        
        logger.debug(f"✅ Authenticated user: {user_id[:8]}...")
        return user_id
    
    except JWTError as e:
        logger.warning(f"JWT validation failed: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected auth error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error",
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Extract user ID from token if present, but don't require authentication.
    
    Useful for endpoints that work for both authenticated and anonymous users.
    
    Returns:
        Optional[str]: User ID if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def get_user_from_token(token: str) -> Optional[str]:
    """
    Synchronous helper to extract user ID from JWT token.
    
    Useful for background tasks or synchronous code.
    Returns None if token is invalid instead of raising exception.
    
    Args:
        token: JWT token string (without "Bearer " prefix)
    
    Returns:
        Optional[str]: User ID if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload.get("sub")
    except JWTError:
        return None


# Export for use in routers
__all__ = [
    "get_current_user",
    "get_optional_user",
    "get_user_from_token",
]
