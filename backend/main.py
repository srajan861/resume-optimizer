from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import uvicorn
import time
from pathlib import Path

from routers import resume, analysis, history, evolution, auto_editor
from core.config import settings
from core.logging_config import setup_logging, get_logger, log_request
from core.security import SecurityMiddleware
from core.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Setup logging
log_dir = Path(__file__).parent / "logs"
setup_logging(app_name="resume-optimizer", log_level="INFO", log_dir=log_dir)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Resume Optimizer API starting up...")
    logger.info(f"   Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"   CORS Origins: {settings.ALLOWED_ORIGINS}")
    logger.info(f"   Log Directory: {log_dir}")
    yield
    logger.info("🛑 Resume Optimizer API shutting down...")


app = FastAPI(
    title="Resume Optimizer API",
    description="ATS + AI-Powered Resume Analysis Engine with Security & Rate Limiting (SlowAPI)",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.DEBUG else None,  # Hide docs in production
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Add SlowAPI state to app
app.state.limiter = limiter

# Register rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Security Middleware (must be first)
app.add_middleware(SecurityMiddleware)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    request_id = str(time.time())
    
    # Add request ID to headers for tracking
    response = await call_next(request)
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Extract user ID if available (from Supabase auth header)
    user_id = request.headers.get("x-user-id")
    
    # Log the request
    log_request(
        logger,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        user_id=user_id,
    )
    
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body,
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {type(exc).__name__}: {exc}")
    
    # Don't expose internal errors in production
    if settings.DEBUG:
        import traceback
        detail = {
            "error": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(),
        }
    else:
        detail = {
            "error": "Internal Server Error",
            "message": "An unexpected error occurred. Please try again later.",
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=detail
    )


# Include routers
app.include_router(resume.router, prefix="/api", tags=["Resume"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(history.router, prefix="/api", tags=["History"])
app.include_router(evolution.router, prefix="/api", tags=["Evolution"])
app.include_router(auto_editor.router, tags=["Auto-Editor"])


@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {
        "message": "Resume Optimizer API",
        "version": "2.0.0",
        "status": "healthy",
        "features": ["ATS Analysis", "AI Recruiter Simulation", "Auto Editor", "Cover Letters", "Skill Gap Analysis"]
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": "2.0.0"
    }


@app.get("/api/status")
async def api_status():
    """Detailed API status with Groq metrics."""
    from core.throttle import get_groq_metrics
    
    groq_metrics = get_groq_metrics()
    
    return {
        "api": "operational",
        "services": {
            "groq": "operational",
            "supabase": "operational",
            "embeddings": "operational",
        },
        "rate_limiting": "active",
        "security": "active",
        "throttling": {
            "groq_api": {
                "max_concurrent": groq_metrics["max_concurrent"],
                "available_slots": groq_metrics["available_slots"],
                "utilization": f"{groq_metrics['utilization_percent']}%",
                "total_calls": groq_metrics["total_calls"],
                "throttled_calls": groq_metrics["throttled_calls"],
                "failed_calls": groq_metrics["failed_calls"],
            }
        },
    }


if __name__ == "__main__":
    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
    )
