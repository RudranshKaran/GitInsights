"""
GitInsight Backend API

This is the main entry point for the FastAPI application.
It initializes the app and registers all route handlers.

Phase 7: Includes rate limiting, request timeouts, structured error handling,
environment validation, and in-memory caching for stability and demo readiness.
"""

import sys
import asyncio
from pathlib import Path
from typing import Callable
from contextlib import asynccontextmanager

# Add backend directory to Python path when running directly
if __name__ == "__main__":
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Load environment variables from .env file
load_dotenv()

# Import hardening utilities (separated to avoid circular imports)
from app.utils.hardening import (
    limiter,
    logger,
    validate_environment,
    generate_request_id,
    analysis_cache,
    CORS_ORIGINS,
    RATE_LIMIT,
    REQUEST_TIMEOUT_SECONDS,
    MAX_REQUEST_BODY_SIZE,
    CACHE_TTL_SECONDS,
    CACHE_MAX_SIZE,
)

# ============================================================================
# Application Lifespan (Startup/Shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("GitInsight API Starting...")
    logger.info("=" * 60)
    
    # Validate environment
    warnings = validate_environment()
    if warnings:
        logger.warning(f"Configuration warnings: {warnings}")
    
    logger.info(f"Rate limit: {RATE_LIMIT}")
    logger.info(f"Request timeout: {REQUEST_TIMEOUT_SECONDS}s")
    logger.info(f"CORS origins: {CORS_ORIGINS}")
    logger.info(f"Cache TTL: {CACHE_TTL_SECONDS}s, Max size: {CACHE_MAX_SIZE}")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("GitInsight API Shutting down...")
    analysis_cache.clear()

# ============================================================================
# FastAPI Application
# ============================================================================

from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.evaluate import router as evaluate_router
from app.api.analyze import router as analyze_router

# Initialize FastAPI application
app = FastAPI(
    title="GitInsight API",
    description="AI-powered GitHub repository evaluation and analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# Attach rate limiter to app
app.state.limiter = limiter

# ============================================================================
# Middleware
# ============================================================================

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next: Callable) -> Response:
    """
    Global middleware for request handling:
    - Adds unique request ID for tracing
    - Enforces request body size limits
    - Applies request timeout
    - Logs request/response details
    """
    # Generate unique request ID
    request_id = generate_request_id()
    request.state.request_id = request_id
    
    # Check content length for body size limits
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_SIZE:
        logger.warning(f"[{request_id}] Request body too large: {content_length} bytes")
        return JSONResponse(
            status_code=413,
            content={
                "status": "error",
                "error": {
                    "type": "PAYLOAD_TOO_LARGE",
                    "message": "Request body is too large. Please try with a smaller request.",
                },
            },
        )
    
    # Log incoming request
    logger.info(f"[{request_id}] {request.method} {request.url.path}")
    
    try:
        # Apply timeout to the request handler
        response = await asyncio.wait_for(
            call_next(request),
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        # Add request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id
        
        logger.info(f"[{request_id}] Completed with status {response.status_code}")
        return response
        
    except asyncio.TimeoutError:
        logger.error(f"[{request_id}] Request timed out after {REQUEST_TIMEOUT_SECONDS}s")
        return JSONResponse(
            status_code=504,
            content={
                "status": "error",
                "error": {
                    "type": "TIMEOUT",
                    "message": "The analysis is taking too long. Please try again with a smaller repository.",
                },
            },
            headers={"X-Request-ID": request_id},
        )
    except Exception as e:
        logger.exception(f"[{request_id}] Unhandled exception: {type(e).__name__}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "type": "UNKNOWN",
                    "message": "An unexpected error occurred. Please try again.",
                },
            },
            headers={"X-Request-ID": request_id},
        )


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded with user-friendly message."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"[{request_id}] Rate limit exceeded for {get_remote_address(request)}")
    
    return JSONResponse(
        status_code=429,
        content={
            "status": "error",
            "error": {
                "type": "RATE_LIMITED",
                "message": "You've made too many requests. Please try again in a few minutes.",
            },
        },
        headers={"X-Request-ID": request_id},
    )


# ============================================================================
# Register Routers
# ============================================================================

app.include_router(health_router, tags=["Health"])
app.include_router(ingest_router, prefix="/api/v1", tags=["Ingestion"])
app.include_router(evaluate_router, prefix="/api/v1", tags=["Evaluation"])
app.include_router(analyze_router, prefix="/api/v1", tags=["Analysis"])


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        dict: API welcome message and available endpoints
    """
    return {
        "message": "Welcome to GitInsight API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
